"""
Module containing all endpoints related to org services
"""

from __future__ import annotations

import logging
import uuid

import fastapi
import fastapi_injector

from api import dependencies, errors, models, ports
from api.helpers import auth, data
from api.helpers import schemas as util_schemas
from api.helpers import session_manager as sess_mg

from . import crud, schemas

router = fastapi.APIRouter(tags=["organizations"])

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
    "/export",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def export_organizations(
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    list_organizations: ports.ListOrganizations = fastapi_injector.Injected(
        ports.ListOrganizations
    ),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    page_size: int = fastapi.Query(default=-1),
) -> fastapi.Response:
    """
    Export organizations as csv.

    :param session_manager: implementation of session to get current user.
    :param list_organizations: implementation of organizations list.
    :param storage: implementation of storage.
    """
    current_session = await session_manager.get_current_session()
    organizations, _ = await list_organizations(page_size=page_size)
    url = await data.handle_export(
        objs=organizations,
        export_keys=[
            "id",
            "customer_id",
            "name",
            "region",
            "city",
            "state",
            "county",
        ],
        user_id=current_session.user.id,
        exp_type="organizations",
        storage=storage,
    )
    return fastapi.responses.JSONResponse(content={"url": url})


@router.get(
    "/utils",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def list_unique_state_region_county(
    list_org_utils: ports.ListOrganizationUtils = fastapi_injector.Injected(
        ports.ListOrganizationUtils
    ),
) -> fastapi.Response:
    """
    List organizations utils data.

    Handles requests related to county/state/region of orgs.

    :param list_org_utils: implementation of orgs util list.
    """
    response = await list_org_utils()
    return fastapi.responses.JSONResponse(
        response, status_code=fastapi.status.HTTP_200_OK
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
    async with uow_builder() as uow:
        organization = await uow.organization_repository.get(organization_id)
        organization = crud.update_org(organization, body)
        await uow.commit()

    return schemas.OrganizationGet.from_orm(organization)


@router.put(
    "/batch",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def import_org_batch(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    body: util_schemas.ImportData = fastapi.Body(...),
) -> fastapi.Response:
    """
    Import organizations.

    Handles requests related to importing a specific groups.

    :param session_factory: implementation of session factory.
    :param body: parsed data for user import.
    """
    org_ids, customer_ids, result = await data.handle_import(
        body.url, body.key_relation, storage
    )
    async with uow_builder() as uow:
        org_list = await uow.organization_repository.list(
            org_ids=org_ids, customer_ids=customer_ids
        )
        for org_tmp in org_list:
            if org_tmp.id in result:
                org_data = result.pop(org_tmp.id)[0]
            elif org_tmp.customer_id and org_tmp.customer_id in result:
                org_data = result.pop(org_tmp.customer_id)[0]
            else:
                continue
            crud.update_org(org_tmp, schemas.OrganizationCreate.parse_obj(org_data))
        new_orgs = []
        for org_result in result.values():
            for org in org_result:
                org_obj = schemas.OrganizationCreate.parse_obj({**org})
                new_orgs.append(models.Organization(**org_obj.dict()))
        await uow.add_all(new_orgs)
        await uow.commit()
    return fastapi.responses.JSONResponse(
        {}, status_code=fastapi.status.HTTP_201_CREATED
    )
