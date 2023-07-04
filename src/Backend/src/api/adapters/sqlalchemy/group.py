"""
Module for all user related sqlalchemy queries.
"""

import logging
import uuid

import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import exc, orm
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, models, ports, typings

logger = logging.getLogger(__name__)


class GroupRepository(ports.GroupRepository):
    """
    Group repository implementation that returns group data.
    """

    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, group_id: uuid.UUID) -> models.Group:
        """
        Get group by params.

        :params group_id: group id on database.
        """
        stmt = (
            sa.select(models.Group)
            .options(
                orm.joinedload(models.Group.organization),
            )
            .where(models.Group.id == group_id)
        )

        result = await self._session.execute(stmt)
        if not (group := result.scalars().one_or_none()):
            raise errors.NotFound("group")
        return group

    async def create(self, group_model: models.Group) -> models.Group:
        """
        Method to create a group.

        :param group_model: the group model parameter.

        :returns: group model.

        :raises errors.AlreadyExists: if the entity is duplicated.
        """
        self._session.add(group_model)

        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception

        await self._session.refresh(group_model, ["organization"])
        return group_model

    async def delete(self, group_model: models.Group) -> None:
        """
        Method to delete a group.

        :param group_model: the group model parameter.
        """
        await self._session.delete(group_model)


class ListGroups(ports.ListGroups):
    """
    Query to get all groups.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        groups: list[uuid.UUID] | None = None,
        shift: str | None = None,
        grade: models.Grades | None = None,
        organizations: list[uuid.UUID] | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.Group], typings.PaginationMetadata]:
        """
        Method to list all groups.
        """
        group = models.Group

        stmt = sa.select(group).options(
            orm.joinedload(group.organization),
        )

        if groups is not None:
            stmt = stmt.where(group.id.in_(groups))

        if shift:
            stmt = stmt.where(group.shift == shift)

        if grade:
            stmt = stmt.where(group.grade == grade)

        if organizations:
            stmt = stmt.where(group.organization_id.in_(organizations))

        if query:
            stmt = stmt.join(models.Organization).where(
                sa.or_(
                    group.name.ilike(f"%{query}%"),
                    models.Organization.name.ilike(f"%{query}%"),
                )
            )

        async with self._session_factory() as session:
            if page_size >= 0:
                params = Params(page=page, size=page_size)
                result: typings.Paginated = await paginate(
                    session, stmt, params=params, unique=True
                )
            else:
                result_all = await session.execute(stmt)
                groups_result = list(result_all.scalars().unique())
                return groups_result, typings.PaginationMetadata(
                    current_page=1,
                    total_pages=1,
                    total_items=len(groups_result),
                    page_size=len(groups_result),
                )

        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )


class GetGroup(ports.GetGroup):
    """
    Query to get a specific group.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, group_id: uuid.UUID) -> models.Group:
        """
        Method to get a specific group.

        :param group_id: the group identifier.
        """

        stmt = (
            sa.select(models.Group)
            .options(
                orm.joinedload(models.Group.organization),
            )
            .where(models.Group.id == group_id)
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)

        if not (group := result.scalars().one_or_none()):
            raise errors.NotFound("group")

        return group


class ListGroupsWithoutOrg(ports.ListGroupsWithoutOrg):
    """
    Query to get all groups.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        groups: list[uuid.UUID] | None = None,
        shift: str | None = None,
        grade: str | None = None,
    ) -> list[models.Group]:
        """
        Method to list all groups.
        """

        stmt = sa.select(models.Group)

        if groups is not None:
            stmt = stmt.where(models.Group.id.in_(groups))

        if shift:
            stmt = stmt.where(models.Group.shift == shift)

        if grade:
            stmt = stmt.where(models.Group.grade == grade)

        async with self._session_factory() as session:
            result = await session.execute(stmt)

        group_result = list(result.scalars().unique())

        return group_result


class CheckGroupOnOrg(ports.CheckGroupOnOrg):
    """
    Query to check if any group is on an org.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, organization_id: uuid.UUID) -> bool:
        """
        Method to check if group is on any org.

        :param organization_id: the org identifier.
        """

        stmt = (
            sa.select(models.Group.id)
            .where(models.Group.organization_id == organization_id)
            .limit(1)
        )

        async with self._session_factory() as session:
            result = await session.scalars(stmt)

        if not result.first():
            return False
        return True
