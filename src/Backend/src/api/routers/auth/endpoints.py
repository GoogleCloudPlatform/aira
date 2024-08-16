"""
Module containing all endpoints related to auth services
"""

from __future__ import annotations

import base64
import logging

import fastapi
import fastapi_injector
from passlib import context

from api import dependencies, errors, ports, typings
from api.helpers import auth
from api.helpers import schemas as helper_schema
from api.helpers import session_manager as sess_mg
from api.routers.schemas import PubsubRequest
from api.typings import Settings

from . import crud, schemas

router = fastapi.APIRouter(tags=["auth"])

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


@router.post("/forgot")
async def forgot_password(
    body: schemas.ForgotPassword = fastapi.Body(...),
    notification: ports.Notification = fastapi_injector.Injected(ports.Notification),
    setts: typings.Settings = fastapi_injector.Injected(typings.Settings),
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
) -> fastapi.Response:
    """
    Sends a forgot password email
    """
    async with uow_builder() as uow:
        try:
            token = await crud.forgot_password(body.email, uow)
            url = f"{setts['front_base_url']}/reset?token={token}"
            await notification.send(
                body.email,
                setts["forgot_pw_template"],
                reset_url=url,
            )
            await uow.commit()
        except errors.NotFound:
            pass
    return fastapi.Response(status_code=fastapi.status.HTTP_200_OK)


@router.post("/reset")
async def reset_password(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.ResetPassword = fastapi.Body(...),
    hash_ctx: context.CryptContext = fastapi_injector.Injected(context.CryptContext),
) -> fastapi.Response:
    """
    Sends a forgot password email
    """
    async with uow_builder() as uow:
        await crud.reset_password(body.token, body.password, uow, hash_ctx)
        await uow.commit()
    return fastapi.Response(status_code=fastapi.status.HTTP_200_OK)


@router.get(
    "/users/looker",
    dependencies=[fastapi.Security(auth.validate_scheduler_token)],
)
async def set_delete_users_pubsub(
    provide_looker: ports.Dashboard = fastapi_injector.Injected(ports.Dashboard),
    publisher: ports.MessagePublisher = fastapi_injector.Injected(
        ports.MessagePublisher
    ),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
) -> fastapi.Response:
    """
    Set pubsub to delete each user
    """
    users = await provide_looker.get_all_looker_users()

    for user in users:
        await publisher.publish(
            schemas.DeleteLookerUserMessage(user_id=user.id),
            topic=settings.get("pubsub_delete_user_topic"),
        )
    return fastapi.Response(status_code=fastapi.status.HTTP_200_OK)


@router.post("/user/looker/_handle")
async def handle_delete_users_pubsub(
    provide_looker: ports.Dashboard = fastapi_injector.Injected(ports.Dashboard),
    body: PubsubRequest = fastapi.Body(...),
) -> fastapi.Response:
    """
    Handle delete looker user
    """
    data = schemas.PubsubDeleteUserData.parse_raw(
        base64.b64decode(body.message.data.decode("utf-8"))
    )
    await provide_looker.delete_looker_user(data.user_id)
    return fastapi.Response(status_code=fastapi.status.HTTP_200_OK)
