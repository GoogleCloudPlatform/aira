"""
Module for testing the role repository.
"""

import contextlib
import typing

import hypothesis
import pytest
from api import errors, models
from api.adapters.sqlalchemy import role

from tests.helpers import database, strats


def _create_role_from_dict(
    schema_list: list[dict[str, typing.Any]],
) -> list[models.Role]:
    return [
        models.Role(
            name=schema["name"],
            display_name={},
            description={},
            scopes=schema["scopes"],
        )
        for schema in schema_list
    ]


@pytest.mark.asyncio
@pytest.mark.database
async def test_get_role_query() -> None:
    """
    Test of adapter to get an role from query.
    """
    async with contextlib.AsyncExitStack() as stack:
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        await stack.enter_async_context(database.clear_between_tests())
        role_model = await stack.enter_async_context(database.role())
        get_role = role.GetRoleByName(session_factory)
        response = await get_role(role_model.name)
        assert response == role_model


@pytest.mark.asyncio
@pytest.mark.database
async def test_get_role_repo_query() -> None:
    """
    Test of adapter to get role.
    """
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        fake_role = await stack.enter_async_context(database.role())
        role_model = await uow.role_repository.get(fake_role.id)

        assert role_model == fake_role, role_model


@pytest.mark.asyncio
@pytest.mark.database
@hypothesis.given(role_schema=strats.create_role)
async def test_create_role(role_schema: dict[str, typing.Any]) -> None:
    """
    Test of adapter to create role.
    """
    role_model = _create_role_from_dict([role_schema])[0]
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        expected = await uow.role_repository.create(role_model)
        role_model = await uow.role_repository.get(expected.id)
        assert expected == role_model


@pytest.mark.asyncio
@pytest.mark.database
async def test_should_raise_already_exists() -> None:
    """
    Test of adapter to create role.
    """
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        role_model = await stack.enter_async_context(database.role())
        new_role_same_data = _create_role_from_dict(
            [{"name": role_model.name, "scopes": role_model.scopes}]
        )[0]
        new_role_same_data.id = role_model.id
        with pytest.raises(errors.AlreadyExists):
            await uow.role_repository.create(new_role_same_data)
