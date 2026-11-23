"""Integration and regression tests guarding handle_import and /batch endpoints
against confused-deputy GCS SSRF, scheme/host bypasses, and path traversal.
"""

from __future__ import annotations

import datetime
import os
import tempfile
import typing
import uuid

import pytest
import sqlalchemy as sa
from api import errors, models
from api.helpers import auth, data
from api.helpers import schemas as helper_schemas
from api.typings import SessionFactory, Settings
from httpx import AsyncClient

if typing.TYPE_CHECKING:
    from tests.conftest import MockStorage


async def _get_or_create_series(
    session_factory: SessionFactory, grade: models.Grades
) -> models.Series:
    async with session_factory() as session:
        existing = (
            await session.execute(
                sa.select(models.Series).where(models.Series.name == grade.value)
            )
        ).scalar_one_or_none()
        if existing:
            return existing
        series = models.Series(
            name=grade.value,
            code=f"S{uuid.uuid4().hex[:8]}",
        )
        session.add(series)
        await session.commit()
        return series


async def _get_or_create_shift(session_factory: SessionFactory) -> models.WorkShift:
    async with session_factory() as session:
        existing = (
            await session.execute(
                sa.select(models.WorkShift).where(models.WorkShift.name == "Manhã")
            )
        ).scalar_one_or_none()
        if existing:
            return existing
        shift = models.WorkShift(name="Manhã", code="MORNING")
        session.add(shift)
        await session.commit()
        return shift


async def _create_org(
    session_factory: SessionFactory,
    *,
    label: str = "batch",
) -> models.Organization:
    suffix = uuid.uuid4().hex[:8]
    org = models.Organization(
        customer_id=f"cust-{label}-{suffix}",
        name=f"Org-{label}-{suffix}",
        region="Sul",
        city="Curitiba",
        state="PR",
    )
    async with session_factory() as session:
        session.add(org)
        await session.commit()
    return org


async def _create_user_with_scopes(
    test_app: typing.Any,
    session_factory: SessionFactory,
    scopes: list[str],
) -> tuple[models.User, str]:
    role = models.Role(
        name=f"role-{uuid.uuid4()}",
        display_name={"en-US": "Role"},
        description={"en-US": "Role"},
        scopes=scopes,
    )
    user = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        name="Batch Test User",
        email_address=f"batch-{uuid.uuid4().hex[:10]}@example.com",
        role_id=role.id,
        region=None,
        state=None,
    )
    now = datetime.datetime.now(datetime.UTC)
    session_row = models.Session(
        id=uuid.uuid4(),
        user_id=user.id,
        expires_at=now + datetime.timedelta(hours=1),
    )
    async with session_factory() as session:
        session.add(role)
        await session.flush()
        session.add(user)
        await session.flush()
        session.add(session_row)
        await session.commit()

    from api import ports

    secret_manager = test_app.state.injector.get(ports.SecretManager)
    private_key = await secret_manager.read("private-key")
    assert private_key is not None
    token = auth.create_token(
        issued_at=now,
        certificate=str(private_key),
        subject=str(session_row.id),
        audience="test-project",
        scopes=set(scopes),
        duration=datetime.timedelta(hours=1),
    )
    return user, token


