"""
Module containing crud actions for auth
"""

import datetime
import functools
import logging
import secrets
import uuid

from passlib import context

from api import errors, models, ports
from api.helpers import auth, time_now
from api.helpers import schemas as helper_schema
from api.typings import Settings

from . import schemas

logger = logging.getLogger(__name__)

SESSION_DURATION = datetime.timedelta(days=10)
TOKEN_DURATION = datetime.timedelta(minutes=60)
REFRESH_DURATION = datetime.timedelta(days=1)


async def create_session(
    secret_manager: ports.SecretManager,
    db: ports.UnitOfWork,
    settings: Settings,
    user_id: uuid.UUID,
    user_name: str,
    scopes: list[str],
    session: models.Session | None = None,
) -> schemas.Session:
    """
    Return a new user session.
    """
    certificate = await auth.get_private_key(secret_manager)

    session_duration = SESSION_DURATION
    token_duration = TOKEN_DURATION
    refresh_duration = REFRESH_DURATION

    now = datetime.datetime.now(datetime.UTC)
    session_id = uuid.uuid4()

    if not session:
        session = models.Session(
            id=session_id,
            user_id=user_id,
            expires_at=now + session_duration,
        )
        await db.session_repository.create(session)
    else:
        if session.expires_at <= now:
            raise errors.SessionExpired()
        session_id = session.id
        token_duration = min(token_duration, session.expires_at - now)
        refresh_duration = min(refresh_duration, session.expires_at - now)

    create_token = functools.partial(
        auth.create_token,
        issued_at=now,
        certificate=certificate,
        subject=str(session_id),
        audience=settings.get("project_id"),
    )
    session_data = schemas.Session(
        id=session_id,
        access_token=create_token(scopes=scopes, duration=token_duration),
        refresh_token=create_token(scopes=["refresh"], duration=refresh_duration),
        expires_in=token_duration,
        scopes=scopes,
        user_name=user_name,
        user_id=user_id,
    )
    return session_data


async def login(
    external_login: ports.ExternalAuth,
    secret_manager: ports.SecretManager,
    settings: Settings,
    db: ports.UnitOfWork,
    hash_ctx: context.CryptContext,
    credentials: schemas.FirebaseLogin | schemas.EmailPasswordLogin,
) -> schemas.Session:
    """
    Checks if user belongs to the system.
    """
    match credentials:
        case schemas.FirebaseLogin():
            user_data = await external_login.login_from_token(credentials.token)
            user_id = user_data.get("uid")
            try:
                user = await db.user_repository.get(external_id=user_id)
            except errors.NotFound as err:
                email = user_data.get("email")
                user = await db.user_repository.get(email=email)
                if user.external_id or user.type != models.UserType.FIREBASE:
                    raise errors.InvalidCredentials() from err
                user.external_id = user_id
        case schemas.EmailPasswordLogin():
            try:
                user = await db.user_repository.get(email=credentials.email_address)
            except errors.NotFound as err:
                raise errors.InvalidCredentials() from err
            if not (
                user.type == models.UserType.PASSWORD
                and user.check_password(credentials.password, hash_ctx)
            ):
                raise errors.InvalidCredentials()
    user.last_login = time_now()
    return await create_session(
        secret_manager=secret_manager,
        db=db,
        settings=settings,
        user_id=user.id,
        user_name=user.name,
        scopes=user.role.scopes,
    )


async def refresh(
    secret_manager: ports.SecretManager,
    settings: Settings,
    db: ports.UnitOfWork,
    token_data: helper_schema.TokenData,
) -> schemas.Session | None:
    """
    Function that gets the current session and refreshes it.
    """
    session_id = token_data.sub.split(":")[0]
    user_session = await db.session_repository.get(uuid.UUID(session_id))
    user_session.generation += 1
    return await create_session(
        secret_manager=secret_manager,
        db=db,
        settings=settings,
        user_id=user_session.user_id,
        user_name=user_session.user.name,
        scopes=user_session.user.role.scopes,
        session=user_session,
    )


async def forgot_password(email: str, uow: ports.UnitOfWork) -> str:
    """
    Sends a forgot password email
    """
    user = await uow.user_repository.get(email=email)
    user.reset_token = secrets.token_urlsafe(100)[:100]
    return user.reset_token


async def reset_password(
    token: str, password: str, uow: ports.UnitOfWork, hash_ctx: context.CryptContext
) -> bool:
    """
    Sends a forgot password email
    """
    try:
        user = await uow.user_repository.get(reset_token=token)
    except errors.NotFound as err:
        raise errors.InvalidResetUrl() from err
    user.reset_token = None
    user.set_password(password, hash_ctx)
    return True
