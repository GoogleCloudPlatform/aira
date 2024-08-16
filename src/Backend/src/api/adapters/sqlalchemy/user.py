"""
Module for all user related sqlalchemy queries.
"""

import json
import logging
import uuid

import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import exc, func, orm
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, helpers, models, ports, typings

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
        reset_token: str | None = None,
    ) -> models.User:
        """
        Get user by params.

        :param user_id: user id on database.
        :param external_id: user id provided by firebase.
        :param email: user's email.
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
        if reset_token:
            stmt = stmt.where(models.User.reset_token == reset_token)

        result = await self._session.execute(stmt)
        if not (user := result.unique().scalar_one_or_none()):
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

    async def create_or_update_student(
        self,
        student: typings.CreateOrUpdateUser,
        group_customer_id: str,
        updated_groups: dict[str, models.Group],
        cached_users: list[models.User],
    ) -> models.User | None:
        group = updated_groups.get(group_customer_id)
        if not group:
            group_stmt = sa.select(models.Group).where(
                models.Group.customer_id == group_customer_id
            )
            group_result = await self._session.execute(group_stmt)
            group = group_result.unique().scalar_one_or_none()
            if not group:
                return None
        user = next(
            (u for u in cached_users if u.customer_id == student.customer_id), None
        )

        if user:
            user.name = student.name
            user.type = student.type
            user.role_id = student.role_id
            user.groups = [group]
            user.organizations = [group.organization]
        else:
            user = models.User(
                external_id=None,
                name=student.name,
                email_address=student.email_address,
                customer_id=student.customer_id,
                type=student.type,
                role_id=student.role_id,
                groups=[group],
                organizations=[group.organization],
                county=student.county,
                region=student.region,
                state=student.state,
            )
            self._session.add(user)
        return user

    async def create_or_update_professor(
        self,
        professor: typings.CreateOrUpdateUser,
        groups_customer_id: list[str],
        organizations_customer_id: list[str],
        updated_organizations: dict[str, models.Organization],
        updated_groups: dict[str, models.Group],
        cached_profs: list[models.User],
    ) -> models.User | None:
        groups: list[models.Group] = []
        for group_customer_id in groups_customer_id:
            group = updated_groups.get(group_customer_id)
            if not group:
                group_stmt = sa.select(models.Group).where(
                    models.Group.customer_id == group_customer_id
                )
                group_result = await self._session.execute(group_stmt)
                group = group_result.unique().scalar_one_or_none()
                if group and group.customer_id:
                    updated_groups[group.customer_id] = group
            if group:
                groups.append(group)
        if not groups:
            return None

        organizations: list[models.Organization] = []
        for organization_customer_id in organizations_customer_id:
            organization = updated_organizations.get(organization_customer_id)
            if not organization:
                organization_stmt = sa.select(models.Organization).where(
                    models.Organization.customer_id == organization_customer_id
                )
                organization_result = await self._session.execute(organization_stmt)
                organization = organization_result.unique().scalar_one_or_none()
                if organization and organization.customer_id:
                    updated_organizations[organization.customer_id] = organization
            if organization:
                organizations.append(organization)
        if not organizations:
            return None
        user = next(
            (u for u in cached_profs if u.customer_id == professor.customer_id), None
        )
        if user:
            user.name = professor.name
            user.type = models.UserType.PASSWORD
            user.role_id = professor.role_id
            user.groups = [
                g for g in user.groups if g.customer_id in groups_customer_id
            ]
            user.groups = [
                *user.groups,
                *[
                    g
                    for g in groups
                    if not any(user_group.id == g.id for user_group in user.groups)
                ],
            ]
            user.organizations = [
                o
                for o in user.organizations
                if o.customer_id in organizations_customer_id
            ]
            user.organizations = [
                *user.organizations,
                *[
                    o
                    for o in organizations
                    if not any(user_org.id == o.id for user_org in user.organizations)
                ],
            ]
        else:
            user = models.User(
                external_id=None,
                name=professor.name,
                email_address=professor.email_address,
                customer_id=professor.customer_id,
                type=models.UserType.PASSWORD,
                role_id=professor.role_id,
                groups=groups,
                organizations=organizations,
                county=professor.county,
                region=professor.region,
                state=professor.state,
            )
            self._session.add(user)
        return user

    async def list(
        self,
        user_ids: list[uuid.UUID] | None = None,
        customer_ids: list[str] | None = None,
    ) -> list[models.User]:
        """
        Method to facilitate user import and list users based on an id list.
        It must have either customer or user_ids

        :param user_ids: array with user ids.
        :param customer_ids: array with customer's user ids.
        """
        if not (user_ids or customer_ids):
            return []
        stmt = (
            sa.select(models.User)
            .options(
                orm.joinedload(models.User.groups),
            )
            .options(
                orm.joinedload(models.User.organizations),
            )
        )
        if user_ids:
            stmt = stmt.where(models.User.id.in_(user_ids))
        if customer_ids:
            stmt = stmt.where(models.User.customer_id.in_(customer_ids))
        result = await self._session.execute(stmt)
        users = list(result.scalars().unique())
        return users


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

        async with self._session_factory() as session:
            if page_size > 0:
                params = Params(page=page, size=page_size)
                result: typings.Paginated = await paginate(
                    session, stmt, params=params, unique=True
                )
                return result.items, typings.PaginationMetadata(
                    current_page=result.page,
                    total_pages=result.pages,
                    total_items=result.total,
                    page_size=result.size,
                )
            result_all = await session.execute(stmt)
            user_results = list(result_all.scalars().unique())
            return user_results, typings.PaginationMetadata(
                current_page=1,
                total_pages=1,
                total_items=len(user_results),
                page_size=len(user_results),
            )


class ListUsersWithExams(ports.ListUsersWithExams):
    """
    Query to get all users with exams.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        groups: list[uuid.UUID],
        organizations: list[uuid.UUID],
        role_ids: list[uuid.UUID] | None = None,
        query: str | None = None,
        show_finished: bool = True,
        page_size: int = 10,
        page: int = 1,
    ) -> tuple[list[dict], typings.PaginationMetadata]:  # type:ignore[type-arg]
        user = models.User
        org = models.Organization
        group = models.Group
        exam = models.Exam
        exam_user = models.ExamUser
        current_date = helpers.time_now()
        stmt = (
            sa.select(
                user,
                sa.cast(
                    sa.func.json_agg(
                        sa.func.json_build_object(
                            "id",
                            exam.id,
                            "name",
                            exam.name,
                            "start_date",
                            exam.start_date,
                            "end_date",
                            exam.end_date,
                            "status",
                            exam_user.status,
                        )
                    ),
                    type_=sa.String,
                ).label("exams"),
            )
            .join(models.UserGroup, models.UserGroup.user_id == user.id)
            .join(
                group,
                sa.and_(group.id.in_(groups), group.id == models.UserGroup.group_id),
            )
            .join(models.UserOrganization, models.UserOrganization.user_id == user.id)
            .join(
                org,
                sa.and_(
                    org.id.in_(organizations),
                    org.id == models.UserOrganization.organization_id,
                ),
            )
        )
        stmt = stmt.where(user.role_id.in_(role_ids)) if role_ids else stmt

        if not show_finished:
            stmt = (
                stmt.join(
                    exam,
                    sa.and_(
                        group.grade == exam.grade,
                        exam.start_date <= current_date,
                        exam.end_date > current_date,
                    ),
                )
                .outerjoin(
                    exam_user,
                    sa.and_(exam_user.user_id == user.id, exam.id == exam_user.exam_id),
                )
                .where(
                    sa.or_(
                        exam_user.status != models.ExamStatus.FINISHED,
                        exam_user.exam_id.is_(None),
                    )
                )
            )
        else:
            stmt = stmt.outerjoin(
                exam,
                sa.and_(
                    group.grade == exam.grade,
                    exam.start_date <= current_date,
                ),
            ).outerjoin(
                exam_user,
                sa.and_(exam_user.user_id == user.id, exam.id == exam_user.exam_id),
            )

        if query:
            stmt = stmt.where(
                sa.or_(
                    user.name.ilike(f"%{query}%"),
                    user.email_address.ilike(f"%{query}%"),
                )
            )

        stmt = stmt.group_by(user.id)

        async with self._session_factory() as session:
            if page_size >= 0:
                params = Params(page=page, size=page_size)
                result: typings.Paginated = await paginate(session, stmt, params=params)
                result_items = result.items
                current_page = result.page
                total_pages = result.pages
                total_items = result.total
                page_size = result.size
            else:
                result_all = await session.execute(stmt)
                result_items = list(result_all.unique().all())
                current_page = 1
                total_pages = 1
                total_items = len(result_items)
                page_size = len(result_items)

        items_result = []
        for item in result_items:
            user_dict = {
                col.name: getattr(item.User, col.name)
                for col in item.User.__table__.columns
            }
            exams_dict_list = json.loads(item.exams)
            items_result.append(
                {
                    **user_dict,
                    "exams": [ex for ex in exams_dict_list if ex["id"] is not None],
                }
            )
        return items_result, typings.PaginationMetadata(
            current_page=current_page,
            total_pages=total_pages,
            total_items=total_items,
            page_size=page_size,
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


class ListPersonifiableUsers(ports.ListPersonifiableUsers):
    """
    List users that a user can impersonate.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, groups: list[uuid.UUID]) -> list[models.User]:
        """
        Method to list all users.
        """
        stmt = (
            sa.select(models.User)
            .join(models.UserGroup)
            .filter(models.UserGroup.group_id.in_(groups))
            .options(
                orm.joinedload(models.User.groups),
            )
            .options(
                orm.joinedload(models.User.organizations),
            )
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)
        return list(result.scalars().unique())
