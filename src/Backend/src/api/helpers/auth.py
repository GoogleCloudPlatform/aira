# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
from fastapi.security import http as http_sec
from jose import exceptions, jwt
from jose.constants import ALGORITHMS

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
        claims=claims,
        key=certificate,
        algorithm=ALGORITHMS.RS512,
    )


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
            algorithms=[ALGORITHMS.RS512],
            audience=settings.get("project_id"),
        )
    except (exceptions.JWKError, exceptions.JWTError) as exc:
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
