# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Module with the implementation of sqlalchemy's sessions.
"""
from __future__ import annotations

import typing

from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import ports
from api.typings import SessionFactory

from . import exam, group, organization, result, role, session_query, user


class UnitOfWorkBuilder(ports.UnitOfWorkBuilder):
    """
    Session builder related stuff.
    """

    def __init__(
        self,
        session_factory: SessionFactory,
    ) -> None:
        self._session_factory = session_factory

    async def _create(self) -> ports.UnitOfWork:
        session = self._session_factory()

        return UnitOfWork(
            session=session,
        )


# pylint: disable=too-many-instance-attributes
class UnitOfWork(ports.UnitOfWork):
    """
    Implementation of sqlalchemy's session.
    """

    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session
        self.closed = False
        self.user_repository = user.UserRepository(
            session=session,
        )
        self.session_repository = session_query.SessionRepository(
            session=session,
        )
        self.group_repository = group.GroupRepository(
            session=session,
        )
        self.organization_repository = organization.OrganizationRepository(
            session=session,
        )
        self.role_repository = role.RoleRepository(
            session=session,
        )
        self.exam_repository = exam.ExamRepository(
            session=session,
        )
        self.question_repository = exam.QuestionRepository(
            session=session,
        )
        self.result_repository = result.ResultRepository(
            session=session,
        )

    async def close(self) -> None:
        if not self.closed:
            await self._session.close()
            self.closed = True

    async def merge(self, obj: typing.Any) -> typing.Any:
        return await self._session.merge(obj)

    async def commit(self) -> None:
        if not self.closed:
            await self._session.commit()
            self.committed = True

    async def flush(self) -> None:
        await self._session.flush()

    async def rollback(self) -> None:
        if not self._session.dirty or self.closed:
            return
        await self._session.rollback()
