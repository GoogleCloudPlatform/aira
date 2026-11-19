"""Shared pytest fixtures for AIRA Agent unit and security tests."""

from __future__ import annotations

import base64
import datetime
import json
import time
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from google.adk.tools.tool_context import ToolContext

from tools.db_auth import clear_public_key_cache

TEST_PROJECT_ID = "aira-test-project"
TEACHER_SESSION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN_SESSION_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
STUDENT_SESSION_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def mint_rs512_jwt(
    private_key: rsa.RSAPrivateKey,
    *,
    session_id: uuid.UUID,
    scopes: list[str],
    audience: str = TEST_PROJECT_ID,
    exp_offset: int = 3600,
    nbf_offset: int = -10,
    generation: int = 0,
    header_overrides: dict[str, Any] | None = None,
    payload_overrides: dict[str, Any] | None = None,
) -> str:
    """Mint a real RS512 JWT matching src/Backend/src/api/helpers/auth.py:create_token."""
    now = int(time.time())
    header: dict[str, Any] = {"alg": "RS512", "typ": "JWT"}
    if header_overrides:
        header.update(header_overrides)
    payload: dict[str, Any] = {
        "sub": f"{session_id}:{generation}",
        "aud": audience,
        "exp": now + exp_offset,
        "nbf": now + nbf_offset,
        "iat": now,
        "scopes": sorted(scopes),
    }
    if payload_overrides:
        payload.update(payload_overrides)

    header_b64 = b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA512())
    return f"{header_b64}.{payload_b64}.{b64url(signature)}"


@pytest.fixture(scope="session")
def rsa_keypair() -> tuple[rsa.RSAPrivateKey, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private_key, public_pem


@pytest.fixture(autouse=True)
def configure_test_auth_env(monkeypatch: pytest.MonkeyPatch, rsa_keypair: tuple[rsa.RSAPrivateKey, str]):
    _, public_pem = rsa_keypair
    clear_public_key_cache()
    monkeypatch.setenv("AUTH_PUBLIC_KEY", public_pem)
    monkeypatch.delenv("AUTH_PUBLIC_KEY_PATH", raising=False)
    monkeypatch.setenv("GCP_PROJECT_ID", TEST_PROJECT_ID)
    monkeypatch.setenv("AUTH_TOKEN_AUDIENCE", TEST_PROJECT_ID)
    monkeypatch.setenv("BQ_DATASET", "dataset_lia")
    monkeypatch.setenv("BQ_TABLE_NAME", "student_results")
    yield
    clear_public_key_cache()


def make_db_session_row(
    *,
    session_id: uuid.UUID,
    user_id: str,
    user_name: str,
    email_address: str,
    role_name: str,
    role_scopes: list[str],
    allowed_organizations: list[str],
    allowed_organization_names: list[str],
    allowed_groups: list[str],
    expires_delta_seconds: int = 3600,
) -> dict[str, Any]:
    return {
        "session_id": str(session_id),
        "session_expires_at": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(seconds=expires_delta_seconds),
        "user_id": user_id,
        "user_name": user_name,
        "email_address": email_address,
        "role_name": role_name,
        "role_scopes": json.dumps(role_scopes),
        "allowed_organizations": allowed_organizations,
        "allowed_organization_names": allowed_organization_names,
        "allowed_groups": allowed_groups,
    }


@pytest.fixture
def mock_tool_context_teacher(rsa_keypair: tuple[rsa.RSAPrivateKey, str]):
    """Returns a ToolContext with a real signed RS512 teacher JWT and live DB session."""
    private_key, _ = rsa_keypair
    token = mint_rs512_jwt(
        private_key,
        session_id=TEACHER_SESSION_ID,
        scopes=["dashboard.viewer", "exam.list", "group.list", "user.list"],
    )
    context = MagicMock(spec=ToolContext)
    context.state = {"temp:auth_token": token}
    context.get_auth_response.return_value = None

    teacher_row = make_db_session_row(
        session_id=TEACHER_SESSION_ID,
        user_id="user-teacher-1",
        user_name="Teste Professor",
        email_address="professor@radhark.tech",
        role_name="professor",
        role_scopes=["dashboard.viewer", "exam.list", "group.list", "user.list"],
        allowed_organizations=["school-uuid-123"],
        allowed_organization_names=["Escola Senai"],
        allowed_groups=["class-uuid-456"],
    )
    mock_auth_conn = AsyncMock()
    mock_auth_conn.fetchrow.return_value = teacher_row

    with patch(
        "tools.db_auth.get_db_connection",
        new=AsyncMock(return_value=(mock_auth_conn, None)),
    ):
        yield context


@pytest.fixture
def mock_tool_context_admin(rsa_keypair: tuple[rsa.RSAPrivateKey, str]):
    """Returns a ToolContext with a real signed RS512 admin JWT and live DB session."""
    private_key, _ = rsa_keypair
    token = mint_rs512_jwt(
        private_key,
        session_id=ADMIN_SESSION_ID,
        scopes=["admin"],
    )
    context = MagicMock(spec=ToolContext)
    context.state = {"temp:auth_token": token}
    context.get_auth_response.return_value = None

    admin_row = make_db_session_row(
        session_id=ADMIN_SESSION_ID,
        user_id="user-admin-1",
        user_name="Teste Admin",
        email_address="admin@radhark.tech",
        role_name="admin",
        role_scopes=["admin"],
        allowed_organizations=[],
        allowed_organization_names=[],
        allowed_groups=[],
    )
    mock_auth_conn = AsyncMock()
    mock_auth_conn.fetchrow.return_value = admin_row

    with patch(
        "tools.db_auth.get_db_connection",
        new=AsyncMock(return_value=(mock_auth_conn, None)),
    ):
        yield context


@pytest.fixture
def mock_tool_context_unauthenticated():
    """Returns a mock ToolContext representing an unauthenticated session."""
    context = MagicMock(spec=ToolContext)
    context.state = {}
    context.get_auth_response.return_value = None
    return context
