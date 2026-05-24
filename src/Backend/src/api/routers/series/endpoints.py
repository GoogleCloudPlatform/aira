import uuid

import fastapi
import fastapi_injector
from api import errors, models, ports
from api.helpers import auth

from . import schemas

router = fastapi.APIRouter(tags=["series"])


@router.get(
    "",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def list_series(
    list_series_query: ports.ListSeries = fastapi_injector.Injected(ports.ListSeries),
    page: int = 1,
    page_size: int = 10,
    q: str | None = None,
):
    items, metadata = await list_series_query(page=page, page_size=page_size, query=q)
    return {
        "items": items,
        "pages": metadata.total_pages,
        "total": metadata.total_items,
        "current_page": metadata.current_page,
    }


@router.get(
    "/{series_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.SeriesGet,
)
async def get_series(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    series_id: uuid.UUID = fastapi.Path(...),
) -> schemas.SeriesGet:
    async with uow_builder() as uow:
        series = await uow.series_repository.get(series_id)
        return schemas.SeriesGet.from_orm(series)


@router.post(
    "",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.SeriesGet,
)
async def create_series(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.SeriesCreate = fastapi.Body(...),
) -> schemas.SeriesGet:
    series = models.Series(**body.dict())
    async with uow_builder() as uow:
        try:
            series_model = await uow.series_repository.create(series)
            await uow.commit()
            return schemas.SeriesGet.from_orm(series_model)
        except errors.AlreadyExists:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_409_CONFLICT,
                detail="Series already exists",
            )


@router.put(
    "/{series_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.SeriesGet,
)
async def update_series(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.SeriesCreate = fastapi.Body(...),
    series_id: uuid.UUID = fastapi.Path(...),
) -> schemas.SeriesGet:
    async with uow_builder() as uow:
        series = await uow.series_repository.get(series_id)
        series.name = body.name
        series.code = body.code
        await uow.commit()
        return schemas.SeriesGet.from_orm(series)


@router.delete(
    "/{series_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def delete_series(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    series_id: uuid.UUID = fastapi.Path(...),
):
    async with uow_builder() as uow:
        series = await uow.series_repository.get(series_id)
        await uow.series_repository.delete(series)
        await uow.commit()
    return {"detail": "Series deleted"}
