"""Characterization and regression tests for Looker endpoints and SSO signing."""

import base64
import hashlib
import hmac
import json
import typing
import urllib.parse
import uuid

import fastapi
import pytest
from api import models
from api.adapters.google import looker
from api.helpers import auth
from api.routers.auth import schemas as auth_schemas
from api.typings import SessionFactory
from httpx import AsyncClient
from passlib import context

if typing.TYPE_CHECKING:
    from tests.conftest import MockMessagePublisher


async def _create_viewer_role(session_factory: SessionFactory) -> models.Role:
    """Insert an isolated dashboard.viewer role row for auth/dashboard tests."""
    role = models.Role(
        name=f"viewer-{uuid.uuid4()}",
        display_name={"en-US": "Viewer"},
        description={"en-US": "Dashboard Viewer"},
        scopes=["dashboard.viewer"],
    )
    async with session_factory() as session:
        session.add(role)
        await session.commit()
    return role


@pytest.mark.asyncio
async def test_characterize_looker_delete_handle_endpoint_unauthenticated(
    unauthenticated_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOOKERSDK_BASE_URL", "https://looker.example.com")
    deleted_ids: list[str] = []

    async def fake_delete_looker_user(
        self: looker.LookerDashboard, user_id: str
    ) -> str:
        deleted_ids.append(user_id)
        return ""

    monkeypatch.setattr(
        looker.LookerDashboard, "delete_looker_user", fake_delete_looker_user
    )

    encoded = base64.b64encode(b'{"user_id": "1"}').decode("utf-8")
    valid_resp = await unauthenticated_client.post(
        "/api/v1/auth/user/looker/_handle",
        json={
            "message": {"data": encoded, "messageId": "1"},
            "subscription": "projects/test/subscriptions/sub",
        },
    )
    assert valid_resp.status_code == 200
    assert deleted_ids == ["1"]

    minimal_resp = await unauthenticated_client.post(
        "/api/v1/auth/user/looker/_handle",
        json={"message": {"data": encoded}},
    )
    assert minimal_resp.status_code == 422


@pytest.mark.asyncio
async def test_characterize_looker_list_users_scheduler_endpoint(
    unauthenticated_client: AsyncClient,
    test_app: fastapi.FastAPI,
    mock_publisher: "MockMessagePublisher",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unauth_resp = await unauthenticated_client.get("/api/v1/auth/users/looker")
    assert unauth_resp.status_code == 403
    assert unauth_resp.json() == {"detail": "Not authenticated"}

    monkeypatch.setenv("LOOKERSDK_BASE_URL", "https://looker.example.com")

    class _StubLookerUser:
        id = "42"

    async def fake_get_all_looker_users(
        self: looker.LookerDashboard,
    ) -> list[typing.Any]:
        return [_StubLookerUser()]

    monkeypatch.setattr(
        looker.LookerDashboard, "get_all_looker_users", fake_get_all_looker_users
    )

    test_app.dependency_overrides[auth.validate_scheduler_token] = lambda: None
    try:
        sched_resp = await unauthenticated_client.get("/api/v1/auth/users/looker")
    finally:
        test_app.dependency_overrides.pop(auth.validate_scheduler_token, None)

    assert sched_resp.status_code == 200
    assert mock_publisher.published == [
        (auth_schemas.DeleteLookerUserMessage(user_id="42"), None)
    ]


@pytest.mark.asyncio
async def test_characterize_openapi_currently_exposes_looker_routes_and_pubsub_schemas(
    unauthenticated_client: AsyncClient,
) -> None:
    resp = await unauthenticated_client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    paths = spec["paths"]
    assert "/api/v1/auth/user/looker/_handle" in paths
    assert "/api/v1/auth/users/looker" in paths
    for retained_path in (
        "/api/v1/auth/token",
        "/api/v1/auth/refresh",
        "/api/v1/auth/dashboard",
        "/api/v1/auth/forgot",
        "/api/v1/auth/reset",
    ):
        assert retained_path in paths

    schemas = spec.get("components", {}).get("schemas", {})
    assert "PubsubRequest" in schemas
    assert "PubsubMessage" in schemas
    assert "PubsubDeleteUserData" not in schemas
    assert "DeleteLookerUserMessage" not in schemas
    for retained_schema in (
        "FirebaseLogin",
        "EmailPasswordLogin",
        "Session",
        "ForgotPassword",
        "ResetPassword",
    ):
        assert retained_schema in schemas


@pytest.mark.asyncio
async def test_dashboard_endpoint_rejects_unauthenticated_and_forged_tokens(
    unauthenticated_client: AsyncClient,
) -> None:
    missing_auth_resp = await unauthenticated_client.get(
        "/api/v1/auth/dashboard?src=/embed/dashboards/1"
    )
    assert missing_auth_resp.status_code == 403
    assert missing_auth_resp.json() == {"detail": "Not authenticated"}

    forged_jwt_resp = await unauthenticated_client.get(
        "/api/v1/auth/dashboard?src=/embed/dashboards/1",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert forged_jwt_resp.status_code == 401
    assert forged_jwt_resp.json()["code"] == "token_expired_or_invalid"


@pytest.mark.asyncio
async def test_dashboard_returns_valid_hmac_signed_url_for_authenticated_session(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Characterization workarounds for pre-existing looker.py:71 & looker.py:109 bugs
    # (removed via TDD Red->Green in Slice 3).
    monkeypatch.setenv("LOOKERSDK_BASE_URL", "https://looker.example.com")
    monkeypatch.setattr(models.User, "county", None, raising=False)

    role = await _create_viewer_role(session_factory)
    email = f"viewer-{uuid.uuid4()}@example.com"
    password = "Password123!"
    hash_ctx = context.CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        role_id=role.id,
        name="Maria Silva",
        email_address=email,
        state="SP",
        region="Sul",
    )
    user.set_password(password, hash_ctx)

    async with session_factory() as session:
        session.add(user)
        await session.commit()

    login_resp = await unauthenticated_client.post(
        "/api/v1/auth/token",
        json={"email_address": email, "password": password},
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    dashboard_resp = await unauthenticated_client.get(
        "/api/v1/auth/dashboard?src=/embed/dashboards/1",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert dashboard_resp.status_code == 200
    signed_url = dashboard_resp.json()["url"]

    parsed = urllib.parse.urlsplit(signed_url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "looker.example.com"
    assert parsed.path == "/login/embed/%2Fembed%2Fdashboards%2F1"

    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    params = dict(pairs)
    assert len(pairs) == len(params)
    assert params["session_length"] == "3000"
    assert params["external_user_id"] == f'"{user.id}"'
    assert params["first_name"] == '"Maria"'
    assert params["last_name"] == '"Silva"'
    assert params["force_logout_login"] == "true"
    assert json.loads(params["user_attributes"]) == {
        "group_ids": "[]",
        "organization_ids": "[]",
        "state": "SP",
        "region": "Sul",
        "county": None,
    }

    string_to_sign = "\n".join(
        [
            "looker.example.com",
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
            bytearray("test-looker-secret", "UTF-8"),
            string_to_sign.encode("UTF-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")
    assert params["signature"] == expected_sig