def _stub_csv_download(mock_storage: MockStorage, csv_content: str) -> list[str]:
    """Patch mock_storage.download to write CSV content and track created temp paths."""
    created_paths: list[str] = []

    async def _download(uri: str, file_name: str) -> str:
        mock_storage.download_calls.append((uri, file_name))
        path = os.path.join(tempfile.gettempdir(), file_name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(csv_content)
        created_paths.append(path)
        return path

    mock_storage.download = _download  # type: ignore[method-assign]
    return created_paths


# --- 1. Cross-bucket SSRF & URL smuggling rejected across all /batch endpoints ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v1/organizations/batch",
        "/api/v1/groups/batch",
        "/api/v1/users/batch",
    ],
)
@pytest.mark.parametrize(
    "malicious_url",
    [
        # Cross-bucket HTTPS (standard and cloud console hosts)
        "https://storage.googleapis.com/victim-other-bucket/import/USER/20261122%7Cabc.csv",
        "https://storage.googleapis.com/test-bucket-evil/import/USER/20261122%7Cabc.csv",
        "https://storage.cloud.google.com/victim-other-bucket/import/USER/20261122%7Cabc.csv",
        # Cross-bucket gs://
        "gs://victim-other-bucket/import/USER/20261122|abc.csv",
        "gs://test-bucket-evil/import/USER/20261122|abc.csv",
        "gs://TEST-BUCKET/import/USER/20261122|abc.csv",
        # Arbitrary external hosts, subdomain tricks, userinfo, ports, metadata
        "https://evil.com/test-bucket/import/USER/20261122%7Cabc.csv",
        "https://evil.com/storage.googleapis.com/test-bucket/import/USER/20261122%7Cabc.csv",
        "https://storage.googleapis.com.evil.com/test-bucket/import/USER/20261122%7Cabc.csv",
        "https://storage.googleapis.com@evil.com/test-bucket/import/USER/20261122%7Cabc.csv",
        "https://user@storage.googleapis.com/test-bucket/import/USER/20261122%7Cabc.csv",
        "https://storage.googleapis.com:8443/test-bucket/import/USER/20261122%7Cabc.csv",
        "https://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
        # Disallowed schemes
        "http://storage.googleapis.com/test-bucket/import/USER/20261122%7Cabc.csv",
        "file:///etc/passwd",
        "ftp://storage.googleapis.com/test-bucket/import/USER/20261122%7Cabc.csv",
        "test-bucket/import/USER/20261122|abc.csv",
        # Path traversal, encoded traversal, double-encoding, backslashes
        "https://storage.googleapis.com/test-bucket/import/USER/../../../victim-bucket/secret.csv",
        "https://storage.googleapis.com/test-bucket/import/USER/%2e%2e/%2e%2e/secret.csv",
        "https://storage.googleapis.com/test-bucket/import/USER/%252e%252e/secret.csv",
        "https://storage.googleapis.com/test-bucket/import%2fUSER%2f20261122.csv",
        "https://storage.googleapis.com/test-bucket/import/USER/a%5cb.csv",
        "https://storage.googleapis.com/test-bucket/import/USER/a%00.csv",
        "https://storage.googleapis.com/test-bucket/import/USER/a\\b.csv",
        "gs://test-bucket//import/USER/20261122|abc.csv",
        # Query / fragment / path params / leading-dash / empty path
        "https://storage.googleapis.com/test-bucket/import/USER/a.csv?alt=media",
        "https://storage.googleapis.com/test-bucket/import/USER/a.csv#frag",
        "https://storage.googleapis.com/test-bucket/import/USER/a.csv;foo=bar",
        "https://storage.googleapis.com/test-bucket/import/USER/-flag.csv",
        "https://storage.googleapis.com/test-bucket/",
        # Same-bucket non-import paths (exports, exam audio, root files)
        "https://storage.googleapis.com/test-bucket/export/20261122-admin-users.csv",
        "https://storage.googleapis.com/test-bucket/secrets.csv",
        "https://storage.googleapis.com/test-bucket/org-id/group-id/audio.wav",
        "gs://test-bucket/export/20261122-admin-users.csv",
    ],
)
async def test_batch_endpoints_reject_ssrf_and_unsafe_urls(
    client: AsyncClient,
    mock_storage: MockStorage,
    endpoint: str,
    malicious_url: str,
) -> None:
    """Reject cross-bucket, non-GCS, non-import, and malformed /batch import URLs."""
    _stub_csv_download(mock_storage, "name,region,city,state\nExfil,S,C,PR\n")

    resp = await client.put(
        endpoint,
        json={"url": malicious_url, "key_relation": {}},
    )

    assert (
        resp.status_code == 422
    ), f"{endpoint} accepted {malicious_url!r}: {resp.status_code} {resp.text}"
    assert mock_storage.download_calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("endpoint", "wrong_type_path"),
    [
        ("/api/v1/organizations/batch", "import/USER/20261122%7Cabc.csv"),
        ("/api/v1/organizations/batch", "import/GROUP/20261122%7Cabc.csv"),
        (
            "/api/v1/organizations/batch",
            "import/ORGANIZATION/nested/20261122%7Cabc.csv",
        ),
        ("/api/v1/groups/batch", "import/USER/20261122%7Cabc.csv"),
        ("/api/v1/groups/batch", "import/ORGANIZATION/20261122%7Cabc.csv"),
        ("/api/v1/users/batch", "import/GROUP/20261122%7Cabc.csv"),
        ("/api/v1/users/batch", "import/ORGANIZATION/20261122%7Cabc.csv"),
    ],
)
async def test_batch_endpoints_reject_cross_type_import_paths(
    client: AsyncClient,
    mock_storage: MockStorage,
    endpoint: str,
    wrong_type_path: str,
) -> None:
    """Each /batch endpoint only accepts objects under its own import/<TYPE>/ prefix."""
    _stub_csv_download(mock_storage, "name\nBad\n")

    resp = await client.put(
        endpoint,
        json={
            "url": f"https://storage.googleapis.com/test-bucket/{wrong_type_path}",
            "key_relation": {},
        },
    )

    assert resp.status_code == 422
    assert mock_storage.download_calls == []


