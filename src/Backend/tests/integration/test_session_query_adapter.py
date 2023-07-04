"""
Module for testing the session_model repository.
"""
import contextlib
import datetime
import uuid

import pytest

from api import errors, models
from api.adapters.sqlalchemy import session_query
from api.helpers import time_now
from tests.helpers import database


def _create_session_model(user_id: uuid.UUID, qty: int = 1) -> list[models.Session]:
    return [
        models.Session(
            id=uuid.uuid4(),
            user_id=user_id,
            expires_at=time_now() + datetime.timedelta(hours=1),
        )
        for _ in range(qty)
    ]


@pytest.mark.asyncio
async def test_get_session_model_query() -> None:
    """
    Test of adapter to get an session_model from query.
    """
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(database.clear_between_tests())
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        role_model = await stack.enter_async_context(database.role())
        user_model = await stack.enter_async_context(database.user(role_model))
        session_model = await stack.enter_async_context(
            database.session_model(user_model)
        )
        get_session_model = session_query.GetSession(session_factory)
        response = await get_session_model(session_model.id)
        assert response == session_model


@pytest.mark.asyncio
async def test_get_session_model_repo_query() -> None:
    """
    Test of adapter to get session_query.
    """
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(database.clear_between_tests())
        uow = await stack.enter_async_context(database.uow_ctx())
        role = await stack.enter_async_context(database.role())
        user = await stack.enter_async_context(database.user(role))
        fake_session_model = await stack.enter_async_context(
            database.session_model(user)
        )
        session_model = await uow.session_repository.get(fake_session_model.id)

        assert session_model == fake_session_model, session_model


@pytest.mark.asyncio
async def test_create_session_model() -> None:
    """
    Test of adapter to create session_query.
    """
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(database.clear_between_tests())
        role_model = await stack.enter_async_context(database.role())
        user_model = await stack.enter_async_context(database.user(role_model))
        session_model_model = _create_session_model(user_model.id)[0]
        uow = await stack.enter_async_context(database.uow_ctx())
        expected = await uow.session_repository.create(session_model_model)
        session_model_model = await uow.session_repository.get(expected.id)
        assert expected == session_model_model


@pytest.mark.asyncio
async def test_should_raise_already_exists() -> None:
    """
    Test of adapter to create session_query.
    """
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(database.clear_between_tests())
        uow = await stack.enter_async_context(database.uow_ctx())
        role_model = await stack.enter_async_context(database.role())
        user_model = await stack.enter_async_context(database.user(role_model))
        session_model = await stack.enter_async_context(
            database.session_model(user_model)
        )
        new_session_model_same_data = _create_session_model(user_model.id, qty=1)[0]
        new_session_model_same_data.id = session_model.id
        with pytest.raises(errors.AlreadyExists):
            await uow.session_repository.create(new_session_model_same_data)
