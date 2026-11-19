"""Comprehensive regression guard suite for Agent cryptographic auth & tenant isolation."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from google.adk.auth.auth_credential import (
    AuthCredential,
    AuthCredentialTypes,
    HttpAuth,
    HttpCredentials,
)
from google.adk.sessions.state import State
from google.adk.tools.tool_context import ToolContext

import agent
import tools as tools_pkg
from tests.conftest import (
    ADMIN_SESSION_ID,
    STUDENT_SESSION_ID,
    TEACHER_SESSION_ID,
    TEST_PROJECT_ID,
    b64url,
    make_db_session_row,
    mint_rs512_jwt,
)
from tools import db_auth
from tools.bq_query import query_reading_proficiency
from tools.pedagogical_recommendations import query_pedagogical_recommendations


def _make_context(state: dict | State | None = None, credential: AuthCredential | None = None) -> MagicMock:
    ctx = MagicMock(spec=ToolContext)
    ctx.state = {} if state is None else state
    ctx.get_auth_response.return_value = credential
    return ctx


# ---------------------------------------------------------------------------
# 1. Removal of unverified email authentication surface
# ---------------------------------------------------------------------------


def test_unverified_email_login_tool_and_helpers_removed():
    """Agent must not expose unverified email-only login tools or email lookup functions."""
    assert not hasattr(agent, "login_manager")
    assert not hasattr(db_auth, "get_user_context")
    assert not hasattr(tools_pkg, "get_user_context")

    tool_names = [
        getattr(t, "name", getattr(getattr(t, "func", None), "__name__", ""))
        for t in agent.root_agent.tools
    ]
    assert "login_manager" not in tool_names
    assert set(tool_names) == {
        "query_reading_proficiency",
        "query_pedagogical_recommendations",
    }

    instruction_lower = agent.root_agent.instruction.lower()
    assert "login_manager" not in instruction_lower
    assert "ask the user to provide their school manager email" not in instruction_lower


# ---------------------------------------------------------------------------
# 2. Unverified state claims / forged tokens must fail closed across all tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("tools.bq_query.get_bq_client")
@patch("tools.db_auth.get_db_connection")
async def test_spoofed_admin_email_in_state_cannot_query_bq(mock_db, mock_bq_client):
    """Unverified email/role claims in session state must never grant BigQuery access."""
    ctx = _make_context(
        {
            "user_email": "admin@school.edu",
            "user_name": "Admin",
            "role_name": "admin",
            "allowed_organizations": [],
            "allowed_groups": [],
        }
    )
    result = await query_reading_proficiency(tool_context=ctx)
    assert result["success"] is False
    assert "Access Denied" in result["error"]
    mock_bq_client.assert_not_called()
    mock_db.assert_not_called()


@pytest.mark.asyncio
@patch("tools.pedagogical_recommendations.get_bq_client")
@patch("tools.db_auth.get_db_connection")
async def test_spoofed_admin_email_in_state_cannot_query_recommendations(mock_db, mock_bq_client):
    """Unverified email/role claims in session state must never grant recommendations access."""
    ctx = _make_context(
        {
            "user_email": "admin@school.edu",
            "role_name": "admin",
            "allowed_organizations": [],
            "allowed_groups": [],
        }
    )
    result = await query_pedagogical_recommendations(
        pedagogical_approach="Consciência fonêmica",
        tool_context=ctx,
    )
    assert result["success"] is False
    assert "Access Denied" in result["error"]
    mock_bq_client.assert_not_called()
    mock_db.assert_not_called()


@pytest.mark.asyncio
@patch("tools.bq_query.get_bq_client")
async def test_plain_email_passed_as_auth_token_rejected(mock_bq_client):
    """Passing a raw email string as temp:auth_token or auth_token must be rejected."""
    for key in ("temp:auth_token", "auth_token"):
        ctx = _make_context({key: "admin@school.edu"})
        result = await query_reading_proficiency(tool_context=ctx)
        assert result["success"] is False
        assert "Access Denied" in result["error"]
    mock_bq_client.assert_not_called()


# ---------------------------------------------------------------------------
# 3. Cryptographic JWT validation guards (alg confusion, tampering, claims)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rejects_alg_none_unsigned_token():
    now = int(time.time())
    header = b64url(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    payload = b64url(
        json.dumps(
            {
                "sub": f"{ADMIN_SESSION_ID}:0",
                "aud": TEST_PROJECT_ID,
                "exp": now + 3600,
                "nbf": now - 10,
                "scopes": ["admin"],
            }
        ).encode()
    )
    forged = f"{header}.{payload}."
    with pytest.raises(db_auth.AuthenticationError):
        await db_auth.verify_access_token(forged)


@pytest.mark.asyncio
async def test_rejects_hs256_algorithm_confusion_with_public_key(rsa_keypair):
    _, public_pem = rsa_keypair
    now = int(time.time())
    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64url(
        json.dumps(
            {
                "sub": f"{ADMIN_SESSION_ID}:0",
                "aud": TEST_PROJECT_ID,
                "exp": now + 3600,
                "nbf": now - 10,
                "scopes": ["admin"],
            }
        ).encode()
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    sig = hmac.new(public_pem.encode("utf-8"), signing_input, hashlib.sha256).digest()
    forged = f"{header}.{payload}.{b64url(sig)}"
    with pytest.raises(db_auth.AuthenticationError):
        await db_auth.verify_access_token(forged)


@pytest.mark.asyncio
async def test_rejects_rs256_even_with_valid_rsa_key(rsa_keypair):
    private_key, _ = rsa_keypair
    now = int(time.time())
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    payload = b64url(
        json.dumps(
            {
                "sub": f"{ADMIN_SESSION_ID}:0",
                "aud": TEST_PROJECT_ID,
                "exp": now + 3600,
                "nbf": now - 10,
                "scopes": ["admin"],
            }
        ).encode()
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    sig = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    forged = f"{header}.{payload}.{b64url(sig)}"
    with pytest.raises(db_auth.AuthenticationError):
        await db_auth.verify_access_token(forged)


@pytest.mark.asyncio
async def test_rejects_token_signed_by_attacker_keypair():
    attacker_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    forged = mint_rs512_jwt(attacker_key, session_id=ADMIN_SESSION_ID, scopes=["admin"])
    with pytest.raises(db_auth.AuthenticationError):
        await db_auth.verify_access_token(forged)


@pytest.mark.asyncio
async def test_rejects_tampered_payload(rsa_keypair):
    private_key, _ = rsa_keypair
    valid_token = mint_rs512_jwt(
        private_key,
        session_id=TEACHER_SESSION_ID,
        scopes=["dashboard.viewer"],
    )
    header_b64, _, sig_b64 = valid_token.split(".")
    now = int(time.time())
    tampered_payload = b64url(
        json.dumps(
            {
                "sub": f"{ADMIN_SESSION_ID}:0",
                "aud": TEST_PROJECT_ID,
                "exp": now + 3600,
                "nbf": now - 10,
                "scopes": ["admin"],
            }
        ).encode()
    )
    with pytest.raises(db_auth.AuthenticationError):
        await db_auth.verify_access_token(f"{header_b64}.{tampered_payload}.{sig_b64}")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kwargs",
    [
        {"exp_offset": -5},  # expired
        {"nbf_offset": 300},  # not yet valid
        {"audience": "other-project"},  # wrong audience
        {"scopes": ["refresh"]},  # refresh token replayed as access token
        {"scopes": ["user"]},  # student scope only
        {"scopes": []},  # empty scopes
        {"payload_overrides": {"exp": True}},  # bool masquerading as int
        {"payload_overrides": {"exp": None}},  # missing exp
        {"payload_overrides": {"nbf": None}},  # missing nbf
        {"payload_overrides": {"sub": "not-a-uuid:0"}},  # invalid uuid
        {"payload_overrides": {"sub": str(ADMIN_SESSION_ID)}},  # missing generation
        {"payload_overrides": {"sub": f"{ADMIN_SESSION_ID}:abc"}},  # non-digit generation
        {"header_overrides": {"crit": ["exp"]}},  # unsupported crit header
        {"header_overrides": {"typ": "NOTJWT"}},  # invalid typ
    ],
)
async def test_rejects_invalid_jwt_claims_and_headers(rsa_keypair, kwargs):
    private_key, _ = rsa_keypair
    token = mint_rs512_jwt(
        private_key,
        session_id=kwargs.get("session_id", ADMIN_SESSION_ID),
        scopes=kwargs.get("scopes", ["admin"]),
        audience=kwargs.get("audience", TEST_PROJECT_ID),
        exp_offset=kwargs.get("exp_offset", 3600),
        nbf_offset=kwargs.get("nbf_offset", -10),
        header_overrides=kwargs.get("header_overrides"),
        payload_overrides=kwargs.get("payload_overrides"),
    )
    with pytest.raises(db_auth.AuthenticationError):
        await db_auth.verify_access_token(token)


@pytest.mark.asyncio
async def test_fails_closed_when_audience_or_public_key_unconfigured(monkeypatch, rsa_keypair):
    private_key, _ = rsa_keypair
    token = mint_rs512_jwt(private_key, session_id=ADMIN_SESSION_ID, scopes=["admin"])

    monkeypatch.delenv("AUTH_TOKEN_AUDIENCE", raising=False)
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("_PROJECT_ID", raising=False)
    with pytest.raises(db_auth.AuthenticationError):
        await db_auth.verify_access_token(token)

    monkeypatch.delenv("AUTH_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("AUTH_PUBLIC_KEY_PATH", raising=False)
    db_auth.clear_public_key_cache()
    with pytest.raises(db_auth.AuthenticationError):
        await db_auth.get_auth_public_key()


@pytest.mark.asyncio
async def test_rejects_weak_1024_bit_rsa_key(monkeypatch):
    weak_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    weak_pem = (
        weak_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    monkeypatch.setenv("AUTH_PUBLIC_KEY", weak_pem)
    db_auth.clear_public_key_cache()
    with pytest.raises(db_auth.AuthenticationError):
        await db_auth.get_auth_public_key()


# ---------------------------------------------------------------------------
# 4. Live PostgreSQL session revocation, expiration, & RBAC enforcement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("tools.bq_query.get_bq_client")
async def test_revoked_db_session_denied(mock_bq_client, rsa_keypair):
    """A cryptographically valid JWT whose DB session was revoked must be rejected."""
    private_key, _ = rsa_keypair
    token = mint_rs512_jwt(private_key, session_id=ADMIN_SESSION_ID, scopes=["admin"])
    ctx = _make_context({"temp:auth_token": token})

    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = None  # revoked / deleted session
    with patch("tools.db_auth.get_db_connection", new=AsyncMock(return_value=(mock_conn, None))):
        result = await query_reading_proficiency(tool_context=ctx)

    assert result["success"] is False
    assert "Access Denied" in result["error"]
    mock_bq_client.assert_not_called()
    mock_conn.close.assert_awaited_once()


@pytest.mark.asyncio
@patch("tools.bq_query.get_bq_client")
async def test_expired_db_session_denied(mock_bq_client, rsa_keypair):
    """A valid JWT whose DB session expires_at is in the past must be rejected."""
    private_key, _ = rsa_keypair
    token = mint_rs512_jwt(private_key, session_id=ADMIN_SESSION_ID, scopes=["admin"])
    ctx = _make_context({"temp:auth_token": token})

    expired_row = make_db_session_row(
        session_id=ADMIN_SESSION_ID,
        user_id="user-admin-1",
        user_name="Admin",
        email_address="admin@school.edu",
        role_name="admin",
        role_scopes=["admin"],
        allowed_organizations=[],
        allowed_organization_names=[],
        allowed_groups=[],
        expires_delta_seconds=-60,
    )
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = expired_row
    with patch("tools.db_auth.get_db_connection", new=AsyncMock(return_value=(mock_conn, None))):
        result = await query_reading_proficiency(tool_context=ctx)

    assert result["success"] is False
    assert "Access Denied" in result["error"]
    mock_bq_client.assert_not_called()


@pytest.mark.asyncio
@patch("tools.bq_query.get_bq_client")
async def test_student_role_denied_even_with_valid_token_and_active_session(mock_bq_client, rsa_keypair):
    """Students ('user' role) must never be able to query school/class BigQuery analytics."""
    private_key, _ = rsa_keypair
    # Even if a token carried exam.list, live DB role is 'user' (student only) -> denied!
    token = mint_rs512_jwt(private_key, session_id=STUDENT_SESSION_ID, scopes=["exam.list"])
    ctx = _make_context({"temp:auth_token": token})

    student_row = make_db_session_row(
        session_id=STUDENT_SESSION_ID,
        user_id="student-1",
        user_name="Aluno",
        email_address="aluno@school.edu",
        role_name="user",
        role_scopes=["user"],
        allowed_organizations=["school-uuid-123"],
        allowed_organization_names=["Escola Senai"],
        allowed_groups=["class-uuid-456"],
    )
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = student_row
    with patch("tools.db_auth.get_db_connection", new=AsyncMock(return_value=(mock_conn, None))):
        result = await query_reading_proficiency(tool_context=ctx)

    assert result["success"] is False
    assert "Access Denied" in result["error"]
    mock_bq_client.assert_not_called()


@pytest.mark.asyncio
@patch("tools.bq_query.get_bq_client")
async def test_demoted_admin_cannot_keep_unrestricted_access(mock_bq_client, rsa_keypair):
    """If an admin was demoted in DB to professor, effective scopes must restrict queries."""
    private_key, _ = rsa_keypair
    # Token still carries old 'admin' + 'dashboard.viewer' scopes, but DB role is now professor.
    token = mint_rs512_jwt(
        private_key,
        session_id=TEACHER_SESSION_ID,
        scopes=["admin", "dashboard.viewer"],
    )
    ctx = _make_context({"temp:auth_token": token})

    demoted_row = make_db_session_row(
        session_id=TEACHER_SESSION_ID,
        user_id="user-1",
        user_name="Demoted User",
        email_address="user@school.edu",
        role_name="professor",
        role_scopes=["dashboard.viewer"],
        allowed_organizations=["school-only-1"],
        allowed_organization_names=["Escola 1"],
        allowed_groups=["class-only-1"],
    )
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = demoted_row
    mock_bq_instance = MagicMock()
    mock_bq_client.return_value = mock_bq_instance
    mock_bq_instance.query.return_value.result.return_value = []

    with patch("tools.db_auth.get_db_connection", new=AsyncMock(return_value=(mock_conn, None))):
        result = await query_reading_proficiency(tool_context=ctx)

    assert result["success"] is True
    called_sql = mock_bq_instance.query.call_args[0][0]
    assert "school_uuid IN UNNEST(@allowed_orgs_param)" in called_sql
    assert "class_uuid IN UNNEST(@allowed_groups_param)" in called_sql


@pytest.mark.asyncio
@patch("tools.bq_query.get_bq_client")
async def test_teacher_cannot_escalate_via_tampered_state_fields(mock_bq_client, rsa_keypair):
    """Tampered state fields (role_name='admin') are ignored in favor of verified live DB context."""
    private_key, _ = rsa_keypair
    token = mint_rs512_jwt(
        private_key,
        session_id=TEACHER_SESSION_ID,
        scopes=["dashboard.viewer", "exam.list"],
    )
    ctx = _make_context(
        {
            "temp:auth_token": token,
            "user_email": "admin@school.edu",
            "role_name": "admin",
            "allowed_organizations": [],
            "allowed_groups": [],
        }
    )

    teacher_row = make_db_session_row(
        session_id=TEACHER_SESSION_ID,
        user_id="user-teacher-1",
        user_name="Teacher",
        email_address="teacher@school.edu",
        role_name="professor",
        role_scopes=["dashboard.viewer", "exam.list"],
        allowed_organizations=["school-uuid-123"],
        allowed_organization_names=["Escola Senai"],
        allowed_groups=["class-uuid-456"],
    )
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = teacher_row
    mock_bq_instance = MagicMock()
    mock_bq_client.return_value = mock_bq_instance
    mock_bq_instance.query.return_value.result.return_value = []

    with patch("tools.db_auth.get_db_connection", new=AsyncMock(return_value=(mock_conn, None))):
        result = await query_reading_proficiency(tool_context=ctx)

    assert result["success"] is True
    called_sql = mock_bq_instance.query.call_args[0][0]
    assert "school_uuid IN UNNEST(@allowed_orgs_param)" in called_sql
    assert "class_uuid IN UNNEST(@allowed_groups_param)" in called_sql


@pytest.mark.asyncio
@patch("tools.bq_query.get_bq_client")
async def test_non_admin_without_organizations_returns_empty_without_bq(mock_bq_client, rsa_keypair):
    private_key, _ = rsa_keypair
    token = mint_rs512_jwt(
        private_key,
        session_id=TEACHER_SESSION_ID,
        scopes=["dashboard.viewer"],
    )
    ctx = _make_context({"temp:auth_token": token})

    row = make_db_session_row(
        session_id=TEACHER_SESSION_ID,
        user_id="user-teacher-2",
        user_name="Unassigned Teacher",
        email_address="unassigned@school.edu",
        role_name="professor",
        role_scopes=["dashboard.viewer"],
        allowed_organizations=[],
        allowed_organization_names=[],
        allowed_groups=[],
    )
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = row
    with patch("tools.db_auth.get_db_connection", new=AsyncMock(return_value=(mock_conn, None))):
        result = await query_reading_proficiency(tool_context=ctx)

    assert result["success"] is True
    assert result["records"] == []
    mock_bq_client.assert_not_called()


# ---------------------------------------------------------------------------
# 5. Valid authenticated paths (ADK State, Bearer prefix, ADK AuthCredential)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("tools.bq_query.get_bq_client")
async def test_valid_admin_works_with_adk_state_bearer_prefix_and_auth_credential(
    mock_bq_client, rsa_keypair
):
    private_key, _ = rsa_keypair
    token = mint_rs512_jwt(private_key, session_id=ADMIN_SESSION_ID, scopes=["admin"])

    admin_row = make_db_session_row(
        session_id=ADMIN_SESSION_ID,
        user_id="user-admin-1",
        user_name="Admin",
        email_address="admin@school.edu",
        role_name="admin",
        role_scopes=["admin"],
        allowed_organizations=[],
        allowed_organization_names=[],
        allowed_groups=[],
    )
    mock_bq_instance = MagicMock()
    mock_bq_client.return_value = mock_bq_instance
    mock_bq_instance.query.return_value.result.return_value = []

    # 1) Real ADK State object with Bearer prefix
    adk_state = State({"temp:auth_token": f"Bearer {token}"}, {})
    ctx_state = _make_context(adk_state)

    # 2) ADK HTTP AuthCredential via get_auth_response
    cred = AuthCredential(
        auth_type=AuthCredentialTypes.HTTP,
        http=HttpAuth(scheme="bearer", credentials=HttpCredentials(token=token)),
    )
    ctx_cred = _make_context({}, credential=cred)

    for ctx in (ctx_state, ctx_cred):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = admin_row
        with patch("tools.db_auth.get_db_connection", new=AsyncMock(return_value=(mock_conn, None))):
            result = await query_reading_proficiency(tool_context=ctx)
        assert result["success"] is True
        called_sql = mock_bq_instance.query.call_args[0][0]
        assert "school_uuid IN UNNEST" not in called_sql


# ---------------------------------------------------------------------------
# 6. Public key loaders (file path + Secret Manager REST) & BQ config hygiene
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_key_loaded_from_file_path_and_secret_manager(monkeypatch, tmp_path, rsa_keypair):
    _, public_pem = rsa_keypair
    key_file = tmp_path / "public.pem"
    key_file.write_text(public_pem, encoding="utf-8")

    # File path mode
    monkeypatch.delenv("AUTH_PUBLIC_KEY", raising=False)
    monkeypatch.setenv("AUTH_PUBLIC_KEY_PATH", str(key_file))
    db_auth.clear_public_key_cache()
    loaded = await db_auth.get_auth_public_key()
    assert loaded.key_size == 2048

    # Secret Manager REST mode
    monkeypatch.delenv("AUTH_PUBLIC_KEY_PATH", raising=False)
    monkeypatch.setenv("GCP_PROJECT_ID", TEST_PROJECT_ID)
    monkeypatch.setenv("AUTH_PUBLIC_KEY_SECRET_ID", "public-key")
    db_auth.clear_public_key_cache()

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "payload": {"data": base64.b64encode(public_pem.encode("utf-8")).decode("ascii")}
    }
    fake_client = AsyncMock()
    fake_client.get.return_value = fake_resp
    fake_client.__aenter__.return_value = fake_client
    fake_client.__aexit__.return_value = False

    with (
        patch("tools.db_auth._get_gcp_access_token", return_value="fake-gcp-access-token"),
        patch("tools.db_auth.httpx.AsyncClient", return_value=fake_client),
    ):
        sm_key = await db_auth.get_auth_public_key()
        assert sm_key.key_size == 2048
        # Second call served from TTL cache
        sm_key_cached = await db_auth.get_auth_public_key()
        assert sm_key_cached is sm_key
        assert fake_client.get.await_count == 1

    # Invalid secret ID (SSRF / path traversal attempt) fails closed
    monkeypatch.setenv("AUTH_PUBLIC_KEY_SECRET_ID", "../evil/secret")
    db_auth.clear_public_key_cache()
    with pytest.raises(db_auth.AuthenticationError):
        await db_auth.get_auth_public_key()


@pytest.mark.asyncio
@patch("tools.bq_query.get_bq_client")
async def test_invalid_bq_identifier_fails_closed_without_leaking_internals(
    mock_bq_client, monkeypatch, mock_tool_context_admin
):
    monkeypatch.setenv("BQ_DATASET", "dataset_lia`; DROP TABLE x; --")
    result = await query_reading_proficiency(tool_context=mock_tool_context_admin)
    assert result["success"] is False
    assert "DROP TABLE" not in result["error"]
    assert "BigQuery" not in result["error"]
    mock_bq_client.assert_not_called()
