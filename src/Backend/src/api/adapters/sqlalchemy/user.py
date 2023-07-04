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
Module for all user related sqlalchemy queries.
"""
import logging
import uuid

import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import exc, func, orm
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, models, ports, typings

logger = logging.getLogger(__name__)


class UserRepository(ports.UserRepository):
    """
    User repository implementation that returns user data.
    """

    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        user_id: uuid.UUID | None = None,
        external_id: str | None = None,
        email: str | None = None,
    ) -> models.User:
        """
        Get user by params.

        :params user_id: user id on database.
        :params external_id: user id provided by firebase.
        :params email: user's email.
        """
        stmt = (
            sa.select(models.User)
            .options(
                orm.joinedload(models.User.role),
            )
            .options(
                orm.joinedload(models.User.groups),
            )
            .options(
                orm.joinedload(models.User.organizations),
            )
        )
        if user_id:
            stmt = stmt.where(models.User.id == user_id)
        if external_id:
            stmt = stmt.where(models.User.external_id == external_id)
        if email:
            stmt = stmt.where(func.lower(models.User.email_address) == email.lower())
        result = await self._session.execute(stmt)
        if not (user := result.unique().scalars().one_or_none()):
            raise errors.NotFound("user")
        return user

    async def create(self, user_model: models.User) -> models.User:
        """
        Method to create a user.

        :param user_model: the user model parameter.

        :returns: user model.

        :raises errors.AlreadyExists: if the entity is duplicated.
        """
        self._session.add(user_model)

        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception

        return user_model

    async def delete(self, user_model: models.User) -> None:
        """
        Method to delete a user.

        :param user_model: the user model parameter.
        """
        await self._session.delete(user_model)


class ListUsers(ports.ListUsers):
    """
    Query to get all users.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        roles: list[uuid.UUID] | None = None,
        groups: list[uuid.UUID] | None = None,
        organizations: list[uuid.UUID] | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.User], typings.PaginationMetadata]:
        """
        Method to list all users.
        """
        user = models.User
        org = models.Organization
        group = models.Group
        stmt = sa.select(user).order_by(user.updated_at.desc())
        if organizations or query:
            stmt = stmt.outerjoin(models.UserOrganization)

        if groups or query:
            stmt = stmt.outerjoin(models.UserGroup)

        if roles:
            stmt = stmt.where(user.role_id.in_(roles))
        if groups:
            stmt = stmt.where(models.UserGroup.group_id.in_(groups))
        if organizations:
            stmt = stmt.where(
                models.UserOrganization.organization_id.in_(organizations)
            )
        if query:
            stmt = (
                stmt.outerjoin(org)
                .outerjoin(group)
                .where(
                    sa.or_(
                        user.name.ilike(f"%{query}%"),
                        user.email_address.ilike(f"%{query}%"),
                        org.name.ilike(f"%{query}%"),
                        group.name.ilike(f"%{query}%"),
                    )
                )
                .group_by(user.id)
            )

        params = Params(page=page, size=page_size)
        async with self._session_factory() as session:
            result: typings.Paginated = await paginate(session, stmt, params=params)
        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )


class GetUser(ports.GetUser):
    """
    Query to get a specific user.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, user_id: uuid.UUID) -> models.User:
        """
        Method to get a specific user.

        :param user_id: the user identifier.
        """
        stmt = (
            sa.select(models.User)
            .options(
                orm.joinedload(models.User.role),
            )
            .options(
                orm.joinedload(models.User.groups),
            )
            .where(models.User.id == user_id)
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)

        if not (user := result.unique().scalars().one_or_none()):
            raise errors.NotFound("user")
        return user


class CheckUserOnGroup(ports.CheckUserOnGroup):
    """
    Query to check if any user is on a group.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, group_id: uuid.UUID) -> bool:
        """
        Method to check if user on group.

        :param group_id: the group identifier.
        """

        stmt = (
            sa.select(models.UserGroup.user_id)
            .where(models.UserGroup.group_id == group_id)
            .limit(1)
        )

        async with self._session_factory() as session:
            result = await session.scalars(stmt)

        if not result.first():
            return False
        return True
