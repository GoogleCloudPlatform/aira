"""
Module for testing the user repository.
"""

import contextlib

import hypothesis
import pytest
from api import errors, models
from api.adapters.sqlalchemy import user
from api.routers.users import schemas
from hypothesis import strategies as st

from tests.helpers import database, strats


def _create_user_from_schema(
    schema_list: list[schemas.UserCreate],
    role_model: models.Role,
) -> list[models.User]:
    return [
        models.User(
            name=schema.name,
            type=schema.type,
            email_address=schema.email_address,
            external_id=schema.external_id,
            customer_id=schema.customer_id,
            groups=[],
            organizations=[],
            role_id=role_model.id,
            state=None,
            region=None,
            county=None,
        )
        for schema in schema_list
    ]


@pytest.mark.asyncio
@pytest.mark.database
async def test_get_user_query() -> None:
    """
    Test of adapter to get an user from query.
    """
    async with contextlib.AsyncExitStack() as stack:
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )

        role_model = await stack.enter_async_context(database.role())
        user_model = await stack.enter_async_context(
            database.user(role_model=role_model)
        )
        get_user = user.GetUser(session_factory)
        response = await get_user(user_model.id)
        assert response == user_model


@pytest.mark.asyncio
@pytest.mark.database
async def test_get_user_repo_query() -> None:
    """
    Test of adapter to get user.
    """
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        role_model = await stack.enter_async_context(database.role())
        fake_user = await stack.enter_async_context(database.user(role_model))
        user_model = await uow.user_repository.get(fake_user.id)

        assert user_model == fake_user, user_model


@pytest.mark.asyncio
@pytest.mark.database
@hypothesis.given(
    user_schema=st.builds(
        schemas.UserCreate,
        name=strats.safe_text(),
        external_id=strats.safe_text(),
        password=strats.safe_text(),
        email_address=st.emails(),
    )
)
async def test_create_user(user_schema: schemas.UserCreate) -> None:
    """
    Test of adapter to create user.
    """
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        role_model = models.Role(
            name="teste", display_name={}, description={}, scopes=["test"]
        )
        user_model = _create_user_from_schema([user_schema], role_model=role_model)[0]
        user_model.role = role_model
        expected = await uow.user_repository.create(user_model)
        user_model = await uow.user_repository.get(expected.id)
        assert expected == user_model


@pytest.mark.asyncio
@pytest.mark.database
async def test_should_raise_already_exists() -> None:
    """
    Test of adapter to create user.
    """
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        role_model = await stack.enter_async_context(database.role())
        user_model = await stack.enter_async_context(database.user(role_model))
        new_user_same_data = _create_user_from_schema(
            [schemas.UserCreate.from_orm(user_model)], role_model=role_model
        )[0]
        with pytest.raises(errors.AlreadyExists):
            await uow.user_repository.create(new_user_same_data)
