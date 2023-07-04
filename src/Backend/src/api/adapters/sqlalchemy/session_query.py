"""
Module related to the adapter of the session repository.
"""
from __future__ import annotations

import logging
import uuid

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from sqlalchemy import exc
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, models, ports, typings

logger = logging.getLogger(__name__)


class SessionRepository(ports.SessionRepository):
    """
    Session repository implementation.
    """

    def __init__(self, session: sqlalchemy_aio.AsyncSession):
        self._session = session

    async def get(self, session_id: uuid.UUID) -> models.Session:
        """
        Method to get the session for the user.

        :param session_id: the id for the session.

        :returns: session model.

        :raises errors.NotFound: if there's no such session.
        """
        stmt = (
            sa.select(models.Session)
            .where(models.Session.id == session_id)
            .options(sa_orm.joinedload(models.Session.user))
        )
        result = await self._session.execute(stmt)

        if not (session_model := result.unique().scalars().one_or_none()):
            raise errors.NotFound("session")

        return session_model

    async def create(self, session_model: models.Session) -> models.Session:
        """
        Method to create a session for the user.

        :param session_model: the session model parameter.

        :returns: session model.

        :raises errors.AlreadyExists: if the entity is duplicated.
        """
        self._session.add(session_model)

        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception

        await self._session.refresh(session_model, ["user"])

        return session_model

    async def delete(self, session_model: models.Session) -> None:
        """
        Method to delete a session from a user.

        :param session_model: the session model parameter.
        """
        await self._session.delete(session_model)


class GetSession(ports.GetSession):
    """
    Get session individualized.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, session_id: uuid.UUID) -> models.Session | None:
        """
        Method to get the session for the user.

        :param session_id: the id for the session.

        :returns: session model.

        :raises errors.NotFound: if there's no such session.
        """
        stmt = (
            sa.select(models.Session)
            .where(models.Session.id == session_id)
            .options(sa_orm.joinedload(models.Session.user))
        )
        session: sqlalchemy_aio.AsyncSession
        async with self._session_factory() as session:
            result = await session.execute(stmt)

        if not (session_model := result.unique().scalars().one_or_none()):
            return None

        return session_model
