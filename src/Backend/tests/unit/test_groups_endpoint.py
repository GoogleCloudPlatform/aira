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
Unit tests for `groups/endpoints.py`
"""
import datetime
import uuid

import hypothesis
import pytest
from hypothesis import strategies as st

from api import errors, models
from api.adapters.memory import group, unit_of_work, user
from api.helpers import schemas as util_schemas
from api.routers.groups import endpoints as groups_endpoint
from api.routers.groups import schemas


@pytest.mark.asyncio
@hypothesis.given(
    page_size=st.integers(min_value=1, max_value=10),
    shift=st.one_of(st.none(), st.just("test")),
    grade=st.one_of(st.none(), st.just(models.Grades.FIRST_FUND)),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
    max_examples=8,
)
async def test_list_groups(
    page_size: int,
    shift: str | None,
    grade: models.Grades | None,
    fake_org: models.Organization,
) -> None:
    """
    tests if auth endpoint calls correctly.
    """
    groups = []
    for i in range(page_size + 1):
        tmp_group = models.Group(
            grade=models.Grades.FIRST_FUND,
            customer_id="fake",
            shift=f"test-{i}",
            name=f"test-{i}",
            organization_id=fake_org.id,
        )
        tmp_group.organization = fake_org
        tmp_group.created_at = datetime.datetime.now(tz=datetime.UTC)
        tmp_group.updated_at = datetime.datetime.now(tz=datetime.UTC)
        groups.append(tmp_group)
    list_groups = group.ListGroups(groups)
    response = await groups_endpoint.list_resources(
        shift=shift,
        grade=grade,
        organizations=None,
        list_groups=list_groups,
        list_data=util_schemas.ListSchema(
            page_size=page_size,
            page=1,
        ),
    )
    tmp_response = [
        schemas.GroupGet.from_orm(group)
        for group in groups
        if (grade is None or group.grade == grade)
        and (shift is None or group.shift == shift)
    ]
    final_response = tmp_response[:page_size]

    assert len(response.items) == min(page_size, len(final_response))
    assert response.items == final_response
    assert list_groups.called == 1


@pytest.mark.asyncio
async def test_get_group(
    fake_group: models.Group,
) -> None:
    """
    tests if get is behaving properly.
    """
    get_group = group.GetGroup([fake_group])
    response = await groups_endpoint.get(
        get_group=get_group,
        group_id=fake_group.id,
    )
    expected = schemas.GroupGet.from_orm(fake_group)
    assert response == expected

    # Testing now user not found

    with pytest.raises(errors.NotFound):
        await groups_endpoint.get(
            get_group=get_group,
            group_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
@hypothesis.given(create_group=st.builds(schemas.GroupCreate))
async def test_create_group(
    create_group: schemas.GroupCreate,
) -> None:
    """
    tests if get is behaving properly.
    """
    group_repo = group.GroupRepository()
    uow_builder = unit_of_work.UnitOfWorkBuilder(group_repository=group_repo)
    response = await groups_endpoint.create(uow_builder=uow_builder, body=create_group)
    assert uow_builder.call_count == 1
    assert await group_repo.get(response.id)


@pytest.mark.asyncio
async def test_delete_group(
    fake_group: models.Group,
) -> None:
    """
    tests if delete is behaving properly.
    """
    group_repo = group.GroupRepository([fake_group])
    uow_builder = unit_of_work.UnitOfWorkBuilder(group_repository=group_repo)
    check_user = user.CheckUserOnGroup([])
    await groups_endpoint.delete(
        uow_builder=uow_builder, group_id=fake_group.id, check_user=check_user
    )
    assert uow_builder.call_count == 1
    with pytest.raises(errors.NotFound):
        await group_repo.get(fake_group.id)


@pytest.mark.asyncio
async def test_delete_group_should_fail(
    fake_group: models.Group,
    fake_user: models.User,
) -> None:
    """
    tests if delete is behaving properly.
    """
    group_repo = group.GroupRepository([fake_group])
    uow_builder = unit_of_work.UnitOfWorkBuilder(group_repository=group_repo)
    check_user = user.CheckUserOnGroup([fake_user])
    with pytest.raises(errors.CantDelete):
        await groups_endpoint.delete(
            uow_builder=uow_builder, group_id=fake_group.id, check_user=check_user
        )
    assert uow_builder.call_count == 0
    assert await group_repo.get(fake_group.id)


@pytest.mark.asyncio
@hypothesis.given(patch_org=st.builds(schemas.GroupPatch))
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
    max_examples=8,
)
async def test_patch_group(
    patch_org: schemas.GroupPatch,
    fake_group: models.Group,
) -> None:
    """
    tests if patch is behaving properly.
    """
    group_repo = group.GroupRepository([fake_group])
    uow_builder = unit_of_work.UnitOfWorkBuilder(group_repository=group_repo)
    response = await groups_endpoint.update(
        uow_builder=uow_builder, group_id=fake_group.id, body=patch_org
    )
    expected = schemas.GroupGet.from_orm(fake_group)
    for key, value in patch_org.dict().items():
        if value is not None:
            setattr(expected, key, value)

    assert uow_builder.call_count == 1
    assert response.id == fake_group.id
    assert expected == response
