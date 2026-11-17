"""
Module containing things auth related.
"""

import asyncio
import collections.abc
import datetime
import hmac
import logging
import typing
import uuid

import aiocache
import fastapi
import fastapi.security
import fastapi_injector
import jwt
from fastapi.security import http as http_sec
from google.auth import exceptions as google_exceptions
from google.auth.transport import requests
from google.oauth2 import id_token

from api import errors, ports
from api.typings import Settings

from .schemas import TokenData

logger = logging.getLogger(__name__)

_ALLOWED_SCHEDULER_ISSUER = "https://accounts.google.com"


def _secure_equals(
    actual: typing.Any, expected: str, *, case_insensitive: bool = False
) -> bool:
    """Constant-time string comparison safe for arbitrary Unicode inputs."""
    if not isinstance(actual, str):
        return False
    lhs = actual.lower() if case_insensitive else actual
    rhs = expected.lower() if case_insensitive else expected
    return hmac.compare_digest(lhs.encode("utf-8"), rhs.encode("utf-8"))


@aiocache.cached(  # type: ignore[misc]
    ttl=None,
    namespace="public-key",
)
async def get_public_key(
    secrets: ports.SecretManager,
) -> ports.Secrets | None:
    """
    Returns the public key cached
    """
    return await secrets.read("public-key")


@aiocache.cached(  # type: ignore[misc]
    ttl=None,
    namespace="private-key",
)
async def get_private_key(
    secrets: ports.SecretManager,
) -> ports.Secrets | None:
    """
    Returns the private key cached
    """
    return await secrets.read("private-key")


auth_scheme = http_sec.HTTPBearer()


def create_token(
    issued_at: datetime.datetime,
    certificate: str,
    subject: str,
    audience: str,
    scopes: set[str],
    duration: datetime.timedelta,
    generation: int = 0,
) -> str:
    """
    Generates the token used by the app.
    """
    claims = {
        "sub": f"{subject}:{generation}",
        "aud": audience,
        "exp": issued_at + duration,
        "nbf": issued_at,
        "iat": issued_at,
        "scopes": sorted(scopes),
    }
    return jwt.encode(
        payload=claims,
        key=certificate,
        algorithm="RS512",
    )


async def validate_scheduler_token(
    token: http_sec.HTTPAuthorizationCredentials = fastapi.Depends(auth_scheme),
    settings: Settings = fastapi_injector.Injected(Settings),
) -> None:
    """
    Validate a Cloud Scheduler OIDC ID token.

    Fails closed if expected service account email or audience is unconfigured,
    verifies Google signature/expiration/audience, and pins issuer, audience,
    verified email, and (when configured) subject (`sub`).
    """
    raw_expected_email = settings.get("scheduler_service_account_email")
    raw_expected_audience = settings.get("scheduler_audience") or settings.get(
        "project_id"
    )
    raw_expected_sub = settings.get("scheduler_service_account_sub")

    expected_email = (
        raw_expected_email.strip().lower()
        if isinstance(raw_expected_email, str)
        else ""
    )
    expected_audience = (
        raw_expected_audience.strip()
        if isinstance(raw_expected_audience, str)
        else ""
    )
    expected_sub = (
        raw_expected_sub.strip() if isinstance(raw_expected_sub, str) else ""
    )

    if not expected_email or not expected_audience:
        logger.error(
            "Cloud Scheduler OIDC auth misconfigured: missing expected "
            "scheduler_service_account_email or audience."
        )
        raise errors.Forbidden()

    if not token.credentials or not token.credentials.strip():
        raise errors.TokenExpired()

    request = requests.Request()  # type: ignore[no-untyped-call]
    try:
        claims = await asyncio.to_thread(
            id_token.verify_oauth2_token,
            id_token=token.credentials,
            request=request,
            audience=expected_audience,
        )
    except (ValueError, google_exceptions.GoogleAuthError) as exc:
        logger.warning("Rejected Cloud Scheduler OIDC token during verification.")
        raise errors.TokenExpired() from exc

    if not isinstance(claims, collections.abc.Mapping):
        raise errors.TokenExpired()

    if not _secure_equals(
        claims.get("iss"), _ALLOWED_SCHEDULER_ISSUER
    ) or not _secure_equals(claims.get("aud"), expected_audience):
        logger.warning(
            "Rejected Cloud Scheduler OIDC token: invalid issuer or audience."
        )
        raise errors.TokenExpired()

    if claims.get("email_verified") is not True or not _secure_equals(
        claims.get("email"), expected_email, case_insensitive=True
    ):
        logger.warning(
            "Rejected Cloud Scheduler OIDC token: unauthorized caller identity."
        )
        raise errors.Forbidden()

    if expected_sub and not _secure_equals(claims.get("sub"), expected_sub):
        logger.warning(
            "Rejected Cloud Scheduler OIDC token: caller subject mismatch."
        )
        raise errors.Forbidden()


async def get_token(
    scopes: fastapi.security.SecurityScopes,
    token: http_sec.HTTPAuthorizationCredentials = fastapi.Depends(auth_scheme),
    get_session_query: ports.GetSession = fastapi_injector.Injected(ports.GetSession),
    settings: Settings = fastapi_injector.Injected(Settings),
    secrets: ports.SecretManager = fastapi_injector.Injected(ports.SecretManager),
) -> TokenData:
    """
    Get token data based on the token received.
    """
    invalid_creds = fastapi.HTTPException(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
        detail="You don't have enough permission to do it.",
    )
    public_key = await get_public_key(secrets)
    creds = token.credentials
    try:
        decoded_token = jwt.decode(
            creds,
            key=public_key,
            algorithms=["RS512"],
            audience=settings.get("project_id"),
        )
    except jwt.PyJWTError as exc:
        raise errors.TokenExpired() from exc
    token_data = TokenData.parse_obj(decoded_token)
    if scopes.scopes and not any(
        True for scope in scopes.scopes if scope in token_data.scopes
    ):
        raise invalid_creds
    session_id = token_data.sub.split(":")[0]
    if not await get_session_query(uuid.UUID(session_id)):
        raise invalid_creds
    return token_data
