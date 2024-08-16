"""
Unit tests for `process`
"""

import datetime
import functools
import logging
import typing
import unittest.mock
import uuid

import hypothesis
import pytest
from api import errors, models, typings
from api.adapters.memory import (
    external_auth,
    secret_manager,
    session_query,
    unit_of_work,
    user,
)
from api.helpers import schemas as helper_schema
from api.routers.auth import crud, schemas
from hypothesis import strategies as st
from passlib import context

from tests.helpers import strats

logger = logging.getLogger(__name__)


def side_eff_create_token(data: dict[str, str], **kwargs: typing.Any) -> str:
    """
    Side effect to change access and refresh token.
    """
    match kwargs.get("scopes"):
        case ["refresh"]:
            return data["refresh_token"]
        case _:
            return data["access_token"]


@pytest.mark.asyncio
@hypothesis.given(
    credentials=st.builds(
        schemas.FirebaseLogin,
    ),
    expected=st.builds(schemas.Session),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
    max_examples=8,
)
async def test_login(
    credentials: schemas.FirebaseLogin,
    expected: schemas.Session,
    fake_user: models.User,
    hash_ctx: context.CryptContext,
) -> None:
    """
    tests if auth endpoint calls correctly.
    """
    create_session_mock = unittest.mock.AsyncMock()
    create_session_mock.return_value = expected

    user_repo = user.UserRepository([fake_user])
    uow_builder = unit_of_work.UnitOfWorkBuilder(user_repository=user_repo)
    setts = typings.Settings({})
    secret_mg = secret_manager.SecretManager()
    async with uow_builder() as db_session:
        with unittest.mock.patch(
            "api.routers.auth.crud.create_session", create_session_mock
        ):
            response = await crud.login(
                external_login=external_auth.ExternalAuth(),
                secret_manager=secret_mg,
                settings=setts,
                db=db_session,
                credentials=credentials,
                hash_ctx=hash_ctx,
            )
    create_session_mock.assert_called_once_with(
        secret_manager=secret_mg,
        db=db_session,
        settings=setts,
        user_id=fake_user.id,
        user_name=fake_user.name,
        scopes=fake_user.role.scopes,
    )
    assert uow_builder.call_count == 1
    assert expected == response


@pytest.mark.asyncio
@hypothesis.given(
    user_id=st.uuids(),
    user_name=strats.safe_text(),
    session_id=st.uuids(),
    scopes=st.lists(st.text(min_size=1, max_size=10)),
    access_token=st.text(min_size=1, max_size=100),
    refresh_token=st.text(min_size=1, max_size=100),
)
async def test_create_session(
    user_id: uuid.UUID,
    user_name: str,
    session_id: uuid.UUID,
    scopes: list[str],
    access_token: str,
    refresh_token: str,
) -> None:
    """
    tests that the create_session works properly
    """
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": crud.TOKEN_DURATION,
        "id": session_id,
        "user_name": user_name,
        "scopes": scopes,
        "user_id": user_id,
    }
    create_token = functools.partial(side_eff_create_token, data=data)
    secret_mg = secret_manager.SecretManager()
    setts = typings.Settings({})
    uuid_mock = unittest.mock.Mock()
    uuid_mock.return_value = session_id
    session_repo = session_query.SessionRepository([])
    uow_builder = unit_of_work.UnitOfWorkBuilder(session_repository=session_repo)
    async with uow_builder() as db_session:
        with (
            unittest.mock.patch("uuid.uuid4", uuid_mock),
            unittest.mock.patch("api.helpers.auth.create_token") as token_mock,
        ):
            token_mock.side_effect = create_token
            response = await crud.create_session(
                secret_manager=secret_mg,
                db=db_session,
                settings=setts,
                user_id=user_id,
                user_name=user_name,
                scopes=scopes,
            )
    assert response == schemas.Session(**data)
    assert await session_repo.get(session_id)


