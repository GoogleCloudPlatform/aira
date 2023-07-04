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
Module containing all endpoints related to user services
"""
from __future__ import annotations

import logging
import uuid

import fastapi
import fastapi_injector
from passlib import context

from api import dependencies, errors, ports
from api.helpers import auth
from api.helpers import session_manager as sess_mg
from api.helpers.schemas import ListSchema

from . import crud, schemas

router = fastapi.APIRouter()

logger = logging.getLogger(__name__)


@router.get("/me", dependencies=[fastapi.Security(auth.get_token)])
async def get_profile(
    get_user: ports.GetUser = fastapi_injector.Injected(ports.GetUser),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
) -> schemas.UserGet:
    """
    Get current user.
    :param get_user: implementation for get user port.
    :param session_manager: session manager to get current user.
    """
    current_user = await session_manager.get_current_session()
    user = await get_user(user_id=current_user.user_id)
    return schemas.UserGet.from_orm(user)


@router.get("", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])])
async def list_resources(
    roles: list[uuid.UUID] | None = fastapi.Query(default=None),
    groups: list[uuid.UUID] | None = fastapi.Query(default=None),
    organizations: list[uuid.UUID] | None = fastapi.Query(default=None),
    list_data: ListSchema = fastapi.Depends(),
    list_users: ports.ListUsers = fastapi_injector.Injected(ports.ListUsers),
) -> schemas.UserList:
    """
    List users.

    Handles requests related to users being listed.

    :param list_users: implementation of orgs list.
    """
    result, pagination_metadata = await list_users(
        roles=roles,
        groups=groups,
        organizations=organizations,
        page_size=list_data.page_size,
        page=list_data.page,
        query=list_data.q,
    )

    return schemas.UserList(
        items=result,
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get(
    "/{user_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def get(
    get_user: ports.GetUser = fastapi_injector.Injected(ports.GetUser),
    user_id: uuid.UUID = fastapi.Path(...),
) -> schemas.UserGet:
    """
    Get users.

    Handles requests related to finding a specific user.

    :param get_user: implementation user get query.
    :param user_id: query param with user identifier.
    """
    user = await get_user(user_id=user_id)
    return schemas.UserGet.from_orm(user)


@router.post("", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])])
async def create(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.UserCreate = fastapi.Body(...),
    list_groups: ports.ListGroupsWithoutOrg = fastapi_injector.Injected(
        ports.ListGroupsWithoutOrg
    ),
    list_organizations: ports.ListOrganizations = fastapi_injector.Injected(
        ports.ListOrganizations
    ),
    hash_ctx: context.CryptContext = fastapi_injector.Injected(context.CryptContext),
) -> schemas.UserGet:
    """
    Create user.

    Handles requests related to creating a specific user.

    :param uow_builder: implementation user get query.
    :param body: parsed data for user creation.
    """
    async with uow_builder() as uow:
        groups = await list_groups(
            groups=body.groups,
        )
        orgs, _ = await list_organizations(
            organizations=body.organizations,
            page_size=len(body.organizations)
            if body.organizations is not None and len(body.organizations) > 0
            else 1,
        )
        user_model = await crud.create_user(
            body=body,
            uow=uow,
            hash_ctx=hash_ctx,
            groups=groups if body.groups is not None else None,
            organizations=orgs if body.organizations is not None else None,
        )
        await uow.commit()

    return schemas.UserGet.from_orm(user_model)


@router.delete(
    "/{user_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def delete(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    user_id: uuid.UUID = fastapi.Path(...),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
) -> fastapi.Response:
    """
    Delete user.

    Handles requests related to deleting a specific user.

    :param uow_builder: implementation user get query.
    :param body: parsed data for user deletion.
    """
    current_user = await session_manager.get_current_session()
    if current_user.user_id == user_id:
        raise errors.CantDeleteYourself()
    async with uow_builder() as uow:
        user = await uow.user_repository.get(user_id)
        await uow.user_repository.delete(user)
        await uow.commit()

    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{user_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def update(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.UserPatch = fastapi.Body(...),
    list_groups: ports.ListGroupsWithoutOrg = fastapi_injector.Injected(
        ports.ListGroupsWithoutOrg
    ),
    list_organizations: ports.ListOrganizations = fastapi_injector.Injected(
        ports.ListOrganizations
    ),
    user_id: uuid.UUID = fastapi.Path(...),
) -> schemas.UserGet:
    """
    Update a user.

    Handles requests related to updating a specific users.

    :param uow_builder: implementation user get query.
    :param user_id: query param with user identifier.
    :param body: parsed data for user patch.
    """
    body_dict = body.dict(exclude_unset=True)

    async with uow_builder() as uow:
        user = await uow.user_repository.get(user_id)
        group_ids = [group.id for group in user.groups]
        org_ids = [organization.id for organization in user.organizations]
        for key, value in body_dict.items():
            if key == "groups":
                user.groups = [group for group in user.groups if group.id in value]
                groups = [group for group in value if group not in group_ids]
                if groups:
                    user.groups.extend(await list_groups(groups=groups))
            elif key == "organizations":
                user.organizations = [
                    organization
                    for organization in user.organizations
                    if organization.id in value
                ]
                organizations = [
                    organization
                    for organization in value
                    if organization not in org_ids
                ]
                if organizations:
                    orgs, _ = await list_organizations(
                        organizations=organizations,
                        page_size=len(organizations),
                    )
                    user.organizations.extend(orgs)
            else:
                setattr(user, key, value)

        await crud.validate_default_user(user)
        await uow.commit()

    return schemas.UserGet.from_orm(user)
