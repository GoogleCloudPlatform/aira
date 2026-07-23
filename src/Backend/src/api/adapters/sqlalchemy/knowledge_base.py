import logging
import uuid

import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, models, ports, typings

logger = logging.getLogger(__name__)


class KnowledgeBaseRepository(ports.KnowledgeBaseRepository):
    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        file_id: uuid.UUID,
    ) -> models.KnowledgeBaseFile | None:
        stmt = sa.select(models.KnowledgeBaseFile).where(
            models.KnowledgeBaseFile.id == file_id
        )
        result = await self._session.execute(stmt)
        return result.scalars().one_or_none()

    async def create(
        self,
        file_model: models.KnowledgeBaseFile,
    ) -> models.KnowledgeBaseFile:
        self._session.add(file_model)
        await self._session.flush()
        return file_model

    async def delete(
        self,
        file_model: models.KnowledgeBaseFile,
    ) -> None:
        await self._session.delete(file_model)


class ListKnowledgeBaseFiles(ports.ListKnowledgeBaseFiles):
    def __init__(self, session_factory: typings.SessionFactory) -> None:
        self._session_factory = session_factory

    async def __call__(
        self,
        page_size: int = 10,
        page: int = 1,
    ) -> tuple[list[models.KnowledgeBaseFile], typings.PaginationMetadata]:
        stmt = sa.select(models.KnowledgeBaseFile).order_by(
            models.KnowledgeBaseFile.created_at.desc()
        )

        async with self._session_factory() as session:
            if page_size >= 0:
                params = Params(page=page, size=page_size)
                result: typings.Paginated = await paginate(
                    session, stmt, params=params, unique=True
                )
            else:
                result_all = await session.execute(stmt)
                files_result = list(result_all.scalars().unique())
                return files_result, typings.PaginationMetadata(
                    current_page=1,
                    total_pages=1,
                    total_items=len(files_result),
                    page_size=len(files_result),
                )

        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )
