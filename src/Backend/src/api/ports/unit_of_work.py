"""
Module related to the port of any external auth.
"""
from __future__ import annotations

import abc
import collections.abc
import contextlib
import typing

from sqlalchemy.ext import asyncio as sqlalchemy_aio

from . import exam, group, organization, result, role, session_query, user


# pylint: disable=too-few-public-methods
class UnitOfWorkBuilder(abc.ABC):
    """
    Port related to Session Builder.
    """

    @contextlib.asynccontextmanager
    async def __call__(self) -> collections.abc.AsyncIterator[UnitOfWork]:
        session = await self._create()

        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

    @abc.abstractmethod
    async def _create(self) -> UnitOfWork:
        ...


class UnitOfWork(abc.ABC):
    """
    Port related to Session.
    """

    exam_repository: exam.ExamRepository
    user_repository: user.UserRepository
    session_repository: session_query.SessionRepository
    group_repository: group.GroupRepository
    organization_repository: organization.OrganizationRepository
    role_repository: role.RoleRepository
    question_repository: exam.QuestionRepository
    result_repository: result.ResultRepository
    closed: bool
    _session: sqlalchemy_aio.AsyncSession
    committed: bool

    @abc.abstractmethod
    async def close(self) -> None:
        """
        Close session
        """

    @abc.abstractmethod
    async def commit(self) -> None:
        """
        Commit session
        """

    @abc.abstractmethod
    async def merge(self, obj: typing.Any) -> typing.Any:
        """
        Merge session
        """

    @abc.abstractmethod
    async def rollback(self) -> None:
        """
        Rollback session
        """

    @abc.abstractmethod
    async def flush(self) -> None:
        """
        Flush session
        """
