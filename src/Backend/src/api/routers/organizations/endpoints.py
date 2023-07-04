"""
Module containing all endpoints related to org services
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
    city: str | None = fastapi.Query(default=None),
    list_data: util_schemas.ListSchema = fastapi.Depends(),
    list_orgs: ports.ListOrganizations = fastapi_injector.Injected(
        ports.ListOrganizations
    ),
) -> schemas.OrganizationList:
    """
    List organizations.

    Handles requests related to organizations being listed.

    :param list_orgs: implementation of orgs list.
    """
    result, pagination_metadata = await list_orgs(
        city=city, page_size=list_data.page_size, page=list_data.page, query=list_data.q
    )
    return schemas.OrganizationList(
        items=result,
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get(
    "/{organization_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def get(
    get_organization: ports.GetOrganization = fastapi_injector.Injected(
        ports.GetOrganization
    ),
    organization_id: uuid.UUID = fastapi.Path(...),
) -> schemas.OrganizationGet:
    """
    Get organizations.

    Handles requests related to finding a specific organization.

    :param get_organization: implementation organization get query.
    :param organization_id: query param with organization identifier.
    """
    organization = await get_organization(organization_id=organization_id)
    return schemas.OrganizationGet.from_orm(organization)


@router.post("", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])])
async def create(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.OrganizationCreate = fastapi.Body(...),
) -> schemas.OrganizationGet:
    """
    Create organization.

    Handles requests related to finding a specific organization.

    :param uow_builder: implementation organization get query.
    :param body: parsed data for organization creation.
    """
    organization = models.Organization(**body.dict())
    async with uow_builder() as uow:
        organization_model = await uow.organization_repository.create(organization)
        await uow.commit()

    return schemas.OrganizationGet.from_orm(organization_model)


@router.delete(
    "/{organization_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def delete(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    check_group: ports.CheckGroupOnOrg = fastapi_injector.Injected(
        ports.CheckGroupOnOrg
    ),
    organization_id: uuid.UUID = fastapi.Path(...),
) -> fastapi.Response:
    """
    Create organization.

    Handles requests related to finding a specific organization.

    :param uow_builder: implementation organization get query.
    :param body: parsed data for organization creation.
    """
    if await check_group(organization_id=organization_id):
        raise errors.CantDelete("organization", "groups")
    async with uow_builder() as uow:
        organization = await uow.organization_repository.get(organization_id)
        await uow.organization_repository.delete(organization)
        await uow.commit()

    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{organization_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def update(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.OrganizationCreate = fastapi.Body(...),
    organization_id: uuid.UUID = fastapi.Path(...),
) -> schemas.OrganizationGet:
    """
    Update a organization.

    Handles requests related to finding a specific organization.

    :param uow_builder: implementation organization get query.
    :param organization_id: query param with organization identifier.
    :param body: parsed data for organization patch.
    """
    body_dict = body.dict(exclude_unset=True)

    async with uow_builder() as uow:
        organization = await uow.organization_repository.get(organization_id)
        for key, value in body_dict.items():
            setattr(organization, key, value)
        await uow.commit()

    return schemas.OrganizationGet.from_orm(organization)
