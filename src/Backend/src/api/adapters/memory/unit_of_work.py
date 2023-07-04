"""
Module with the implementation of sqlalchemy's sessions.
"""
from __future__ import annotations

import typing

from api import ports

from . import exam, group, organization, result, role, session_query, user


# pylint: disable=too-many-instance-attributes
class UnitOfWorkBuilder(ports.UnitOfWorkBuilder):
    """
    Session memory implementation builder related stuff.
    """

    def __init__(
        self,
        user_repository: ports.UserRepository | None = None,
        session_repository: ports.SessionRepository | None = None,
        group_repository: ports.GroupRepository | None = None,
        organization_repository: ports.OrganizationRepository | None = None,
        role_repository: ports.RoleRepository | None = None,
        exam_repository: ports.ExamRepository | None = None,
        question_repository: ports.QuestionRepository | None = None,
        result_repository: ports.ResultRepository | None = None,
    ) -> None:
        self.call_count = 0
        self.user_repository = user_repository or user.UserRepository()
        self.group_repository = group_repository or group.GroupRepository()
        self.organization_repository = (
            organization_repository or organization.OrganizationRepository()
        )
        self.session_repository = (
            session_repository or session_query.SessionRepository()
        )
        self.role_repository = role_repository or role.RoleRepository()
        self.exam_repository = exam_repository or exam.ExamRepository()
        self.question_repository = question_repository or exam.QuestionRepository()
        self.result_repository = result_repository or result.ResultRepository()

    async def _create(self) -> ports.UnitOfWork:
        self.call_count += 1
        return UnitOfWork(
            user_repository=self.user_repository,
            session_repository=self.session_repository,
            group_repository=self.group_repository,
            organization_repository=self.organization_repository,
            role_repository=self.role_repository,
            exam_repository=self.exam_repository,
            question_repository=self.question_repository,
            result_repository=self.result_repository,
        )


class UnitOfWork(ports.UnitOfWork):
    """
    Implementation of sqlalchemy's memory implementation session.
    """

    def __init__(
        self,
        user_repository: ports.UserRepository,
        session_repository: ports.SessionRepository,
        group_repository: ports.GroupRepository,
        organization_repository: ports.OrganizationRepository,
        role_repository: ports.RoleRepository,
        exam_repository: ports.ExamRepository,
        question_repository: ports.QuestionRepository,
        result_repository: ports.ResultRepository,
    ) -> None:
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.group_repository = group_repository
        self.organization_repository = organization_repository
        self.role_repository = role_repository
        self.exam_repository = exam_repository
        self.question_repository = question_repository
        self.result_repository = result_repository
        self.closed = False
        self.committed = False

    async def close(self) -> None:
        self.closed = True

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    async def flush(self) -> None:
        pass

    async def merge(self, obj: typing.Any) -> typing.Any:
        return obj
