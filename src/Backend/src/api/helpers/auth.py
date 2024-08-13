"""
Module containing things auth related.
"""

import datetime
import logging
import uuid

import aiocache
import fastapi
import fastapi.security
import fastapi_injector
import jwt
from fastapi.security import http as http_sec
from google.auth.transport import requests
from google.oauth2 import id_token

from api import errors, ports
from api.typings import Settings

from .schemas import TokenData

logger = logging.getLogger(__name__)


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
    Validate the cloud scheduler token.
    """
    request = requests.Request()
    try:
        id_token.verify_oauth2_token(
            id_token=token.credentials,
            request=request,
            audience=settings.get("project_id"),
        )
    except ValueError as exc:
        raise errors.TokenExpired() from exc


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
