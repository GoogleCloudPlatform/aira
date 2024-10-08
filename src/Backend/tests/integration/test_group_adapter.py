"""
Module for testing the group repository.
"""

import contextlib
import math

import hypothesis
import pytest
from api import errors, models, typings
from api.adapters.sqlalchemy import group
from api.routers.groups import schemas
from hypothesis import strategies as st

from tests.helpers import database, strats


def _create_group_from_schema(
    schema_list: list[schemas.GroupCreate],
) -> list[models.Group]:
    return [
        models.Group(
            name=schema.name,
            shift=schema.shift,
            grade=schema.grade,
            organization_id=schema.organization_id,
            customer_id=schema.customer_id,
        )
        for schema in schema_list
    ]


@pytest.mark.asyncio
@pytest.mark.database
async def test_get_group_query() -> None:
    """
    Test of adapter to get an group from query.
    """
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(database.clear_between_tests())
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        org = await stack.enter_async_context(database.organization())
        group_model = await stack.enter_async_context(database.group(org))
        get_group = group.GetGroup(session_factory)
        response = await get_group(group_model.id)
        assert response == group_model


@pytest.mark.asyncio
@pytest.mark.database
@hypothesis.given(
    group_schema=st.builds(
        schemas.GroupCreate,
        name=strats.safe_text(),
        shift=st.sampled_from(models.Shifts),
        grade=st.sampled_from(models.Grades),
    ),
    page_size=st.one_of(st.just(10), st.integers(min_value=1, max_value=5)),
    shift=st.one_of(st.none(), st.sampled_from(models.Shifts)),
    grade=st.one_of(st.none(), st.sampled_from(models.Grades)),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
)
async def test_list_groups_query(
    group_schema: schemas.GroupCreate,
    page_size: int,
    shift: models.Shifts | None,
    grade: models.Grades | None,
) -> None:
    """
    Test of adapter to list groups.
    """
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(database.clear_between_tests())
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        org = await stack.enter_async_context(database.organization())
        group_schema.organization_id = org.id
        group_schemas = [group_schema] * 10
        schema_models = _create_group_from_schema(group_schemas)

        list_groups = group.ListGroups(session_factory)
        async with session_factory() as session:
            session.add_all(schema_models)
            await session.flush()
            await session.commit()
            for mod in schema_models:
                await session.refresh(mod, ["organization"])

        expected = [
            group_model
            for group_model in schema_models
            if (shift is None or group_model.shift == shift)
            and (grade is None or group_model.grade == grade)
        ]
        expected_metadata = typings.PaginationMetadata(
            current_page=1,
            total_pages=math.ceil(len(expected) / page_size),
            total_items=len(expected),
            page_size=page_size,
        )
        items, params = await list_groups(
            shift=shift,
            grade=grade,
            page_size=page_size,
        )
        assert items == expected[:page_size]
        assert params == expected_metadata


@pytest.mark.asyncio
@pytest.mark.database
async def test_get_group_repo_query() -> None:
    """
    Test of adapter to get group.
    """
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(database.clear_between_tests())
        uow = await stack.enter_async_context(database.uow_ctx())
        org = await stack.enter_async_context(database.organization())
        fake_group = await stack.enter_async_context(database.group(org))
        group_model = await uow.group_repository.get(fake_group.id)

        assert group_model == fake_group, group_model


@pytest.mark.asyncio
@pytest.mark.database
@hypothesis.given(
    group_schema=st.builds(
        schemas.GroupCreate,
        shift=st.sampled_from(models.Shifts),
        grade=st.sampled_from(models.Grades),
        name=strats.safe_text(),
    )
)
async def test_create_group_adapter(group_schema: schemas.GroupCreate) -> None:
    """
    Test of adapter to create group.
    """
    group_model = _create_group_from_schema([group_schema])[0]
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(database.clear_between_tests())
        org = await stack.enter_async_context(database.organization())
        group_model.organization_id = org.id
        uow = await stack.enter_async_context(database.uow_ctx())
        expected = await uow.group_repository.create(group_model)
        group_model = await uow.group_repository.get(expected.id)
        assert expected == group_model


@pytest.mark.asyncio
@pytest.mark.database
async def test_should_raise_already_exists() -> None:
    """
    Test of adapter to create group.
    """
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(database.clear_between_tests())
        uow = await stack.enter_async_context(database.uow_ctx())
        org = await stack.enter_async_context(database.organization())
        group_model = await stack.enter_async_context(database.group(org))
        new_group_same_data = _create_group_from_schema(
            [schemas.GroupCreate.from_orm(group_model)]
        )[0]
        new_group_same_data.id = group_model.id
        with pytest.raises(errors.AlreadyExists):
            await uow.group_repository.create(new_group_same_data)
