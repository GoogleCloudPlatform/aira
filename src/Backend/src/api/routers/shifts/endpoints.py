import uuid

import fastapi
import fastapi_injector
from api import models, ports
from api.helpers import auth

from . import schemas

router = fastapi.APIRouter(tags=["shifts"])


@router.get(
    "",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.ShiftList,
)
async def list_shifts(
    list_shifts_query: ports.ListShifts = fastapi_injector.Injected(ports.ListShifts),
    page: int = 1,
    page_size: int = 10,
    q: str | None = None,
):
    items, metadata = await list_shifts_query(page=page, page_size=page_size, query=q)
    return {
        "items": items,
        "pages": metadata.total_pages,
        "total": metadata.total_items,
        "current_page": metadata.current_page,
    }


@router.get(
    "/{shift_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.ShiftGet,
)
async def get_shift(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    shift_id: uuid.UUID = fastapi.Path(...),
) -> schemas.ShiftGet:
    async with uow_builder() as uow:
        shift = await uow.shift_repository.get(shift_id)
        return schemas.ShiftGet.from_orm(shift)


@router.post(
    "",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.ShiftGet,
)
async def create_shift(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.ShiftCreate = fastapi.Body(...),
) -> schemas.ShiftGet:
    shift = models.WorkShift(**body.dict())
    async with uow_builder() as uow:
        shift_model = await uow.shift_repository.create(shift)
        await uow.commit()
        return schemas.ShiftGet.from_orm(shift_model)


@router.patch(
    "/{shift_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.ShiftGet,
)
async def update_shift(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.ShiftCreate = fastapi.Body(...),
    shift_id: uuid.UUID = fastapi.Path(...),
) -> schemas.ShiftGet:
    async with uow_builder() as uow:
        shift = await uow.shift_repository.get(shift_id)
        shift.name = body.name
        shift.code = body.code
        await uow.commit()
        return schemas.ShiftGet.from_orm(shift)


@router.delete(
    "/{shift_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def delete_shift(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    shift_id: uuid.UUID = fastapi.Path(...),
) -> fastapi.Response:
    async with uow_builder() as uow:
        shift = await uow.shift_repository.get(shift_id)
        await uow.shift_repository.delete(shift)
        await uow.commit()
    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)
