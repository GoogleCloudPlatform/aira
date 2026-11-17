"""Regression tests for Looker SSO RBAC scope enforcement, embed path allow-listing,
and least-privilege embed permissions.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import urllib.parse
import uuid

import pytest
import sqlalchemy as sa
from api import errors, models
from api.adapters.google import looker
from api.typings import SessionFactory
from httpx import AsyncClient
from passlib import context
from starlette import datastructures

FORBIDDEN_PERMISSIONS = {
    "schedule_look_emails",
    "download_without_limit",
    "see_looks",
    "mobile_app_access",
    "clear_cache_refresh",
    "see_drill_overlay",
}

EXPECTED_PERMISSIONS = [
    "access_data",
    "see_lookml_dashboards",
    "see_user_dashboards",
]


async def _create_user_with_scopes(
    session_factory: SessionFactory,
    scopes: list[str],
    *,
    name: str = "Test User",
    state: str | None = "SP",
    region: str | None = "Sul",
) -> tuple[models.User, str, models.Role]:
    """Create an isolated role + password user in the test DB."""
    role = models.Role(
        name=f"role-{uuid.uuid4()}",
        display_name={"en-US": "Role"},
        description={"en-US": "Role"},
        scopes=scopes,
    )
    email = f"user-{uuid.uuid4()}@example.com"
    password = "Password123!"
    hash_ctx = context.CryptContext(schemes=["bcrypt"], deprecated="auto")

    async with session_factory() as session:
        session.add(role)
        await session.flush()

        user = models.User(
            external_id=None,
            customer_id=None,
            type=models.UserType.PASSWORD,
            role_id=role.id,
            name=name,
            email_address=email,
            state=state,
            region=region,
        )
        user.set_password(password, hash_ctx)
        session.add(user)
        await session.commit()

    return user, password, role


async def _login(
    client: AsyncClient, email: str, password: str
) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/token",
        json={"email_address": email, "password": password},
    )
    assert resp.status_code == 200
    data: dict[str, str] = resp.json()
    return data


def _verify_signed_looker_url(
    url: str,
    *,
    expected_host: str = "looker.example.com",
    expected_secret: str = "test-looker-secret",
) -> tuple[urllib.parse.SplitResult, dict[str, str]]:
    parsed = urllib.parse.urlsplit(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == expected_host

    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    params = dict(pairs)
    assert len(pairs) == len(params)

    string_to_sign = "\n".join(
        [
            expected_host,
            parsed.path,
            params["nonce"],
            params["time"],
            params["session_length"],
            params["external_user_id"],
            params["permissions"],
            params["models"],
            params["group_ids"],
            params["external_group_id"],
            params["user_attributes"],
            params["access_filters"],
        ]
    )
    expected_sig = base64.b64encode(
        hmac.new(
            bytearray(expected_secret, "UTF-8"),
            string_to_sign.encode("UTF-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")
    assert params["signature"] == expected_sig
    return parsed, params


@pytest.mark.asyncio
async def test_student_token_cannot_obtain_looker_sso_url(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
) -> None:
    """Students (scope='user') must be rejected from GET /api/v1/auth/dashboard."""
    student, password, _ = await _create_user_with_scopes(
        session_factory, scopes=["user"], name="Student User"
    )
    tokens = await _login(unauthenticated_client, student.email_address, password)

    resp = await unauthenticated_client.get(
        "/api/v1/auth/dashboard",
        params={"src": "/embed/dashboards/1"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 401
    assert "url" not in resp.json()


@pytest.mark.asyncio
async def test_refresh_token_cannot_obtain_looker_sso_url(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
) -> None:
    """Refresh tokens (scope='refresh') must be rejected from /api/v1/auth/dashboard."""
    viewer, password, _ = await _create_user_with_scopes(
        session_factory, scopes=["dashboard.viewer"], name="Viewer User"
    )
    tokens = await _login(unauthenticated_client, viewer.email_address, password)

    resp = await unauthenticated_client.get(
        "/api/v1/auth/dashboard",
        params={"src": "/embed/dashboards/1"},
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert resp.status_code == 401
    assert "url" not in resp.json()


@pytest.mark.asyncio
async def test_demoted_user_with_stale_token_rejected(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
) -> None:
    """Downgraded DB role must fail closed even with a stale viewer JWT."""
    user, password, _ = await _create_user_with_scopes(
        session_factory, scopes=["dashboard.viewer"], name="Demoted User"
    )
    tokens = await _login(unauthenticated_client, user.email_address, password)

    student_role = models.Role(
        name=f"student-{uuid.uuid4()}",
        display_name={"en-US": "Student"},
        description={"en-US": "Student"},
        scopes=["user"],
    )
    async with session_factory() as session:
        session.add(student_role)
        await session.flush()
        await session.execute(
            sa.update(models.User)
            .where(models.User.id == user.id)
            .values(role_id=student_role.id)
        )
        await session.commit()

    resp = await unauthenticated_client.get(
        "/api/v1/auth/dashboard",
        params={"src": "/embed/dashboards/1"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malicious_src",
    [
        "",
        "   ",
        "/embed/looks/1",
        "/embed/explore/aira/student_results",
        "/admin/users",
        "/browse",
        "/login",
        "/embed/dashboards/999",
        "/embed/dashboards/1/extra",
        "/embed/dashboards/1/../../admin",
        "/embed/dashboards/..%2Fadmin",
        "/embed/dashboards/1%2F..%2Fadmin",
        "/embed/dashboards/1\\..\\admin",
        "https://evil.example.com/embed/dashboards/1",
        "//evil.example.com/embed/dashboards/1",
        "/embed/dashboards/1#fragment",
        "/embed/dashboards/1\r\ninjected",
        "/embed/dashboards/1\ninjected",
        "/embed/dashboards/1?embed_domain=https://evil.example.com&sdk=2",
        "/embed/dashboards/1?embed_domain=https://app.example.com.evil.com&sdk=2",
        "/embed/dashboards/1?embed_domain=javascript:alert(1)",
        "/embed/dashboards/1?embed_domain=https://app.example.com/extra",
        "/embed/dashboards/1?sdk=2&theme=evil",
        "/embed/dashboards/1?sdk=../../etc",
        (
            "/embed/dashboards/1?embed_domain=https://app.example.com"
            "&embed_domain=https://evil.example.com"
        ),
        "/embed/dashboards/1?malformed_flag",
        "/embed/dashboards/1?",
        "/embed/dashboards/%31",
        "/embed/dashboards/1%3Ffoo%3Dbar",
        "/embed/dashboards/1?embed_domain=https://user:pass@app.example.com",
        "/embed/dashboards/1?embed_domain=https://app.example.com:8443",
    ],
)
async def test_dashboard_rejects_unallowlisted_or_malicious_src(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    malicious_src: str,
) -> None:
    """Arbitrary, non-allowlisted, or malformed src paths must be rejected."""
    viewer, password, _ = await _create_user_with_scopes(
        session_factory, scopes=["dashboard.viewer"], name="Viewer Src Test"
    )
    tokens = await _login(unauthenticated_client, viewer.email_address, password)

    resp = await unauthenticated_client.get(
        "/api/v1/auth/dashboard",
        params={"src": malicious_src},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 422, (
        f"Expected 422 for src={malicious_src!r}, "
        f"got {resp.status_code}: {resp.text}"
    )
    assert resp.json()["code"] == "invalid_field"


@pytest.mark.asyncio
async def test_dashboard_rejects_missing_and_duplicate_src(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
) -> None:
    """Missing src or duplicate src parameters (HPP) must be rejected."""
    admin, password, _ = await _create_user_with_scopes(
        session_factory, scopes=["admin"], name="Admin Src Test"
    )
    tokens = await _login(unauthenticated_client, admin.email_address, password)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    missing_resp = await unauthenticated_client.get(
        "/api/v1/auth/dashboard", headers=headers
    )
    assert missing_resp.status_code == 422
    assert missing_resp.json()["code"] == "invalid_field"

    dup_resp = await unauthenticated_client.get(
        "/api/v1/auth/dashboard?src=/embed/dashboards/1&src=/embed/looks/2",
        headers=headers,
    )
    assert dup_resp.status_code == 422
    assert dup_resp.json()["code"] == "invalid_field"


@pytest.mark.asyncio
@pytest.mark.parametrize("scopes", [["admin"], ["dashboard.viewer"]])
async def test_authorized_roles_receive_least_privilege_signed_embed_url(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    scopes: list[str],
) -> None:
    """Admin and dashboard.viewer roles get minimal-permission signed URLs."""
    user, password, _ = await _create_user_with_scopes(
        session_factory, scopes=scopes, name="Ana Costa"
    )
    tokens = await _login(unauthenticated_client, user.email_address, password)

    sdk_src = "/embed/dashboards/2?embed_domain=https%3A%2F%2Fapp.example.com&sdk=2"
    resp = await unauthenticated_client.get(
        "/api/v1/auth/dashboard",
        params={"src": sdk_src},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    parsed, params = _verify_signed_looker_url(resp.json()["url"])

    expected_canonical_src = (
        "/embed/dashboards/2?embed_domain=https%3A%2F%2Fapp.example.com&sdk=2"
    )
    assert parsed.path == "/login/embed/" + urllib.parse.quote_plus(
        expected_canonical_src
    )

    granted_permissions = json.loads(params["permissions"])
    assert granted_permissions == EXPECTED_PERMISSIONS
    assert not (set(granted_permissions) & FORBIDDEN_PERMISSIONS)


@pytest.mark.asyncio
async def test_looker_adapter_fails_closed_when_unconfigured() -> None:
    """LookerDashboard must fail closed if allow-list, host, or secret is unset."""
    dummy_user = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        role_id=uuid.uuid4(),
        name="Manager One",
        email_address="mgr@example.com",
        state="SP",
        region="Sul",
    )
    dummy_user.groups = []
    dummy_user.organizations = []

    query = datastructures.QueryParams({"src": "/embed/dashboards/1"})

    for adapter in (
        looker.LookerDashboard(
            looker_host="looker.example.com",
            looker_secret="secret",
        ),
        looker.LookerDashboard(
            looker_host="",
            looker_secret="secret",
            allowed_dashboard_ids=["1"],
        ),
        looker.LookerDashboard(
            looker_host="looker.example.com",
            looker_secret="",
            allowed_dashboard_ids=["1"],
        ),
    ):
        with pytest.raises(errors.Forbidden):
            await adapter.get_signed_url(user=dummy_user, query=query)


@pytest.mark.asyncio
async def test_looker_adapter_models_and_concurrent_isolation() -> None:
    """Configured models are signed, and singleton adapter has no shared user state."""
    adapter = looker.LookerDashboard(
        looker_host="looker.example.com",
        looker_secret="secret-key",
        allowed_dashboard_ids=["1"],
        allowed_embed_domains=["https://app.example.com/"],
        models=["aira_analytics"],
    )

    user_a = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        role_id=uuid.uuid4(),
        name="Alice One",
        email_address="alice@example.com",
        state="SP",
        region="Norte",
    )
    user_a.groups = []
    user_a.organizations = []

    user_b = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        role_id=uuid.uuid4(),
        name="Bob Two",
        email_address="bob@example.com",
        state="RJ",
        region="Sudeste",
    )
    user_b.groups = []
    user_b.organizations = []

    query = datastructures.QueryParams(
        {"src": "/embed/dashboards/1?embed_domain=https://app.example.com&sdk=2"}
    )
    url_a, url_b = await asyncio.gather(
        adapter.get_signed_url(user=user_a, query=query),
        adapter.get_signed_url(user=user_b, query=query),
    )

    assert not hasattr(adapter, "user")

    _, params_a = _verify_signed_looker_url(
        url_a, expected_host="looker.example.com", expected_secret="secret-key"
    )
    _, params_b = _verify_signed_looker_url(
        url_b, expected_host="looker.example.com", expected_secret="secret-key"
    )
    assert params_a["external_user_id"] == f'"{user_a.id}"'
    assert params_b["external_user_id"] == f'"{user_b.id}"'
    assert json.loads(params_a["models"]) == ["aira_analytics"]
    assert json.loads(params_b["models"]) == ["aira_analytics"]


@pytest.mark.asyncio
async def test_build_looker_dashboard_wires_allowlists() -> None:
    """Settings wiring ignores '*' origin, normalizes front URL, allows LookML IDs."""
    from api.dependencies import _build_looker_dashboard
    from api.typings import Settings

    adapter = _build_looker_dashboard(
        Settings(
            {
                "looker_host": "looker.example.com",
                "looker_secret": "secret-key",
                "looker_allowed_dashboard_ids": "1, aira_model::reading_overview",
                "looker_models": "aira_model",
                "front_base_url": "https://frontend.example.com/",
                "origin": "*, https://admin.example.com",
            }
        )
    )
    assert adapter.allowed_dashboard_ids == frozenset(
        {"1", "aira_model::reading_overview"}
    )
    assert adapter.allowed_embed_domains == frozenset(
        {"https://frontend.example.com", "https://admin.example.com"}
    )
    assert adapter.models == ["aira_model"]

    dummy_user = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        role_id=uuid.uuid4(),
        name="Manager Two",
        email_address="mgr2@example.com",
        state="SP",
        region="Sul",
    )
    dummy_user.groups = []
    dummy_user.organizations = []

    valid_query = datastructures.QueryParams(
        {
            "src": (
                "/embed/dashboards/aira_model::reading_overview"
                "?embed_domain=HTTPS://FRONTEND.EXAMPLE.COM&sdk=2"
            )
        }
    )
    signed_url = await adapter.get_signed_url(user=dummy_user, query=valid_query)
    parsed, params = _verify_signed_looker_url(
        signed_url, expected_host="looker.example.com", expected_secret="secret-key"
    )
    assert parsed.path == "/login/embed/" + urllib.parse.quote_plus(
        "/embed/dashboards/aira_model::reading_overview"
        "?embed_domain=https%3A%2F%2Ffrontend.example.com&sdk=2"
    )
    assert json.loads(params["models"]) == ["aira_model"]

    evil_origin_query = datastructures.QueryParams(
        {"src": "/embed/dashboards/1?embed_domain=https://evil.example.com&sdk=2"}
    )
    with pytest.raises(errors.InvalidField):
        await adapter.get_signed_url(user=dummy_user, query=evil_origin_query)

