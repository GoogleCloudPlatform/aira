"""Tests for Cloud Scheduler OIDC verification hardening (validate_scheduler_token)."""

from __future__ import annotations

import typing
from unittest.mock import AsyncMock

import fastapi
import pytest
import sqlalchemy as sa
from api import errors, models
from api.adapters.sere import SereApi
from api.helpers import auth
from api.typings import SessionFactory, Settings
from fastapi.security import http as http_sec
from google.auth import exceptions as google_exceptions
from google.oauth2 import id_token
from httpx import AsyncClient

EXPECTED_SA_EMAIL = "scheduler-sync@test-project.iam.gserviceaccount.com"
EXPECTED_SA_SUB = "112233445566778899001"
EXPECTED_AUDIENCE = "test-project"
VALID_ISSUER = "https://accounts.google.com"


def _make_credentials(
    raw_token: str = "valid-google-oidc-jwt",
) -> http_sec.HTTPAuthorizationCredentials:
    return http_sec.HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=raw_token,
    )


def _valid_claims(**overrides: typing.Any) -> dict[str, typing.Any]:
    claims: dict[str, typing.Any] = {
        "iss": VALID_ISSUER,
        "aud": EXPECTED_AUDIENCE,
        "email": EXPECTED_SA_EMAIL,
        "email_verified": True,
        "sub": EXPECTED_SA_SUB,
    }
    claims.update(overrides)
    return claims


async def _ensure_sync_roles(session_factory: SessionFactory) -> None:
    """Ensure the 'user' and 'professor' roles exist for /api/v1/processor/sync."""
    async with session_factory() as session:
        for role_name in ("user", "professor"):
            existing = (
                await session.execute(
                    sa.select(models.Role).where(models.Role.name == role_name)
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    models.Role(
                        name=role_name,
                        display_name={"en-US": role_name},
                        description={"en-US": role_name},
                        scopes=[role_name],
                    )
                )
        await session.commit()


def _stub_sere_api(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Stub SereApi and org writes so /sync completes without network I/O."""
    from api.adapters.sqlalchemy.organization import OrganizationRepository

    list_org = AsyncMock(
        return_value=[
            {
                "codMec": "1",
                "descEscola": "Test School",
                "descNre": "Test Region",
                "descMun": "Test City",
            }
        ]
    )
    monkeypatch.setattr(SereApi, "list_organization", list_org)
    monkeypatch.setattr(
        SereApi, "list_group", AsyncMock(return_value=[{"codSeriacao": 0}])
    )
    monkeypatch.setattr(
        SereApi,
        "list_student_paginated",
        AsyncMock(
            return_value=[{"cgm": "1", "nome": "Student", "codTurma": "missing"}]
        ),
    )
    monkeypatch.setattr(
        SereApi,
        "list_professor",
        AsyncMock(
            return_value=[
                {
                    "nomeProfessor": "Prof",
                    "emailProfessor": "prof@example.com",
                    "cpfProfessor": "1",
                    "codTurma": "missing",
                    "codMec": "missing",
                }
            ]
        ),
    )
    monkeypatch.setattr(
        OrganizationRepository,
        "create_or_update",
        AsyncMock(return_value=None),
    )
    return list_org


# --- Unit tests for validate_scheduler_token ---


@pytest.mark.asyncio
async def test_validate_scheduler_token_rejects_attacker_google_service_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reproducer: an arbitrary Google-signed token with victim aud is rejected."""
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda **_kwargs: _valid_claims(
            email="attacker@evil-project.iam.gserviceaccount.com",
            sub="999999999999999999999",
        ),
    )
    settings = Settings(
        {
            "project_id": EXPECTED_AUDIENCE,
            "scheduler_service_account_email": EXPECTED_SA_EMAIL,
        }
    )

    with pytest.raises(errors.Forbidden):
        await auth.validate_scheduler_token(
            token=_make_credentials(),
            settings=settings,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_settings",
    [
        Settings({"project_id": EXPECTED_AUDIENCE}),
        Settings(
            {"project_id": EXPECTED_AUDIENCE, "scheduler_service_account_email": ""}
        ),
        Settings(
            {"project_id": EXPECTED_AUDIENCE, "scheduler_service_account_email": "   "}
        ),
        Settings({"scheduler_service_account_email": EXPECTED_SA_EMAIL}),
        Settings(
            {"project_id": "", "scheduler_service_account_email": EXPECTED_SA_EMAIL}
        ),
        Settings(
            {
                "project_id": "   ",
                "scheduler_audience": "  ",
                "scheduler_service_account_email": EXPECTED_SA_EMAIL,
            }
        ),
    ],
)
async def test_validate_scheduler_token_fails_closed_when_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
    bad_settings: Settings,
) -> None:
    """Fail closed before calling Google OIDC verification if config is missing."""
    called = False

    def _should_not_be_called(**_kwargs: typing.Any) -> dict[str, typing.Any]:
        nonlocal called
        called = True
        return _valid_claims()

    monkeypatch.setattr(id_token, "verify_oauth2_token", _should_not_be_called)

    with pytest.raises(errors.Forbidden):
        await auth.validate_scheduler_token(
            token=_make_credentials(),
            settings=bad_settings,
        )
    assert called is False