@pytest.mark.asyncio
@hypothesis.given(
    user_id=st.uuids(),
    user_name=strats.safe_text(),
    session_id=st.uuids(),
    scopes=st.lists(st.text(min_size=1, max_size=10)),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
)
async def test_should_not_refresh(
    user_id: uuid.UUID,
    user_name: str,
    session_id: uuid.UUID,
    scopes: list[str],
    fake_user: models.User,
) -> None:
    """
    tests that it should not refresh
    """

    secret_mg = secret_manager.SecretManager()
    setts = typings.Settings({})

    fake_session = models.Session(
        id=session_id,
        user_id=user_id,
        expires_at=datetime.datetime.now(tz=datetime.UTC),
        generation=0,
    )
    fake_session.user = fake_user

    uow_builder = unit_of_work.UnitOfWorkBuilder()

    async with uow_builder() as db_session:
        with pytest.raises(errors.SessionExpired):
            await crud.create_session(
                secret_manager=secret_mg,
                db=db_session,
                settings=setts,
                user_id=user_id,
                user_name=user_name,
                scopes=scopes,
                session=fake_session,
            )


@pytest.mark.asyncio
@hypothesis.given(
    user_id=st.uuids(),
    user_name=strats.safe_text(),
    session_id=st.uuids(),
    scopes=st.lists(st.text(min_size=1, max_size=10)),
    access_token=st.text(min_size=1, max_size=100),
    refresh_token=st.text(min_size=1, max_size=100),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
)
async def test_should_refresh_successfully(
    user_id: uuid.UUID,
    user_name: str,
    session_id: uuid.UUID,
    scopes: list[str],
    access_token: str,
    refresh_token: str,
    fake_user: models.User,
) -> None:
    """
    tests that it should refresh successfully
    """

    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": crud.TOKEN_DURATION,
        "id": session_id,
        "user_name": user_name,
        "scopes": scopes,
        "user_id": user_id,
    }

    secret_mg = secret_manager.SecretManager()
    setts = typings.Settings({})
    create_token = functools.partial(side_eff_create_token, data=data)

    fake_session = models.Session(
        id=session_id,
        user_id=user_id,
        expires_at=datetime.datetime.now(tz=datetime.UTC) + crud.SESSION_DURATION,
        generation=0,
    )
    fake_session.user = fake_user

    session_repo = session_query.SessionRepository([fake_session])
    uow_builder = unit_of_work.UnitOfWorkBuilder(session_repository=session_repo)

    async with uow_builder() as db_session:
        with unittest.mock.patch("api.helpers.auth.create_token") as token_mock:
            token_mock.side_effect = create_token
            response = await crud.create_session(
                secret_manager=secret_mg,
                db=db_session,
                settings=setts,
                user_id=user_id,
                user_name=user_name,
                scopes=scopes,
                session=fake_session,
            )
    assert response == schemas.Session(**data)


@hypothesis.given(
    user_id=st.uuids(),
    user_name=strats.safe_text(),
    session_id=st.uuids(),
    scopes=st.lists(st.text(min_size=1, max_size=10)),
    access_token=st.text(min_size=1, max_size=100),
    refresh_token=st.text(min_size=1, max_size=100),
    token_data=st.builds(helper_schema.TokenData),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
)
@pytest.mark.asyncio
async def test_refresh_function(
    user_id: uuid.UUID,
    user_name: str,
    session_id: uuid.UUID,
    scopes: list[str],
    access_token: str,
    refresh_token: str,
    token_data: helper_schema.TokenData,
    fake_user: models.User,
) -> None:
    """
    tests that the refresh handles data properly
    """
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": crud.TOKEN_DURATION,
        "id": session_id,
        "user_name": user_name,
        "scopes": scopes,
        "user_id": user_id,
    }

    secret_mg = secret_manager.SecretManager()
    setts = typings.Settings({})

    fake_session = models.Session(
        id=session_id,
        user_id=user_id,
        expires_at=datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(hours=1),
        generation=0,
    )
    fake_session.user = fake_user
    session_repo = session_query.SessionRepository([fake_session])
    uow_builder = unit_of_work.UnitOfWorkBuilder(session_repository=session_repo)

    token_data.sub = f"{str(session_id)}:0"

    async with uow_builder() as db_session:
        with unittest.mock.patch(
            "api.routers.auth.crud.create_session"
        ) as create_session_mock:
            create_session_mock.return_value = schemas.Session(**data)
            response = await crud.refresh(
                secret_manager=secret_mg,
                settings=setts,
                db=db_session,
                token_data=token_data,
            )

            assert (
                current_session := await session_repo.get(session_id)
            ), current_session
            assert current_session.generation == 1
            create_session_mock.assert_called_with(
                secret_manager=secret_mg,
                db=db_session,
                settings=setts,
                user_id=current_session.user_id,
                user_name=current_session.user.name,
                scopes=current_session.user.role.scopes,
                session=current_session,
            )
    assert response == schemas.Session(**data)
