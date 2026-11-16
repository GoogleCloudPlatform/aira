"""Regression tests for Looker user-deletion removal and retained SSO URL signing."""

import base64
import hashlib
import hmac
import importlib.util
import json
import typing
import urllib.parse
import uuid

import pytest
from api import models, ports
from api.adapters.google import looker
from api.routers import schemas as router_schemas
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
async def test_looker_delete_handle_endpoint_removed(
    unauthenticated_client: AsyncClient,
) -> None:
    encoded = base64.b64encode(b'{"user_id": "1"}').decode("utf-8")

    valid_resp = await unauthenticated_client.post(
        "/api/v1/auth/user/looker/_handle",
        json={
            "message": {"data": encoded, "messageId": "1"},
            "subscription": "projects/test/subscriptions/sub",
        },
    )
    assert valid_resp.status_code == 404
    assert valid_resp.json() == {"detail": "Not Found"}

    minimal_resp = await unauthenticated_client.post(
        "/api/v1/auth/user/looker/_handle",
        json={"message": {"data": encoded}},
    )
    assert minimal_resp.status_code == 404
    assert minimal_resp.json() == {"detail": "Not Found"}

    for method in ("GET", "DELETE"):
        resp = await unauthenticated_client.request(
            method, "/api/v1/auth/user/looker/_handle"
        )
        assert resp.status_code == 404
        assert resp.json() == {"detail": "Not Found"}


@pytest.mark.asyncio
async def test_looker_list_users_scheduler_endpoint_removed(
    unauthenticated_client: AsyncClient,
    mock_publisher: "MockMessagePublisher",
) -> None:
    unauth_resp = await unauthenticated_client.get("/api/v1/auth/users/looker")
    assert unauth_resp.status_code == 404
    assert unauth_resp.json() == {"detail": "Not Found"}

    sched_resp = await unauthenticated_client.get(
        "/api/v1/auth/users/looker",
        headers={"Authorization": "Bearer fake-scheduler-oidc-token"},
    )
    assert sched_resp.status_code == 404
    assert sched_resp.json() == {"detail": "Not Found"}

    post_resp = await unauthenticated_client.post("/api/v1/auth/users/looker")
    assert post_resp.status_code == 404
    assert post_resp.json() == {"detail": "Not Found"}

    assert mock_publisher.published == []


@pytest.mark.asyncio
async def test_openapi_excludes_removed_looker_routes_and_schemas(
    unauthenticated_client: AsyncClient,
) -> None:
    resp = await unauthenticated_client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    paths = spec["paths"]
    assert "/api/v1/auth/user/looker/_handle" not in paths
    assert "/api/v1/auth/users/looker" not in paths
    for retained_path in (
        "/api/v1/auth/token",
        "/api/v1/auth/refresh",
        "/api/v1/auth/dashboard",
        "/api/v1/auth/forgot",
        "/api/v1/auth/reset",
    ):
        assert retained_path in paths

    schemas = spec.get("components", {}).get("schemas", {})
    for absent_schema in (
        "PubsubDeleteUserData",
        "DeleteLookerUserMessage",
        "PubsubRequest",
        "PubsubMessage",
    ):
        assert absent_schema not in schemas
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
    for env_key in (
        "LOOKERSDK_BASE_URL",
        "LOOKERSDK_CLIENT_ID",
        "LOOKERSDK_CLIENT_SECRET",
    ):
        monkeypatch.delenv(env_key, raising=False)

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


def test_dead_looker_delete_symbols_and_sdk_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for env_key in (
        "LOOKERSDK_BASE_URL",
        "LOOKERSDK_CLIENT_ID",
        "LOOKERSDK_CLIENT_SECRET",
    ):
        monkeypatch.delenv(env_key, raising=False)

    assert not hasattr(auth_schemas, "DeleteLookerUserMessage")
    assert not hasattr(auth_schemas, "PubsubDeleteUserData")
    assert hasattr(router_schemas, "PubsubRequest")
    assert hasattr(router_schemas, "PubsubMessage")

    assert not hasattr(ports.Dashboard, "delete_looker_user")
    assert not hasattr(ports.Dashboard, "get_all_looker_users")
    assert not hasattr(looker.LookerDashboard, "delete_looker_user")
    assert not hasattr(looker.LookerDashboard, "get_all_looker_users")

    dashboard = looker.LookerDashboard(
        looker_host="looker.example.com", looker_secret="secret"
    )
    assert not hasattr(dashboard, "_looker")
    assert importlib.util.find_spec("looker_sdk") is None
