"""
Module for testing the organization repository.
"""
import contextlib
import math

import hypothesis
import pytest
from hypothesis import strategies as st

from api import errors, models, typings
from api.adapters.sqlalchemy import organization
from api.routers.organizations import schemas
from tests.helpers import database, strats


def _create_org_from_schema(
    schema_list: list[schemas.OrganizationCreate],
) -> list[models.Organization]:
    return [
        models.Organization(
            name=schema.name,
            city=schema.city,
            state=schema.state,
            region=schema.region,  # type: ignore[arg-type]
            customer_id=schema.customer_id,  # type: ignore[arg-type]
        )
        for schema in schema_list
    ]


@pytest.mark.asyncio
async def test_get_org_query() -> None:
    """
    Test of adapter to get an org from query.
    """
    async with contextlib.AsyncExitStack() as stack:
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        await stack.enter_async_context(database.clear_between_tests())
        org = await stack.enter_async_context(database.organization())
        get_org = organization.GetOrganization(session_factory)
        response = await get_org(org.id)
        assert response == org


@pytest.mark.asyncio
@hypothesis.given(
    organization_schema=st.builds(
        schemas.OrganizationCreate,
        state=strats.safe_text(min_size=2, max_size=2),
        city=strats.safe_text(),
        name=strats.safe_text(),
    ),
    page_size=st.one_of(st.just(10), st.integers(min_value=1, max_value=5)),
    city=st.one_of(strats.safe_text(min_size=1, max_size=10), st.none()),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
)
async def test_list_orgs_query(
    organization_schema: schemas.OrganizationCreate,
    page_size: int,
    city: str | None,
) -> None:
    """
    Test of adapter to list orgs.
    """
    async with contextlib.AsyncExitStack() as stack:
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        await stack.enter_async_context(database.clear_between_tests())
        list_orgs = organization.ListOrganizations(session_factory)
        async with session_factory() as session:
            org_schemas = [organization_schema] * 10
            schema_models = _create_org_from_schema(org_schemas)
            session.add_all(schema_models)
            await session.commit()

        expected = sorted(
            (org for org in schema_models if city is None or org.city == city),
            key=lambda x: x.updated_at,
            reverse=True,
        )
        expected_metadata = typings.PaginationMetadata(
            current_page=1,
            total_pages=math.ceil(len(expected) / page_size),
            total_items=len(expected),
            page_size=page_size,
        )

        items, params = await list_orgs(
            city=city,
            page_size=page_size,
        )
        assert items == expected[:page_size]
        assert params == expected_metadata


@pytest.mark.asyncio
async def test_get_org_repo_query() -> None:
    """
    Test of adapter to get org.
    """
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        fake_org = await stack.enter_async_context(database.organization())
        org = await uow.organization_repository.get(fake_org.id)

        assert org == fake_org, org


@pytest.mark.asyncio
@hypothesis.given(
    org_schema=st.builds(
        schemas.OrganizationCreate,
        state=strats.safe_text(min_size=1, max_size=2),
        city=strats.safe_text(),
        name=strats.safe_text(),
    )
)
async def test_create_org(org_schema: schemas.OrganizationCreate) -> None:
    """
    Test of adapter to create org.
    """
    org_model = _create_org_from_schema([org_schema])[0]
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        expected = await uow.organization_repository.create(org_model)
        org = await uow.organization_repository.get(expected.id)
        assert expected == org


@pytest.mark.asyncio
async def test_should_raise_already_exists() -> None:
    """
    Test of adapter to create org.
    """
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        org = await stack.enter_async_context(database.organization())
        new_org_same_data = _create_org_from_schema(
            [schemas.OrganizationCreate.from_orm(org)]
        )[0]
        new_org_same_data.id = org.id
        with pytest.raises(errors.AlreadyExists):
            await uow.organization_repository.create(new_org_same_data)
