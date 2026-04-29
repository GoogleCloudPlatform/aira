import logging
import uuid
import sqlalchemy as sa
from sqlalchemy import exc
from sqlalchemy.ext import asyncio as sqlalchemy_aio
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from api import errors, models, ports, typings

logger = logging.getLogger(__name__)

class SeriesRepository(ports.SeriesRepository):
    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, series_id: uuid.UUID) -> models.Series:
        stmt = sa.select(models.Series).where(models.Series.id == series_id)
        result = await self._session.execute(stmt)
        if not (series := result.scalars().one_or_none()):
            raise errors.NotFound("series")
        return series

    async def create(self, series_model: models.Series) -> models.Series:
        self._session.add(series_model)
        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception
        return series_model

    async def delete(self, series_model: models.Series) -> None:
        await self._session.delete(series_model)

    async def list(self) -> list[models.Series]:
        stmt = sa.select(models.Series).order_by(models.Series.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())

class ListSeries(ports.ListSeries):
    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self, page_size: int = 10, page: int = 1, query: str | None = None
    ) -> tuple[list[models.Series], typings.PaginationMetadata]:
        stmt = sa.select(models.Series).order_by(models.Series.name.asc())
        if query:
            stmt = stmt.where(models.Series.name.ilike(f"%{query}%"))

        async with self._session_factory() as session:
            params = Params(page=page, size=page_size)
            result: typings.Paginated = await paginate(
                session, stmt, params=params, unique=True
            )

        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )

class GetSeries(ports.GetSeries):
    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, series_id: uuid.UUID) -> models.Series:
        stmt = sa.select(models.Series).where(models.Series.id == series_id)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            if not (series := result.scalars().one_or_none()):
                raise errors.NotFound("series")
            return series
