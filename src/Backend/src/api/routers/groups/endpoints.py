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
Module containing all endpoints related to group services
"""
from __future__ import annotations

import logging
import uuid

import fastapi
import fastapi_injector

from api import errors, models, ports
from api.helpers import auth
from api.helpers import schemas as util_schemas

from . import schemas

router = fastapi.APIRouter()

logger = logging.getLogger(__name__)


@router.get("", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])])
async def list_resources(
    shift: str | None = fastapi.Query(default=None),
    grade: models.Grades | None = fastapi.Query(default=None),
    organizations: list[uuid.UUID] | None = fastapi.Query(default=None),
    list_data: util_schemas.ListSchema = fastapi.Depends(),
    list_groups: ports.ListGroups = fastapi_injector.Injected(ports.ListGroups),
) -> schemas.GroupsList:
    """
    List groups.

    Handles requests related to groups being listed.

    :param list_groups: implementation of groups list.
    """
    result, pagination_metadata = await list_groups(
        shift=shift,
        grade=grade,
        organizations=organizations,
        page_size=list_data.page_size,
        page=list_data.page,
        query=list_data.q,
    )

    return schemas.GroupsList(
        items=result,
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get(
    "/{group_id}", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])]
)
async def get(
    get_group: ports.GetGroup = fastapi_injector.Injected(ports.GetGroup),
    group_id: uuid.UUID = fastapi.Path(...),
) -> schemas.GroupGet:
    """
    Get groups.

    Handles requests related to finding a specific group.

    :param get_group: implementation group get query.
    :param group_id: query param with group identifier.
    """
    group = await get_group(group_id=group_id)
    return schemas.GroupGet.from_orm(group)


@router.post("", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])])
async def create(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.GroupCreate = fastapi.Body(...),
) -> schemas.GroupGet:
    """
    Create group.

    Handles requests related to finding a specific group.

    :param uow_builder: implementation group get query.
    :param body: parsed data for group creation.
    """
    group = models.Group(**body.dict())
    async with uow_builder() as uow:
        group_model = await uow.group_repository.create(group)
        await uow.commit()

    return schemas.GroupGet.from_orm(group_model)


@router.delete(
    "/{group_id}", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])]
)
async def delete(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    check_user: ports.CheckUserOnGroup = fastapi_injector.Injected(
        ports.CheckUserOnGroup
    ),
    group_id: uuid.UUID = fastapi.Path(...),
) -> fastapi.Response:
    """
    Create group.

    Handles requests related to finding a specific group.

    :param uow_builder: implementation group get query.
    :param body: parsed data for group creation.
    """
    if await check_user(group_id=group_id):
        raise errors.CantDelete("group", "users")
    async with uow_builder() as uow:
        group = await uow.group_repository.get(group_id)
        await uow.group_repository.delete(group)
        await uow.commit()

    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{group_id}", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])]
)
async def update(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.GroupPatch = fastapi.Body(...),
    group_id: uuid.UUID = fastapi.Path(...),
) -> schemas.GroupGet:
    """
    Update a group.

    Handles requests related to finding a specific group.

    :param uow_builder: implementation group get query.
    :param group_id: query param with group identifier.
    :param body: parsed data for group patch.
    """
    body_dict = body.dict(exclude_unset=True)

    async with uow_builder() as uow:
        group = await uow.group_repository.get(group_id)
        for key, value in body_dict.items():
            setattr(group, key, value)
        await uow.commit()

    return schemas.GroupGet.from_orm(group)