@pytest.mark.asyncio
async def test_batch_endpoint_rejects_non_csv_before_download(
    client: AsyncClient,
    mock_storage: MockStorage,
) -> None:
    """Non-CSV objects under import/ are rejected before invoking storage.download."""
    _stub_csv_download(mock_storage, "not a csv")

    resp = await client.put(
        "/api/v1/organizations/batch",
        json={
            "url": "https://storage.googleapis.com/test-bucket/import/ORGANIZATION/20261122%7Cabc.txt",
            "key_relation": {},
        },
    )

    assert resp.status_code == 400
    assert resp.json()["code"] == "not_supported"
    assert mock_storage.download_calls == []


@pytest.mark.asyncio
async def test_batch_endpoint_fails_closed_when_bucket_unconfigured(
    test_app: typing.Any,
    client: AsyncClient,
    mock_storage: MockStorage,
) -> None:
    """Missing/empty bucket_path fails closed with 403 before storage.download."""
    app_settings = test_app.state.injector.get(Settings)
    original_bucket = app_settings["bucket_path"]
    app_settings["bucket_path"] = ""
    try:
        resp = await client.put(
            "/api/v1/organizations/batch",
            json={
                "url": "https://storage.googleapis.com/test-bucket/import/ORGANIZATION/20261122%7Cabc.csv",
                "key_relation": {},
            },
        )
    finally:
        app_settings["bucket_path"] = original_bucket

    assert resp.status_code == 403
    assert mock_storage.download_calls == []


# --- 2. Authentication & RBAC preserved on all /batch endpoints ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v1/organizations/batch",
        "/api/v1/groups/batch",
        "/api/v1/users/batch",
    ],
)
async def test_batch_endpoints_require_admin_scope(
    test_app: typing.Any,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    endpoint: str,
) -> None:
    """Unauthenticated and non-admin callers cannot invoke /batch importers."""
    payload = {
        "url": "https://storage.googleapis.com/test-bucket/import/ORGANIZATION/20261122%7Cabc.csv",
        "key_relation": {},
    }

    no_auth = await unauthenticated_client.put(endpoint, json=payload)
    assert no_auth.status_code == 403

    _, user_token = await _create_user_with_scopes(
        test_app, session_factory, ["user", "exam.list"]
    )
    non_admin = await unauthenticated_client.put(
        endpoint,
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert non_admin.status_code == 401
    assert mock_storage.download_calls == []


# --- 3. Legitimate happy paths across HTTPS, storage.cloud.google.com, and gs:// ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("url_template", "expected_object"),
    [
        (
            "https://storage.googleapis.com/test-bucket/import/ORGANIZATION/20261122%7C{tag}.csv",
            "import/ORGANIZATION/20261122|{tag}.csv",
        ),
        (
            "https://storage.cloud.google.com/test-bucket/import/ORGANIZATION/20261122%7C{tag}.csv",
            "import/ORGANIZATION/20261122|{tag}.csv",
        ),
        (
            "gs://test-bucket/import/ORGANIZATION/20261122|{tag}.csv",
            "import/ORGANIZATION/20261122|{tag}.csv",
        ),
    ],
)
async def test_organizations_batch_accepts_valid_configured_bucket_urls(
    client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    url_template: str,
    expected_object: str,
) -> None:
    """Valid configured-bucket HTTPS and gs:// URLs import and clean up temp files."""
    org = await _create_org(session_factory, label="ok-org")
    tag = uuid.uuid4().hex[:10]
    updated_name = f"Updated-{tag}"
    created_paths = _stub_csv_download(
        mock_storage,
        f"ext_id,org_name,org_region\n{org.customer_id},{updated_name},Norte\n",
    )

    resp = await client.put(
        "/api/v1/organizations/batch",
        json={
            "url": url_template.format(tag=tag),
            "key_relation": {
                "ext_id": "customer_id",
                "org_name": "name",
                "org_region": "region",
            },
        },
    )

    assert resp.status_code == 201, resp.text
    assert len(mock_storage.download_calls) == 1
    downloaded_uri, downloaded_local_name = mock_storage.download_calls[0]
    assert downloaded_uri == f"gs://test-bucket/{expected_object.format(tag=tag)}"
    # Temp filename must be server-generated, never user-derived
    assert downloaded_local_name.startswith("import-")
    assert downloaded_local_name.endswith(".csv")
    assert tag not in downloaded_local_name
    # Temp file cleaned up after import
    assert len(created_paths) == 1
    assert not os.path.exists(created_paths[0])

    async with session_factory() as session:
        refreshed = (
            await session.execute(
                sa.select(models.Organization).where(models.Organization.id == org.id)
            )
        ).scalar_one()
        assert refreshed.name == updated_name
        assert refreshed.region == "Norte"


