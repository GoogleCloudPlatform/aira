"""Cryptographic authentication and live PostgreSQL authorization for AIRA Agent."""

from __future__ import annotations

import asyncio
import base64
import binascii
import dataclasses
import datetime
import hmac
import json
import logging
import math
import os
import re
import time
import uuid
from typing import Any

import asyncpg
import google.auth
import httpx
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext
from google.auth.transport import requests as google_requests
from google.oauth2 import service_account

try:
    from fastapi.openapi.models import HTTPBearer
    from google.adk.auth.auth_credential import (
        AuthCredential,
        AuthCredentialTypes,
        HttpAuth,
        HttpCredentials,
    )
    from google.adk.auth.auth_tool import AuthConfig

    AIRA_HTTP_AUTH_CONFIG: AuthConfig | None = AuthConfig(
        auth_scheme=HTTPBearer(),
        raw_auth_credential=AuthCredential(
            auth_type=AuthCredentialTypes.HTTP,
            http=HttpAuth(scheme="bearer", credentials=HttpCredentials(token="")),
        ),
        credential_key="aira_bearer_auth",
    )
except Exception:
    AIRA_HTTP_AUTH_CONFIG = None

# Load .env file from the Agent directory if present
load_dotenv()

logger = logging.getLogger(__name__)

# Only educator/manager/administrator scopes may query student reading analytics.
ALLOWED_AGENT_SCOPES: frozenset[str] = frozenset(
    {"admin", "dashboard.viewer", "exam.list"}
)

_EXPECTED_JWT_ALG = "RS512"
_MIN_RSA_KEY_BITS = 2048
_MAX_TOKEN_LENGTH = 8192
_PUBLIC_KEY_CACHE_TTL_SECONDS = 300.0
_B64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_SAFE_PROJECT_ID_RE = re.compile(r"^[a-zA-Z0-9._-]{1,128}$")
_SAFE_SECRET_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,255}$")
_SECRET_MANAGER_SCOPE = "https://www.googleapis.com/auth/cloud-platform"

_public_key_cache: dict[tuple[str, ...], tuple[rsa.RSAPublicKey, float]] = {}


class AuthenticationError(Exception):
    """Raised when caller credentials are missing, invalid, or cannot be verified."""


@dataclasses.dataclass(frozen=True)
class VerifiedTokenClaims:
    """Verified claims extracted from an AIRA RS512 access token."""

    session_id: uuid.UUID
    scopes: frozenset[str]
    exp: float


def clear_public_key_cache() -> None:
    """Clear the in-memory RSA public key cache (for key rotation or tests)."""
    _public_key_cache.clear()


def _has_control_chars(value: str) -> bool:
    return any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)