@pytest.mark.asyncio
@pytest.mark.parametrize("blank_token", ["", "   "])
async def test_validate_scheduler_token_rejects_blank_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
    blank_token: str,
) -> None:
    called = False

    def _should_not_be_called(**_kwargs: typing.Any) -> dict[str, typing.Any]:
        nonlocal called
        called = True
        return _valid_claims()

    monkeypatch.setattr(id_token, "verify_oauth2_token", _should_not_be_called)
    settings = Settings(
        {
            "project_id": EXPECTED_AUDIENCE,
            "scheduler_service_account_email": EXPECTED_SA_EMAIL,
        }
    )

    with pytest.raises(errors.TokenExpired):
        await auth.validate_scheduler_token(
            token=_make_credentials(blank_token),
            settings=settings,
        )
    assert called is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_claims",
    [
        _valid_claims(iss="accounts.google.com"),
        _valid_claims(iss="https://evil.example.com"),
        _valid_claims(iss="https://accounts.góogle.com"),
        _valid_claims(iss=None),
        _valid_claims(iss=""),
        _valid_claims(aud="other-project"),
        _valid_claims(aud=None),
        _valid_claims(aud=[EXPECTED_AUDIENCE]),
    ],
)
async def test_validate_scheduler_token_rejects_unpinned_issuer_or_audience(
    monkeypatch: pytest.MonkeyPatch,
    bad_claims: dict[str, typing.Any],
) -> None:
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda **_kwargs: bad_claims,
    )
    settings = Settings(
        {
            "project_id": EXPECTED_AUDIENCE,
            "scheduler_service_account_email": EXPECTED_SA_EMAIL,
        }
    )

    with pytest.raises(errors.TokenExpired):
        await auth.validate_scheduler_token(
            token=_make_credentials(),
            settings=settings,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_claims",
    [
        _valid_claims(email="attacker@gmail.com"),
        _valid_claims(email="attacker@évil.iam.gserviceaccount.com"),
        _valid_claims(email=f"evil-{EXPECTED_SA_EMAIL}"),
        _valid_claims(email=f"{EXPECTED_SA_EMAIL}.evil.com"),
        _valid_claims(email=f" {EXPECTED_SA_EMAIL} "),
        _valid_claims(email=""),
        _valid_claims(email=None),
        _valid_claims(email_verified=False),
        _valid_claims(email_verified="true"),
        _valid_claims(email_verified=1),
        _valid_claims(email_verified=None),
    ],
)
async def test_validate_scheduler_token_rejects_invalid_email_or_unverified_claim(
    monkeypatch: pytest.MonkeyPatch,
    bad_claims: dict[str, typing.Any],
) -> None:
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda **_kwargs: bad_claims,
    )
    settings = Settings(
        {
            "project_id": EXPECTED_AUDIENCE,
            "scheduler_service_account_email": EXPECTED_SA_EMAIL,
        }
    )

    with pytest.raises(errors.Forbidden):
        await auth.validate_scheduler_token(
            token=_make_credentials(),
            settings=settings,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exc",
    [
        ValueError("Token expired"),
        google_exceptions.GoogleAuthError(  # type: ignore[no-untyped-call]
            "Wrong issuer"
        ),
        google_exceptions.TransportError(  # type: ignore[no-untyped-call]
            "Cert fetch failed"
        ),
    ],
)
async def test_validate_scheduler_token_maps_verification_errors_to_401(
    monkeypatch: pytest.MonkeyPatch,
    exc: Exception,
) -> None:
    def _raise(**_kwargs: typing.Any) -> dict[str, typing.Any]:
        raise exc

    monkeypatch.setattr(id_token, "verify_oauth2_token", _raise)
    settings = Settings(
        {
            "project_id": EXPECTED_AUDIENCE,
            "scheduler_service_account_email": EXPECTED_SA_EMAIL,
        }
    )

    with pytest.raises(errors.TokenExpired):
        await auth.validate_scheduler_token(
            token=_make_credentials(),
            settings=settings,
        )


@pytest.mark.asyncio
async def test_validate_scheduler_token_enforces_optional_sub_pinning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        {
            "project_id": EXPECTED_AUDIENCE,
            "scheduler_service_account_email": EXPECTED_SA_EMAIL,
            "scheduler_service_account_sub": EXPECTED_SA_SUB,
        }
    )

    for bad_sub in ("000000000000000000000", "sub-évil", None):
        monkeypatch.setattr(
            id_token,
            "verify_oauth2_token",
            lambda _sub=bad_sub, **_kwargs: _valid_claims(sub=_sub),
        )
        with pytest.raises(errors.Forbidden):
            await auth.validate_scheduler_token(
                token=_make_credentials(),
                settings=settings,
            )

    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda **_kwargs: _valid_claims(sub=EXPECTED_SA_SUB),
    )
    await auth.validate_scheduler_token(
        token=_make_credentials(),
        settings=settings,
    )


