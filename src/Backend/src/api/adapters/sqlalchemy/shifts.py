import uuid

import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import exc
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, models, ports, typings


class WorkShiftRepository(ports.WorkShiftRepository):
    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, shift_id: uuid.UUID) -> models.WorkShift:
        stmt = sa.select(models.WorkShift).where(models.WorkShift.id == shift_id)
        result = await self._session.execute(stmt)
        if not (shift := result.scalars().one_or_none()):
            raise errors.NotFound()
        return shift

    async def create(self, shift: models.WorkShift) -> models.WorkShift:
        self._session.add(shift)
        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception
        return shift

    async def delete(self, shift: models.WorkShift) -> None:
        await self._session.delete(shift)

    async def list(
        self, shift_ids: list[uuid.UUID] | None = None
    ) -> list[models.WorkShift]:
        stmt = sa.select(models.WorkShift)
        if shift_ids:
            stmt = stmt.where(models.WorkShift.id.in_(shift_ids))
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())


class ListShifts(ports.ListShifts):
    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.WorkShift], typings.PaginationMetadata]:
        stmt = sa.select(models.WorkShift).order_by(models.WorkShift.name.asc())
        if query:
            stmt = stmt.where(models.WorkShift.name.ilike(f"%{query}%"))

        async with self._session_factory() as session:
            params = Params(page=page, size=page_size)
            result: typings.Paginated = await paginate(session, stmt, params=params)

        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )


class GetShift(ports.GetShift):
    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, shift_id: uuid.UUID) -> models.WorkShift:
        stmt = sa.select(models.WorkShift).where(models.WorkShift.id == shift_id)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            if not (shift := result.scalars().one_or_none()):
                raise errors.NotFound()
            return shift
