import logging
import uuid

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, models, ports

logger = logging.getLogger(__name__)


class TutorialRepository(ports.TutorialRepository):
    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, tutorial_id: uuid.UUID) -> models.Tutorial:
        stmt = sa.select(models.Tutorial).where(models.Tutorial.id == tutorial_id)
        result = await self._session.execute(stmt)
        if not (tutorial := result.scalars().one_or_none()):
            raise errors.NotFound("tutorial")
        return tutorial

    async def create(self, tutorial_model: models.Tutorial) -> models.Tutorial:
        self._session.add(tutorial_model)
        await self._session.flush()
        return tutorial_model

    async def delete(self, tutorial_model: models.Tutorial) -> None:
        await self._session.delete(tutorial_model)

    async def get_latest_by_audience(self, audience: str) -> models.Tutorial | None:
        stmt = (
            sa.select(models.Tutorial)
            .where(models.Tutorial.audience == audience)
            .order_by(models.Tutorial.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()