def _decode_base64url(segment: str) -> bytes:
    if not segment or not _B64URL_RE.fullmatch(segment):
        raise AuthenticationError("Invalid base64url segment")
    padded = segment + "=" * (-len(segment) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii"))
    except (binascii.Error, ValueError) as exc:
        raise AuthenticationError("Malformed base64url encoding") from exc


def _parse_numeric_claim(value: Any, claim_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AuthenticationError(f"Invalid {claim_name} claim")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise AuthenticationError(f"Non-finite {claim_name} claim")
    return numeric


def _load_rsa_public_key(pem_data: str) -> rsa.RSAPublicKey:
    if not pem_data or not isinstance(pem_data, str):
        raise AuthenticationError("Empty RSA public key")
    normalized = pem_data.replace("\\n", "\n").strip()
    try:
        key = serialization.load_pem_public_key(normalized.encode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise AuthenticationError("Invalid PEM public key") from exc
    if not isinstance(key, rsa.RSAPublicKey):
        raise AuthenticationError("Public key must be an RSA key")
    if key.key_size < _MIN_RSA_KEY_BITS:
        raise AuthenticationError("RSA public key size below minimum threshold")
    return key


def _resolve_credentials_path() -> str | None:
    creds_path = (
        os.getenv("GCP_CREDENTIALS_PATH")
        or os.getenv("_GCP_SM_CREDENTIALS")
        or os.getenv("_GCP_STORAGE_CREDENTIALS")
    )
    if not creds_path:
        return None
    if os.path.isabs(creds_path):
        return creds_path if os.path.exists(creds_path) else None
    for candidate in (
        creds_path,
        os.path.join("../Backend", creds_path),
        os.path.join("../../src/Backend", creds_path),
        os.path.abspath(creds_path),
    ):
        if os.path.exists(candidate):
            return candidate
    return None


def _get_gcp_access_token() -> str:
    creds_path = _resolve_credentials_path()
    if creds_path:
        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=[_SECRET_MANAGER_SCOPE]
        )
    else:
        credentials, _ = google.auth.default(scopes=[_SECRET_MANAGER_SCOPE])
    credentials.refresh(google_requests.Request())
    token = getattr(credentials, "token", None)
    if not isinstance(token, str) or not token:
        raise AuthenticationError("Failed to obtain GCP access token")
    return token


async def _fetch_public_key_from_secret_manager(
    project_id: str, secret_id: str
) -> rsa.RSAPublicKey:
    if not _SAFE_PROJECT_ID_RE.fullmatch(project_id) or not _SAFE_SECRET_ID_RE.fullmatch(
        secret_id
    ):
        raise AuthenticationError("Invalid Secret Manager project or secret identifier")

    url = (
        f"https://secretmanager.googleapis.com/v1/projects/{project_id}"
        f"/secrets/{secret_id}/versions/latest:access"
    )
    try:
        access_token = await asyncio.to_thread(_get_gcp_access_token)
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
    except AuthenticationError:
        raise
    except Exception as exc:
        raise AuthenticationError("Unable to retrieve auth public key") from exc

    if response.status_code != 200:
        raise AuthenticationError("Auth public key retrieval rejected")

    try:
        payload_b64 = response.json()["payload"]["data"]
        pem_text = base64.b64decode(payload_b64).decode("utf-8")
    except Exception as exc:
        raise AuthenticationError("Malformed Secret Manager public key payload") from exc

    return _load_rsa_public_key(pem_text)


async def get_auth_public_key() -> rsa.RSAPublicKey:
    """Resolve AIRA's RSA public key for RS512 token verification (fail-closed)."""
    inline_pem = (os.getenv("AUTH_PUBLIC_KEY") or "").strip()
    key_path = (os.getenv("AUTH_PUBLIC_KEY_PATH") or "").strip()
    project_id = (
        os.getenv("GCP_PROJECT_ID") or os.getenv("_PROJECT_ID") or ""
    ).strip()
    secret_id = (os.getenv("AUTH_PUBLIC_KEY_SECRET_ID") or "public-key").strip()

    cache_key = (inline_pem, key_path, project_id, secret_id)
    now = time.monotonic()
    cached = _public_key_cache.get(cache_key)
    if cached and (now - cached[1]) < _PUBLIC_KEY_CACHE_TTL_SECONDS:
        return cached[0]

    if inline_pem:
        key = _load_rsa_public_key(inline_pem)
    elif key_path:
        try:
            with open(key_path, encoding="utf-8") as handle:
                key = _load_rsa_public_key(handle.read())
        except AuthenticationError:
            raise
        except OSError as exc:
            raise AuthenticationError("Unable to read AUTH_PUBLIC_KEY_PATH") from exc
    elif project_id:
        key = await _fetch_public_key_from_secret_manager(project_id, secret_id)
    else:
        raise AuthenticationError(
            "Authentication public key is not configured; failing closed"
        )

    _public_key_cache[cache_key] = (key, now)
    return key


def _get_expected_audience(explicit_audience: str | None = None) -> str:
    audience = (
        explicit_audience
        if explicit_audience is not None
        else (
            os.getenv("AUTH_TOKEN_AUDIENCE")
            or os.getenv("GCP_PROJECT_ID")
            or os.getenv("_PROJECT_ID")
            or ""
        )
    )
    normalized = audience.strip()
    if not normalized:
        raise AuthenticationError(
            "Expected token audience is not configured; failing closed"
        )
    return normalized


def _normalize_raw_token(raw_token: Any) -> str:
    if not isinstance(raw_token, str):
        raise AuthenticationError("Missing bearer token")
    token = raw_token.strip()
    if token[:7].lower() == "bearer ":
        token = token[7:].strip()
    if (
        not token
        or len(token) > _MAX_TOKEN_LENGTH
        or _has_control_chars(token)
        or any(ch.isspace() for ch in token)
    ):
        raise AuthenticationError("Malformed bearer token")
    return token


async def verify_access_token(
    raw_token: str,
    *,
    public_key: rsa.RSAPublicKey | None = None,
    expected_audience: str | None = None,
    now: float | None = None,
) -> VerifiedTokenClaims:
    """Verify an AIRA RS512 JWT access token with strict fail-closed validation."""
    token = _normalize_raw_token(raw_token)
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthenticationError("Invalid JWT structure")

    header_b64, payload_b64, sig_b64 = parts
    try:
        header = json.loads(_decode_base64url(header_b64).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthenticationError("Invalid JWT header") from exc

    if not isinstance(header, dict):
        raise AuthenticationError("JWT header must be a JSON object")

    # Hardcode expected asymmetric algorithm; never accept 'none' or HMAC confusion.
    if header.get("alg") != _EXPECTED_JWT_ALG:
        raise AuthenticationError("Unsupported JWT algorithm")
    if "crit" in header:
        raise AuthenticationError("Unsupported critical JWT header")
    typ = header.get("typ")
    if typ is not None and (not isinstance(typ, str) or typ.upper() != "JWT"):
        raise AuthenticationError("Invalid JWT type")

    rsa_key = public_key if public_key is not None else await get_auth_public_key()
    if not isinstance(rsa_key, rsa.RSAPublicKey) or rsa_key.key_size < _MIN_RSA_KEY_BITS:
        raise AuthenticationError("Invalid verification key")

    sig_bytes = _decode_base64url(sig_b64)
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    try:
        rsa_key.verify(sig_bytes, signing_input, padding.PKCS1v15(), hashes.SHA512())
    except InvalidSignature as exc:
        raise AuthenticationError("Invalid JWT signature") from exc
    except Exception as exc:
        raise AuthenticationError("JWT signature verification failed") from exc

    try:
        payload = json.loads(_decode_base64url(payload_b64).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthenticationError("Invalid JWT payload") from exc

    if not isinstance(payload, dict):
        raise AuthenticationError("JWT payload must be a JSON object")

    expected_aud = _get_expected_audience(expected_audience)
    actual_aud = payload.get("aud")
    if not isinstance(actual_aud, str) or not hmac.compare_digest(
        actual_aud.encode("utf-8"), expected_aud.encode("utf-8")
    ):
        raise AuthenticationError("Invalid JWT audience")

    current_ts = time.time() if now is None else now
    exp = _parse_numeric_claim(payload.get("exp"), "exp")
    if current_ts >= exp:
        raise AuthenticationError("JWT has expired")

    nbf = _parse_numeric_claim(payload.get("nbf"), "nbf")
    if current_ts < nbf:
        raise AuthenticationError("JWT is not yet valid")

    if "iat" in payload:
        _parse_numeric_claim(payload.get("iat"), "iat")

    raw_scopes = payload.get("scopes")
    if (
        not isinstance(raw_scopes, list)
        or not raw_scopes
        or not all(isinstance(s, str) and s.strip() for s in raw_scopes)
    ):
        raise AuthenticationError("Invalid JWT scopes")
    scopes = frozenset(s.strip() for s in raw_scopes)
    if "refresh" in scopes or not (scopes & ALLOWED_AGENT_SCOPES):
        raise AuthenticationError("Insufficient JWT scopes")

    raw_sub = payload.get("sub")
    if not isinstance(raw_sub, str):
        raise AuthenticationError("Missing JWT subject")
    sub_parts = raw_sub.split(":")
    if len(sub_parts) != 2 or not sub_parts[1].isdigit():
        raise AuthenticationError("Malformed JWT subject")
    try:
        session_id = uuid.UUID(sub_parts[0])
    except ValueError as exc:
        raise AuthenticationError("Invalid session UUID in JWT subject") from exc

    return VerifiedTokenClaims(session_id=session_id, scopes=scopes, exp=exp)


async def get_db_connection() -> tuple[Any, Any]:
    """Establish and return an asyncpg connection (and optional Cloud SQL connector)."""
    db_uri = os.getenv("DATABASE_URI") or os.getenv("_DATABASE_URI")
    if not db_uri:
        raise ValueError("DATABASE_URI environment variable is not set")

    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
    if instance_connection_name:
        from google.cloud.sql.connector import Connector
        from sqlalchemy.engine import make_url

        url = make_url(db_uri)
        loop = asyncio.get_running_loop()
        connector = Connector(loop=loop)
        conn = await connector.connect_async(
            instance_connection_name,
            "asyncpg",
            user=url.username,
            password=url.password,
            db=url.database,
        )
        return conn, connector

    direct_uri = db_uri.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(direct_uri)
    return conn, None


def _parse_role_scopes(raw_scopes: Any) -> frozenset[str]:
    parsed = raw_scopes
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except json.JSONDecodeError:
            return frozenset()
    if not isinstance(parsed, list):
        return frozenset()
    return frozenset(
        item.strip() for item in parsed if isinstance(item, str) and item.strip()
    )


async def get_verified_user_context(session_id: uuid.UUID) -> dict[str, Any] | None:
    """Resolve live user identity, role scopes, and tenant boundaries for an active session.

    Only sessions that exist in PostgreSQL, have not expired, and belong to a user
    whose live role grants an authorized educator/admin scope are returned.
    """
    conn = None
    connector = None
    try:
        conn, connector = await get_db_connection()
        query = """
        SELECT
            s.id::text AS session_id,
            s.expires_at AS session_expires_at,
            u.id::text AS user_id,
            u.name AS user_name,
            u.email_address,
            r.name AS role_name,
            r.scopes AS role_scopes,
            COALESCE(
                (SELECT array_agg(uo.organization_id::text) FROM users_organizations uo WHERE uo.user_id = u.id),
                ARRAY[]::text[]
            ) AS allowed_organizations,
            COALESCE(
                (SELECT array_agg(o.name) FROM users_organizations uo JOIN organizations o ON uo.organization_id = o.id WHERE uo.user_id = u.id),
                ARRAY[]::text[]
            ) AS allowed_organization_names,
            COALESCE(
                (SELECT array_agg(ug.group_id::text) FROM users_groups ug WHERE ug.user_id = u.id),
                ARRAY[]::text[]
            ) AS allowed_groups
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        JOIN roles r ON u.role_id = r.id
        WHERE s.id = $1
          AND s.expires_at > NOW();
        """
        row = await conn.fetchrow(query, session_id)
        if not row:
            return None

        expires_at = row["session_expires_at"]
        if isinstance(expires_at, datetime.datetime):
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
            if expires_at <= datetime.datetime.now(datetime.timezone.utc):
                return None

        role_name = str(row["role_name"] or "").strip()
        role_scopes = _parse_role_scopes(row["role_scopes"])
        if not (role_scopes & ALLOWED_AGENT_SCOPES):
            return None

        allowed_orgs = [
            str(org_id)
            for org_id in (row["allowed_organizations"] or [])
            if org_id is not None
        ]
        allowed_org_names = [
            str(name)
            for name in (row["allowed_organization_names"] or [])
            if name is not None
        ]
        allowed_groups = [
            str(group_id)
            for group_id in (row["allowed_groups"] or [])
            if group_id is not None
        ]

        return {
            "session_id": str(row["session_id"]),
            "user_id": str(row["user_id"]),
            "user_name": str(row["user_name"]),
            "email_address": str(row["email_address"]),
            "role_name": role_name,
            "role_scopes": sorted(role_scopes),
            "is_admin": role_name == "admin" and "admin" in role_scopes,
            "allowed_organizations": allowed_orgs,
            "allowed_organization_names": allowed_org_names,
            "allowed_groups": allowed_groups,
        }
    finally:
        if conn is not None:
            await conn.close()
        if connector is not None:
            await connector.close_async()


def extract_bearer_token(tool_context: ToolContext | None) -> str | None:
    """Extract an out-of-band AIRA Bearer token from trusted ADK invocation context.

    Never reads or trusts unverified identity claims such as ``user_email``,
    ``role_name``, ``allowed_organizations``, ``allowed_groups``, or ``user_id``.
    """
    if tool_context is None:
        return None

    state = getattr(tool_context, "state", None)
    state_get = getattr(state, "get", None)
    if callable(state_get):
        # Prefer ADK invocation-scoped transient state ('temp:') so tokens are not persisted.
        for key in ("temp:auth_token", "auth_token"):
            candidate = state_get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate

    get_auth_response = getattr(tool_context, "get_auth_response", None)
    if callable(get_auth_response) and AIRA_HTTP_AUTH_CONFIG is not None:
        try:
            credential = get_auth_response(AIRA_HTTP_AUTH_CONFIG)
        except Exception:
            credential = None
        http_auth = getattr(credential, "http", None)
        http_creds = getattr(http_auth, "credentials", None)
        token = getattr(http_creds, "token", None)
        if isinstance(token, str) and token.strip():
            return token

    return None


async def authenticate_tool_context(
    tool_context: ToolContext | None,
) -> dict[str, Any] | None:
    """Verify caller JWT and load live, least-privilege session context from PostgreSQL."""
    raw_token = extract_bearer_token(tool_context)
    if not raw_token:
        return None

    try:
        claims = await verify_access_token(raw_token)
    except AuthenticationError as exc:
        logger.warning("Rejected agent request: %s", exc)
        return None

    try:
        user_context = await get_verified_user_context(claims.session_id)
    except Exception:
        logger.warning("Rejected agent request: session verification lookup failed")
        return None

    if not user_context:
        logger.warning("Rejected agent request: session inactive or role unauthorized")
        return None

    # Enforce intersection of token scopes and live database role scopes.
    effective_scopes = frozenset(user_context["role_scopes"]) & claims.scopes
    if not (effective_scopes & ALLOWED_AGENT_SCOPES):
        logger.warning("Rejected agent request: effective scopes unauthorized")
        return None

    user_context["role_scopes"] = sorted(effective_scopes)
    user_context["is_admin"] = bool(
        user_context["is_admin"] and "admin" in effective_scopes
    )
    return user_context
