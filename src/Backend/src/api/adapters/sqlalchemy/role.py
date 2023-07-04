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
Module for all role related sqlalchemy queries.
"""
import uuid

import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import exc
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, models, ports, typings


class RoleRepository(ports.RoleRepository):
    """
    Role repository implementation that returns role data.
    """

    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(
        self, role_id: uuid.UUID | None = None, name: str | None = None
    ) -> models.Role:
        """
        Get role by params.

        :params role_id: role id on database.
        :params name: name on database.
        """
        if not (role_id or name):
            raise errors.NotFound()
        stmt = sa.select(models.Role)
        if role_id:
            stmt = stmt.where(models.Role.id == role_id)
        if name:
            stmt = stmt.where(models.Role.name == name)
        result = await self._session.execute(stmt)
        if not (role := result.scalars().one_or_none()):
            raise errors.NotFound("role")
        return role

    async def create(self, role_model: models.Role) -> models.Role:
        """
        Method to create a role.

        :param role_model: the role model parameter.

        :returns: role model.

        :raises errors.AlreadyExists: if the entity is duplicated.
        """
        self._session.add(role_model)

        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception

        return role_model

    async def delete(self, role_model: models.Role) -> None:
        """
        Method to delete a role.

        :param role_model: the role model parameter.
        """
        await self._session.delete(role_model)


class GetRoleByName(ports.GetRoleByName):
    """
    Get role by its name.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, name: str) -> models.Role:
        """
        Method to get a specific role.

        :param role_name: the role name.
        """
        stmt = sa.select(models.Role).where(models.Role.name == name)
        async with self._session_factory() as session:
            result = await session.execute(stmt)

        if not (role := result.scalars().one_or_none()):
            raise errors.NotFound("role")

        return role


class ListRoles(ports.ListRoles):
    """
    Query to get all roles.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        page_size: int = 10,
        page: int = 1,
    ) -> tuple[list[models.Role], typings.PaginationMetadata]:
        """
        Method to list all roles.
        """
        stmt = sa.select(models.Role)

        params = Params(page=page, size=page_size)
        async with self._session_factory() as session:
            result: typings.Paginated = await paginate(session, stmt, params=params)
        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )


class GetRole(ports.GetRole):
    """
    Query to get a specific role.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, role_id: uuid.UUID) -> models.Role:
        """
        Method to get a specific role.

        :param role_id: the role identifier.
        """
        stmt = sa.select(models.Role).where(models.Role.id == role_id)
        async with self._session_factory() as session:
            result = await session.execute(stmt)

        if not (role := result.scalars().one_or_none()):
            raise errors.NotFound("role")
        return role
