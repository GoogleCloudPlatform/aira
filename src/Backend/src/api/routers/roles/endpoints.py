"""
Module containing all endpoints related to role services
"""
from __future__ import annotations

import logging
import uuid

import fastapi
import fastapi_injector

from api import ports
from api.helpers import auth

from . import schemas

router = fastapi.APIRouter()

logger = logging.getLogger(__name__)


@router.get("", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])])
async def list_resources(
    page_size: int = fastapi.Query(10, ge=1, le=100),
    page: int = fastapi.Query(1, ge=1, le=100),
    list_roles: ports.ListRoles = fastapi_injector.Injected(ports.ListRoles),
) -> schemas.RoleList:
    """
    List roles.

    Handles requests related to roles being listed.

    :param list_roles: implementation of orgs list.
    """
    result, pagination_metadata = await list_roles(
        page_size=page_size,
        page=page,
    )

    return schemas.RoleList(
        items=result,
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get(
    "/{role_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def get(
    get_role: ports.GetRole = fastapi_injector.Injected(ports.GetRole),
    role_id: uuid.UUID = fastapi.Path(...),
) -> schemas.RoleGet:
    """
    Get roles.

    Handles requests related to finding a specific role.

    :param get_role: implementation role get query.
    :param role_id: query param with role identifier.
    """
    role = await get_role(role_id=role_id)
    return schemas.RoleGet.from_orm(role)
