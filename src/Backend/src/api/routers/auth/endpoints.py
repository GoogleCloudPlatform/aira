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
Module containing all endpoints related to auth services
"""
from __future__ import annotations

import logging

import fastapi
import fastapi_injector
from passlib import context

from api import dependencies, ports
from api.helpers import auth
from api.helpers import schemas as helper_schema
from api.helpers import session_manager as sess_mg
from api.typings import Settings

from . import crud, schemas

router = fastapi.APIRouter()

logger = logging.getLogger(__name__)


@router.post("/token")
async def login(
    external_login: ports.ExternalAuth = fastapi_injector.Injected(ports.ExternalAuth),
    secret_manager: ports.SecretManager = fastapi_injector.Injected(
        ports.SecretManager
    ),
    settings: Settings = fastapi_injector.Injected(Settings),
    hash_ctx: context.CryptContext = fastapi_injector.Injected(context.CryptContext),
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.FirebaseLogin | schemas.EmailPasswordLogin = fastapi.Body(...),
) -> schemas.Session:
    """
    Login.

    Handles requests related to users logging in.

    :param external_login: external auth implementation.
    :param secret_manager: secret manager implementation.
    :param uow_builder: session builder implementation.
    :param settings: settings implementation.
    :param body: parsed HTTP request body.
    """
    async with uow_builder() as db:
        resp = await crud.login(
            external_login, secret_manager, settings, db, hash_ctx, body
        )
        await db.commit()
    return resp


@router.post(
    "/refresh", dependencies=[fastapi.Security(auth.get_token, scopes=["refresh"])]
)
async def refresh_token(
    secret_manager: ports.SecretManager = fastapi_injector.Injected(
        ports.SecretManager
    ),
    settings: Settings = fastapi_injector.Injected(Settings),
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    token_data: helper_schema.TokenData = fastapi.Security(
        auth.get_token, scopes=["refresh"]
    ),
) -> schemas.Session | None:
    """
    Refresh token.

    Handles the refresh of an expired (or not) token.

    :param secret_manager: secret manager implementation.
    :param settings: settings implementation.
    :param uow_builder: uow_builder implementation.
    :param token_data: token parsed.
    """
    async with uow_builder() as db:
        response = await crud.refresh(
            secret_manager=secret_manager,
            settings=settings,
            db=db,
            token_data=token_data,
        )
        await db.commit()
    return response


@router.get("/dashboard", dependencies=[fastapi.Security(auth.get_token)])
async def dashboard_signed_url(
    request: fastapi.Request,
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    dashboard: ports.Dashboard = fastapi_injector.Injected(ports.Dashboard),
) -> dict[str, str]:
    """
    Creates a signed url to access the dashboard.
    """
    session = await session_manager.get_current_session()
    response = await dashboard.get_signed_url(
        user=session.user, query=request.query_params
    )
    return {"url": response}
