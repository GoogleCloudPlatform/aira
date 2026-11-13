"""Regression tests verifying removal of public signup and check_email endpoints."""

import uuid

import pytest
import sqlalchemy as sa
from api import errors, models
from api.helpers import util
from api.routers.users import schemas as user_schemas
from api.typings import SessionFactory
from httpx import AsyncClient


async def _create_admin_role(session_factory: SessionFactory) -> models.Role:
    """Insert an isolated admin role row for user provisioning tests."""
    role = models.Role(
        name=f"admin-{uuid.uuid4()}",
        display_name={"en-US": "Admin"},
        description={"en-US": "Admin"},
        scopes=["admin"],
    )
    async with session_factory() as session:
        session.add(role)
        await session.commit()
    return role


@pytest.mark.asyncio
async def test_signup_endpoint_removed(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
) -> None:
    target_email = f"attacker-{uuid.uuid4()}@example.com"

    response = await unauthenticated_client.post(
        "/api/v1/users/signup",
        json={
            "name": "Attacker",
            "email_address": target_email,
            "password": "Password123!",
            "type": "password",
        },
    )
    assert response.status_code == 405
    assert response.headers["allow"] == "GET"
    assert response.json() == {"detail": "Method Not Allowed"}

    async with session_factory() as session:
        persisted = (
            await session.execute(
                sa.select(models.User).where(models.User.email_address == target_email)
            )
        ).scalar_one_or_none()
    assert persisted is None


@pytest.mark.asyncio
async def test_check_email_endpoint_removed_no_enumeration(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
) -> None:
    role = await _create_admin_role(session_factory)
    existing_email = f"existing-{uuid.uuid4()}@example.com"
    unknown_email = f"unknown-{uuid.uuid4()}@example.com"

    async with session_factory() as session:
        session.add(
            models.User(
                external_id=None,
                customer_id=None,
                type=models.UserType.PASSWORD,
                role_id=role.id,
                name="Existing User",
                email_address=existing_email,
                state=None,
                region=None,
            )
        )
        await session.commit()

    existing_resp = await unauthenticated_client.get(
        f"/api/v1/users/check_email/{existing_email}"
    )
    unknown_resp = await unauthenticated_client.get(
        f"/api/v1/users/check_email/{unknown_email}"
    )
    assert existing_resp.status_code == 404
    assert unknown_resp.status_code == 404
    assert existing_resp.json() == {"detail": "Not Found"}
    assert unknown_resp.json() == {"detail": "Not Found"}

    exams_collision_resp = await unauthenticated_client.get(
        "/api/v1/users/check_email/exams"
    )
    assert exams_collision_resp.status_code == 403
    assert exams_collision_resp.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_openapi_excludes_removed_signup_routes_and_schema(
    unauthenticated_client: AsyncClient,
) -> None:
    resp = await unauthenticated_client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert "/api/v1/users/signup" not in spec["paths"]
    assert "/api/v1/users/check_email/{user_email}" not in spec["paths"]
    assert "SignupUserCreate" not in spec.get("components", {}).get("schemas", {})


@pytest.mark.asyncio
async def test_admin_create_user_rejects_unauthenticated(
    unauthenticated_client: AsyncClient,
) -> None:
    body = {
        "role_id": str(uuid.uuid4()),
        "groups": [],
        "organizations": [],
        "name": "Unauthenticated Caller",
        "email_address": f"unauth-{uuid.uuid4()}@example.com",
        "type": "password",
        "password": "Password123!",
    }

    missing_auth_resp = await unauthenticated_client.post("/api/v1/users", json=body)
    assert missing_auth_resp.status_code == 403
    assert missing_auth_resp.json() == {"detail": "Not authenticated"}

    forged_jwt_resp = await unauthenticated_client.post(
        "/api/v1/users",
        json=body,
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert forged_jwt_resp.status_code == 401
    assert forged_jwt_resp.json()["code"] == "token_expired_or_invalid"


@pytest.mark.asyncio
async def test_admin_create_user_preserves_validation_and_uniqueness(
    client: AsyncClient,
    session_factory: SessionFactory,
) -> None:
    role = await _create_admin_role(session_factory)
    valid_email = f"admin-created-{uuid.uuid4()}@example.com"

    create_resp = await client.post(
        "/api/v1/users",
        json={
            "role_id": str(role.id),
            "groups": [],
            "organizations": [],
            "name": "Provisioned Admin",
            "email_address": valid_email,
            "type": "password",
            "password": "Password123!",
        },
    )
    assert create_resp.status_code == 200
    created_payload = create_resp.json()
    assert created_payload["email_address"] == valid_email
    assert created_payload["role_id"] == str(role.id)

    invalid_email_resp = await client.post(
        "/api/v1/users",
        json={
            "role_id": str(role.id),
            "groups": [],
            "organizations": [],
            "name": "Invalid Email Admin",
            "email_address": "not-a-valid-email",
            "type": "password",
            "password": "Password123!",
        },
    )
    assert invalid_email_resp.status_code == 422
    detail = invalid_email_resp.json()["detail"]
    assert any(err["type"] == "value_error.email" for err in detail)

    duplicate_resp = await client.post(
        "/api/v1/users",
        json={
            "role_id": str(role.id),
            "groups": [],
            "organizations": [],
            "name": "Duplicate Admin",
            "email_address": valid_email,
            "type": "password",
            "password": "Password123!",
        },
    )
    assert duplicate_resp.status_code == 409
    assert duplicate_resp.json()["code"] == "already_exists"


def test_dead_signup_symbols_removed_from_backend() -> None:
    assert not hasattr(user_schemas, "SignupUserCreate")
    assert not hasattr(errors, "UserAlreadyExists")
    assert not hasattr(errors, "InvalidEmail")
    assert not hasattr(util, "validate_email")