@pytest.mark.asyncio
async def test_groups_batch_accepts_valid_configured_bucket_url(
    client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
) -> None:
    """PUT /api/v1/groups/batch succeeds for a valid import/GROUP/*.csv URL."""
    org = await _create_org(session_factory, label="ok-grp")
    series = await _get_or_create_series(session_factory, models.Grades.FIRST_FUND)
    shift = await _get_or_create_shift(session_factory)
    tag = uuid.uuid4().hex[:10]
    group_name = f"BatchGroup-{tag}"
    created_paths = _stub_csv_download(
        mock_storage,
        (
            "name,organization,series_id,shift_id\n"
            f"{group_name},{org.id},{series.id},{shift.id}\n"
        ),
    )

    resp = await client.put(
        "/api/v1/groups/batch",
        json={
            "url": f"https://storage.googleapis.com/test-bucket/import/GROUP/20261122%7C{tag}.csv",
            "key_relation": {},
        },
    )

    assert resp.status_code == 201, resp.text
    assert len(mock_storage.download_calls) == 1
    assert (
        mock_storage.download_calls[0][0]
        == f"gs://test-bucket/import/GROUP/20261122|{tag}.csv"
    )
    assert not os.path.exists(created_paths[0])

    async with session_factory() as session:
        created = (
            await session.execute(
                sa.select(models.Group).where(models.Group.name == group_name)
            )
        ).scalar_one_or_none()
        assert created is not None
        assert created.organization_id == org.id


@pytest.mark.asyncio
async def test_users_batch_accepts_valid_configured_bucket_url(
    client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
) -> None:
    """PUT /api/v1/users/batch succeeds for a valid import/USER/*.csv URL."""
    role = models.Role(
        name=f"batch-admin-{uuid.uuid4().hex[:8]}",
        display_name={"en-US": "Admin"},
        description={"en-US": "Admin"},
        scopes=["admin"],
    )
    async with session_factory() as session:
        session.add(role)
        await session.commit()

    tag = uuid.uuid4().hex[:10]
    email = f"imported-{tag}@example.com"
    created_paths = _stub_csv_download(
        mock_storage,
        (
            "customer_id,name,email_address,role_id,state,region,groups,organizations\n"
            f"u-{tag},Imported User,{email},{role.id},PR,Sul,,\n"
        ),
    )

    resp = await client.put(
        "/api/v1/users/batch",
        json={
            "url": (
                "https://storage.googleapis.com/test-bucket/"
                f"import/USER/20261122%7C{tag}.csv"
            ),
            "key_relation": {},
        },
    )

    assert resp.status_code == 201, resp.text
    assert len(mock_storage.download_calls) == 1
    assert (
        mock_storage.download_calls[0][0]
        == f"gs://test-bucket/import/USER/20261122|{tag}.csv"
    )
    assert not os.path.exists(created_paths[0])

    async with session_factory() as session:
        created = (
            await session.execute(
                sa.select(models.User).where(models.User.email_address == email)
            )
        ).scalar_one_or_none()
        assert created is not None
        assert created.role_id == role.id


# --- 4. Direct unit guards on handle_import & validate_import_gcs_url ---


@pytest.mark.asyncio
async def test_handle_import_cleans_up_temp_file_on_parse_error(
    mock_storage: MockStorage,
) -> None:
    """Temporary downloaded CSV is removed even when CSV parsing raises."""
    created_paths = _stub_csv_download(
        mock_storage,
        "id,name\nnot-a-valid-uuid,Broken\n",
    )

    with pytest.raises(ValueError):
        await data.handle_import(
            "gs://test-bucket/import/USER/20261122|broken.csv",
            {},
            mock_storage,
            "test-bucket",
            expected_import_type=helper_schemas.ImportType.USER,
        )

    assert len(created_paths) == 1
    assert not os.path.exists(created_paths[0])


def test_validate_import_gcs_url_rejects_control_chars_and_invalid_bucket() -> None:
    """Direct validation rejects control characters and invalid configured bucket."""
    with pytest.raises(errors.InvalidField):
        data.validate_import_gcs_url(
            "https://storage.googleapis.com/test-bucket/import/USER/a\r\n.csv",
            "test-bucket",
        )
    with pytest.raises(errors.Forbidden):
        data.validate_import_gcs_url(
            "https://storage.googleapis.com/test-bucket/import/USER/a.csv",
            "../invalid-bucket",
        )
