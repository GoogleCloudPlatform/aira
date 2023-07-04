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
Unit tests for `organizations/endpoints.py`
"""
import uuid

import hypothesis
import pytest
from hypothesis import strategies as st

from api import errors, models
from api.adapters.memory import group, organization, unit_of_work
from api.helpers import schemas as util_schemas
from api.helpers import time_now
from api.routers.organizations import endpoints as organizations_endpoint
from api.routers.organizations import schemas


@pytest.mark.asyncio
@hypothesis.given(
    page_size=st.integers(min_value=1, max_value=10),
    city=st.one_of(st.none(), st.just("test")),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
    max_examples=8,
)
async def test_list_organizations(
    page_size: int,
    city: str | None,
) -> None:
    """
    tests if auth endpoint calls correctly.
    """
    organizations: list[models.Organization] = []
    for i in range(page_size + 1):
        tmp_organization = models.Organization(
            state=f"{i}",
            region=f"test-{i}",
            customer_id=f"test-{i}",
            city=f"test-{i}",
            name=f"test-{i}",
        )
        tmp_organization.created_at = tmp_organization.updated_at = time_now()
        organizations.append(tmp_organization)
    list_organizations = organization.ListOrganizations(organizations)
    response = await organizations_endpoint.list_resources(
        city=city,
        list_data=util_schemas.ListSchema(page_size=page_size, page=1),
        list_orgs=list_organizations,
    )
    tmp_response = [
        schemas.Organization.from_orm(organization)
        for organization in organizations
        if (city is None or organization.city == city)
    ]
    final_response = tmp_response[:page_size]

    assert len(response.items) == min(page_size, len(final_response))
    assert response.items == final_response
    assert list_organizations.called == 1


@pytest.mark.asyncio
async def test_get_organization(
    fake_org: models.Organization,
) -> None:
    """
    tests if get is behaving properly.
    """
    get_organization = organization.GetOrganization([fake_org])
    response = await organizations_endpoint.get(
        get_organization=get_organization,
        organization_id=fake_org.id,
    )
    expected = schemas.OrganizationGet.from_orm(fake_org)
    assert response == expected

    # Testing now organization not found

    with pytest.raises(errors.NotFound):
        await organizations_endpoint.get(
            get_organization=get_organization,
            organization_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
@hypothesis.given(create_organization=st.builds(schemas.OrganizationCreate))
async def test_create_organization(
    create_organization: schemas.OrganizationCreate,
) -> None:
    """
    tests if get is behaving properly.
    """
    organization_repo = organization.OrganizationRepository()
    uow_builder = unit_of_work.UnitOfWorkBuilder(
        organization_repository=organization_repo
    )
    response = await organizations_endpoint.create(
        uow_builder=uow_builder, body=create_organization
    )
    assert uow_builder.call_count == 1
    assert await organization_repo.get(response.id)


@pytest.mark.asyncio
async def test_delete_organization(
    fake_org: models.Organization,
) -> None:
    """
    tests if delete is behaving properly.
    """
    organization_repo = organization.OrganizationRepository([fake_org])
    uow_builder = unit_of_work.UnitOfWorkBuilder(
        organization_repository=organization_repo
    )
    check_group = group.CheckGroupOnOrg([])
    await organizations_endpoint.delete(
        uow_builder=uow_builder,
        organization_id=fake_org.id,
        check_group=check_group,
    )
    assert uow_builder.call_count == 1
    with pytest.raises(errors.NotFound):
        await organization_repo.get(fake_org.id)


@pytest.mark.asyncio
async def test_delete_fails_organization(
    fake_org: models.Organization,
    fake_group: models.Group,
) -> None:
    """
    tests if delete is behaving properly.
    """
    organization_repo = organization.OrganizationRepository([fake_org])
    uow_builder = unit_of_work.UnitOfWorkBuilder(
        organization_repository=organization_repo
    )
    check_group = group.CheckGroupOnOrg([fake_group])
    with pytest.raises(errors.CantDelete):
        await organizations_endpoint.delete(
            uow_builder=uow_builder,
            organization_id=fake_org.id,
            check_group=check_group,
        )
    assert uow_builder.call_count == 0
    assert await organization_repo.get(fake_org.id)


@pytest.mark.asyncio
@hypothesis.given(patch_org=st.builds(schemas.OrganizationCreate))
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
    max_examples=8,
)
async def test_patch_organization(
    patch_org: schemas.OrganizationCreate,
    fake_org: models.Organization,
) -> None:
    """
    tests if patch is behaving properly.
    """
    organization_repo = organization.OrganizationRepository([fake_org])
    uow_builder = unit_of_work.UnitOfWorkBuilder(
        organization_repository=organization_repo
    )
    response = await organizations_endpoint.update(
        uow_builder=uow_builder, organization_id=fake_org.id, body=patch_org
    )
    expected = schemas.OrganizationGet.from_orm(fake_org)
    for key, value in patch_org.dict().items():
        if value is not None:
            setattr(expected, key, value)

    assert uow_builder.call_count == 1
    assert response.id == fake_org.id
    assert expected == response