@pytest.mark.asyncio
async def test_validate_scheduler_token_accepts_pinned_sa_and_audience_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    custom_aud = "https://backend.example.run.app/api/v1/processor/sync"
    seen_audience: list[str | None] = []

    def _verify(**kwargs: typing.Any) -> dict[str, typing.Any]:
        seen_audience.append(kwargs.get("audience"))
        return _valid_claims(
            aud=custom_aud,
            email=EXPECTED_SA_EMAIL.upper(),
        )

    monkeypatch.setattr(id_token, "verify_oauth2_token", _verify)
    settings = Settings(
        {
            "project_id": EXPECTED_AUDIENCE,
            "scheduler_audience": custom_aud,
            "scheduler_service_account_email": f"  {EXPECTED_SA_EMAIL}  ",
        }
    )

    await auth.validate_scheduler_token(
        token=_make_credentials(),
        settings=settings,
    )
    assert seen_audience == [custom_aud]


# --- HTTP integration tests for GET /api/v1/processor/sync ---


@pytest.mark.asyncio
async def test_processor_sync_rejects_unauthenticated_and_attacker_tokens(
    test_app: fastapi.FastAPI,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _ensure_sync_roles(session_factory)
    list_org = _stub_sere_api(monkeypatch)

    # 1. Missing Authorization header -> 403 from HTTPBearer
    resp_missing = await unauthenticated_client.get("/api/v1/processor/sync")
    assert resp_missing.status_code == 403
    assert resp_missing.json() == {"detail": "Not authenticated"}

    # 2. Non-Bearer scheme -> 403 from HTTPBearer
    resp_basic = await unauthenticated_client.get(
        "/api/v1/processor/sync",
        headers={"Authorization": "Basic dGVzdDp0ZXN0"},
    )
    assert resp_basic.status_code == 403

    # 3. Missing scheduler_service_account_email in settings -> fail closed (403)
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda **_kwargs: _valid_claims(),
    )
    resp_unconfigured = await unauthenticated_client.get(
        "/api/v1/processor/sync",
        headers={"Authorization": "Bearer any-token"},
    )
    assert resp_unconfigured.status_code == 403
    assert resp_unconfigured.json()["code"] == "forbidden"

    # 4. Pinned SA configured; attacker Google SA with victim aud -> 403
    app_settings = test_app.state.injector.get(Settings)
    app_settings["scheduler_service_account_email"] = EXPECTED_SA_EMAIL
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda **_kwargs: _valid_claims(
            email="attacker@evil-project.iam.gserviceaccount.com",
            sub="999999999999999999999",
        ),
    )
    resp_attacker = await unauthenticated_client.get(
        "/api/v1/processor/sync",
        headers={"Authorization": "Bearer attacker-google-id-token"},
    )
    assert resp_attacker.status_code == 403
    assert resp_attacker.json()["code"] == "forbidden"
    assert EXPECTED_SA_EMAIL not in resp_attacker.text

    # 5. GoogleAuthError from verify_oauth2_token -> 401 (never 500)
    def _raise_google_auth_error(**_kwargs: typing.Any) -> dict[str, typing.Any]:
        raise google_exceptions.GoogleAuthError(  # type: ignore[no-untyped-call]
            "Wrong issuer"
        )

    monkeypatch.setattr(id_token, "verify_oauth2_token", _raise_google_auth_error)
    resp_bad_iss = await unauthenticated_client.get(
        "/api/v1/processor/sync",
        headers={"Authorization": "Bearer wrong-issuer-token"},
    )
    assert resp_bad_iss.status_code == 401
    assert resp_bad_iss.json()["code"] == "token_expired_or_invalid"
    assert list_org.await_count == 0


@pytest.mark.asyncio
async def test_processor_sync_allows_pinned_scheduler_service_account(
    test_app: fastapi.FastAPI,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _ensure_sync_roles(session_factory)
    list_org = _stub_sere_api(monkeypatch)

    app_settings = test_app.state.injector.get(Settings)
    app_settings["scheduler_service_account_email"] = EXPECTED_SA_EMAIL

    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda **_kwargs: _valid_claims(),
    )
    resp = await unauthenticated_client.get(
        "/api/v1/processor/sync",
        headers={"Authorization": "Bearer legit-scheduler-oidc-token"},
    )
    assert resp.status_code == 200
    assert list_org.await_count == 1

    # Legacy Looker scheduler route remains removed even with a valid token.
    looker_resp = await unauthenticated_client.get(
        "/api/v1/auth/users/looker",
        headers={"Authorization": "Bearer legit-scheduler-oidc-token"},
    )
    assert looker_resp.status_code == 404
