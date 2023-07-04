"""
Module for all user related sqlalchemy queries.
"""

import logging
import uuid

import sqlalchemy as sa
from sqlalchemy import exc, orm
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, models, ports

logger = logging.getLogger(__name__)


class ResultRepository(ports.ResultRepository):
    """
    Result repository implementation that returns result data.
    """

    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, result_id: uuid.UUID) -> models.ExamUserQuestion:
        """
        Get result by params.

        :params result_id: result id on database.
        """
        stmt = (
            sa.select(models.ExamUserQuestion)
            .options(
                orm.joinedload(models.ExamUserQuestion.organization),
            )
            .options(
                orm.joinedload(models.ExamUserQuestion.user),
            )
            .options(
                orm.joinedload(models.ExamUserQuestion.group),
            )
            .options(
                orm.joinedload(models.ExamUserQuestion.exam),
            )
            .where(models.ExamUserQuestion.id == result_id)
        )

        result = await self._session.execute(stmt)
        if not (resp := result.scalars().unique().one_or_none()):
            raise errors.NotFound("result")
        return resp

    async def create(
        self, result_model: models.ExamUserQuestion
    ) -> models.ExamUserQuestion:
        """
        Method to create a result.

        :param result_model: the result model parameter.

        :returns: result model.

        :raises errors.AlreadyExists: if the entity is duplicated.
        """
        self._session.add(result_model)

        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception

        return result_model

    async def delete(self, result_model: models.ExamUserQuestion) -> None:
        """
        Method to delete a result.

        :param result_model: the result model parameter.
        """
        await self._session.delete(result_model)
