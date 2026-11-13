"""Characterization and regression tests for user signup and check_email endpoints."""

import uuid

import pytest
import sqlalchemy as sa
from api import models
from api.typings import SessionFactory
from httpx import AsyncClient


async def _ensure_signup_seed_data(session_factory: SessionFactory) -> None:
    """Ensure default role, organization, and group required by legacy /signup exist."""
    async with session_factory() as session:
        series = (
            await session.execute(
                sa.select(models.Series).where(models.Series.name == "3º Ano")
            )
        ).scalar_one_or_none()
        if series is None:
            series = models.Series(name="3º Ano", code="3EM")
            session.add(series)
            await session.flush()

        shift = (
            await session.execute(
                sa.select(models.WorkShift).where(models.WorkShift.code == "morning")
            )
        ).scalar_one_or_none()
        if shift is None:
            shift = models.WorkShift(name="Manhã", code="morning")
            session.add(shift)
            await session.flush()

        org = (
            await session.execute(
                sa.select(models.Organization).where(
                    models.Organization.name == "Escola Senai"
                )
            )
        ).scalar_one_or_none()
        if org is None:
            org = models.Organization(
                name="Escola Senai",
                city="DF",
                state="DF",
                customer_id=None,
                region="DF",
            )
            session.add(org)
            await session.flush()

        group = (
            await session.execute(
                sa.select(models.Group).where(models.Group.name == "Senai 3EM")
            )
        ).scalar_one_or_none()
        if group is None:
            group = models.Group(
                name="Senai 3EM",
                customer_id=None,
                organization_id=org.id,
                series_id=series.id,
                shift_id=shift.id,
            )
            session.add(group)
            await session.flush()

        role = (
            await session.execute(
                sa.select(models.Role).where(models.Role.name == "user")
            )
        ).scalar_one_or_none()
        if role is None:
            role = models.Role(
                name="user",
                display_name={"en-US": "Student"},
                description={"en-US": "Student"},
                scopes=["user"],
            )
            session.add(role)

        await session.commit()


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
async def test_characterize_signup_endpoint_current_behavior(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
) -> None:
    await _ensure_signup_seed_data(session_factory)
    target_email = f"signup-{uuid.uuid4()}@example.com"

    create_resp = await unauthenticated_client.post(
        "/api/v1/users/signup",
        json={
            "name": "Self Signup User",
            "email_address": target_email,
            "password": "Password123!",
            "type": "password",
        },
    )
    assert create_resp.status_code == 200
    payload = create_resp.json()
    assert payload["email_address"] == target_email
    assert payload["role"]["display_name"] == {"en-US": "Student"}
    assert [org["name"] for org in payload["organizations"]] == ["Escola Senai"]
    assert [grp["name"] for grp in payload["groups"]] == ["Senai 3EM"]

    duplicate_resp = await unauthenticated_client.post(
        "/api/v1/users/signup",
        json={
            "name": "Duplicate Signup User",
            "email_address": target_email,
            "password": "Password123!",
            "type": "password",
        },
    )
    assert duplicate_resp.status_code == 409
    assert duplicate_resp.json()["code"] == "user_already_exists"

    invalid_resp = await unauthenticated_client.post(
        "/api/v1/users/signup",
        json={
            "name": "Invalid Email User",
            "email_address": "not-an-email",
            "password": "Password123!",
            "type": "password",
        },
    )
    assert invalid_resp.status_code == 400
    assert invalid_resp.json()["code"] == "invalid_email"


@pytest.mark.asyncio
async def test_characterize_check_email_endpoint_current_behavior(
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

    unknown_resp = await unauthenticated_client.get(
        f"/api/v1/users/check_email/{unknown_email}"
    )
    assert unknown_resp.status_code == 200

    existing_resp = await unauthenticated_client.get(
        f"/api/v1/users/check_email/{existing_email}"
    )
    assert existing_resp.status_code == 409
    assert existing_resp.json()["code"] == "user_already_exists"


@pytest.mark.asyncio
async def test_characterize_openapi_currently_exposes_signup_routes(
    unauthenticated_client: AsyncClient,
) -> None:
    resp = await unauthenticated_client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert "/api/v1/users/signup" in spec["paths"]
    assert "/api/v1/users/check_email/{user_email}" in spec["paths"]
    assert "SignupUserCreate" in spec["components"]["schemas"]


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
