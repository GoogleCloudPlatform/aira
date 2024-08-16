"""
Module containing all endpoints related to group services
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

router = fastapi.APIRouter(tags=["groups"])

logger = logging.getLogger(__name__)


@router.get(
    "", dependencies=[fastapi.Security(auth.get_token, scopes=["admin", "group.list"])]
)
async def list_resources(
    shift: str | None = fastapi.Query(default=None),
    grade: models.Grades | None = fastapi.Query(default=None),
    organizations: list[uuid.UUID] | None = fastapi.Query(default=None),
    list_data: util_schemas.ListSchema = fastapi.Depends(),
    list_groups: ports.ListGroups = fastapi_injector.Injected(ports.ListGroups),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
) -> schemas.GroupsList:
    """
    List groups.

    Handles requests related to groups being listed.

    :param shift: shift filter for query.
    :param grade: grade filter for query.
    :param organizations: organizations filter for query.
    :param list_data: common list schema.
    :param list_groups: implementation of groups list.
    :param session_manager: implementation of session to get current user.
    """
    current_session = await session_manager.get_current_session()
    group_ids = None
    if "admin" not in current_session.user.role.scopes:
        group_ids = (
            [gp.id for gp in current_session.user.groups]
            if current_session.user.groups
            else None
        )
        organizations = (
            [
                org.id
                for org in current_session.user.organizations
                if not organizations or org.id in organizations
            ]
            if current_session.user.organizations
            else None
        )
    result, pagination_metadata = await list_groups(
        groups=group_ids,
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
    "/export",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def export_groups(
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    list_groups: ports.ListGroups = fastapi_injector.Injected(ports.ListGroups),
    organizations: list[uuid.UUID] | None = fastapi.Query(default=None),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    page_size: int = fastapi.Query(default=-1),
) -> fastapi.Response:
    """
    Export groups as csv.

    :param session_manager: implementation of session to get current user.
    :param list_groups: implementation of groups list.
    :param storage: implementation of storage.
    """
    current_session = await session_manager.get_current_session()
    groups, _ = await list_groups(organizations=organizations, page_size=page_size)
    url = await data.handle_export(
        objs=groups,
        export_keys=[
            "id",
            "customer_id",
            "name",
            "organization_id",
            "grade",
            "shift",
        ],
        user_id=current_session.user.id,
        exp_type="groups",
        storage=storage,
    )
    return fastapi.responses.JSONResponse(content={"url": url})


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


@router.put(
    "/batch",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def import_groups_batch(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    body: util_schemas.ImportData = fastapi.Body(...),
) -> fastapi.Response:
    """
    Import groups.

    Handles requests related to importing a specific groups.

    :param session_factory: implementation of session factory.
    :param body: parsed data for user import.
    """

    group_ids, customer_ids, result = await data.handle_import(
        body.url, body.key_relation, storage
    )
    async with uow_builder() as uow:
        group_list = await uow.group_repository.list(
            group_ids=group_ids, customer_ids=customer_ids
        )
        for group_tmp in group_list:
            if group_tmp.id in result:
                group_data = result.pop(group_tmp.id)[0]
            elif group_tmp.customer_id and group_tmp.customer_id in result:
                group_data = result.pop(group_tmp.customer_id)[0]
            else:
                continue
            group_data["organization_id"] = uuid.UUID(
                group_data.get("organization", group_data.get("organization_id"))
            )
            await crud.update_group(group_tmp, schemas.GroupPatch.parse_obj(group_data))
        new_groups = []
        for group_result in result.values():
            for group in group_result:
                try:
                    organization_id = uuid.UUID(
                        group.get("organization", group.get("organization_id"))
                    )
                except ValueError as exc:
                    raise errors.InvalidModelId("organization") from exc
                group_obj = schemas.GroupCreate.parse_obj(
                    {**group, "organization_id": organization_id}
                )
                new_groups.append(models.Group(**group_obj.dict()))
        await uow.add_all(new_groups)
        await uow.commit()
    return fastapi.responses.JSONResponse(
        {}, status_code=fastapi.status.HTTP_201_CREATED
    )
