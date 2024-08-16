"""
Configurations for tests.
"""

from __future__ import annotations

import contextlib
import datetime
import typing
import uuid

import api
import injector
import sqlalchemy as sa
from api import dependencies, models, ports, typings
from api.helpers import time_now
from httpx import AsyncClient
from passlib import context
from sqlalchemy import event, orm
from sqlalchemy.ext import asyncio as sqlalchemy_aio

_container: injector.Injector | None = None


def create_test_container() -> injector.Injector:
    """
    Creating test container.
    """
    # ruff: noqa: PLW0603
    global _container
    if _container:
        return _container
    modules = (
        dependencies.SettingsModule(),
        dependencies.EngineTestSQLAlchemy(),
        dependencies.SQLAlchemyModule(),
        dependencies.MemoryModule(),
        dependencies.TracingModule(),
    )
    _container = injector.Injector(modules)
    return _container


@contextlib.asynccontextmanager
async def uow_builder_ctx() -> typing.AsyncGenerator[ports.UnitOfWorkBuilder, None]:
    """
    Generate session builder.
    """
    container = create_test_container()
    uow_builder = container.get(ports.UnitOfWorkBuilder)
    yield uow_builder


@contextlib.asynccontextmanager
async def uow_ctx() -> typing.AsyncGenerator[ports.UnitOfWork, None]:
    """
    Generate session.
    """
    container = create_test_container()
    uow_builder = container.get(ports.UnitOfWorkBuilder)
    async with uow_builder() as uow:
        yield uow
    assert uow.closed


@contextlib.asynccontextmanager
async def session_factory_ctx() -> typing.AsyncGenerator[typings.SessionFactory, None]:
    """
    Generate session.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    yield session_factory


@contextlib.asynccontextmanager
async def clear_between_tests() -> typing.AsyncGenerator[None, None]:
    """
    Clear database between tests.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    dirty_tables: set[str] = set()

    # pylint: disable=unused-argument
    def assign_dirty_table(
        session: sqlalchemy_aio.AsyncSession, *args: typing.Any, **kwargs: typing.Any
    ) -> None:
        dirty_tables.update(obj.__tablename__ for obj in session.dirty | session.new)

    def assign_dirty_orm(orm_execute_state: orm.ORMExecuteState) -> None:
        statement = orm_execute_state.statement
        table: sa.TableClause | sa.Alias | sa.Join

        if orm_execute_state.is_insert:
            table = typing.cast(sa.Insert, statement).table
        elif orm_execute_state.is_update:
            table = typing.cast(sa.Update, statement).table
        elif orm_execute_state.is_delete:
            table = typing.cast(sa.Delete, statement).table
        else:
            return

        table_name = str(table)
        dirty_tables.add(table_name)

    event.listen(orm.Session, "before_commit", assign_dirty_table)
    event.listen(orm.Session, "do_orm_execute", assign_dirty_orm)
    try:
        yield
    finally:
        event.remove(orm.Session, "before_commit", assign_dirty_table)
        event.remove(orm.Session, "do_orm_execute", assign_dirty_orm)
        async with session_factory() as session:
            for table in dirty_tables:
                await session.execute(sa.text(f"TRUNCATE {table} CASCADE"))
            await session.commit()


@contextlib.asynccontextmanager
async def organization() -> typing.AsyncGenerator[models.Organization, None]:
    """
    Generate session.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    org_id = uuid.uuid4()
    stmt = sa.insert(models.Organization).values(
        id=org_id,
        name="Test Org",
        city="Niterói",
        state="RJ",
        county="Rio de Janeiro",
        created_at=time_now(),
        updated_at=time_now(),
    )
    select_stmt = sa.select(models.Organization).where(models.Organization.id == org_id)
    async with session_factory() as session:
        await session.execute(stmt)
        await session.commit()

        result = await session.execute(select_stmt)
        org = result.scalar_one_or_none()
    try:
        if not org:
            raise RuntimeError("Should've created an organization")
        yield org
    finally:
        async with session_factory() as session:
            await session.delete(org)
            await session.commit()


@contextlib.asynccontextmanager
async def exam() -> typing.AsyncGenerator[models.Exam, None]:
    """
    Generate exam.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    exam_id = uuid.uuid4()
    stmt = sa.insert(models.Exam).values(
        id=exam_id,
        name="Test Exam",
        start_date=time_now(),
        end_date=time_now() + datetime.timedelta(hours=1),
        grade=models.Grades.FIRST_FUND,
        created_at=time_now(),
        updated_at=time_now(),
    )
    select_stmt = sa.select(models.Exam).where(models.Exam.id == exam_id)
    async with session_factory() as session:
        await session.execute(stmt)
        await session.commit()

        result = await session.execute(select_stmt)
        exam_model = result.unique().scalar_one_or_none()
    try:
        if not exam_model:
            raise RuntimeError("Should've created an exam")
        yield exam_model
    finally:
        async with session_factory() as session:
            await session.delete(exam_model)
            await session.commit()


@contextlib.asynccontextmanager
async def question(
    exam_model: models.Exam,
) -> typing.AsyncGenerator[models.Question, None]:
    """
    Generate question.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    question_id = uuid.uuid4()
    stmt = sa.insert(models.Question).values(
        id=question_id,
        name="Teste Question",
        type=models.QuestionType.WORDS,
        phrase_id="",
        data="",
        formatted_data="",
        exam_id=exam_model.id,
        created_at=time_now(),
        updated_at=time_now(),
        order=1,
    )
    select_stmt = sa.select(models.Question).where(models.Question.id == question_id)
    async with session_factory() as session:
        await session.execute(stmt)
        await session.commit()

        result = await session.execute(select_stmt)
        question_model = result.unique().scalar_one_or_none()
    try:
        if not question_model:
            raise RuntimeError("Should've created a question")
        yield question_model
    finally:
        async with session_factory() as session:
            await session.delete(question_model)
            await session.commit()


@contextlib.asynccontextmanager
async def exam_user_status(
    exam_model: models.Exam,
    user_model: models.User,
) -> typing.AsyncGenerator[models.ExamUser, None]:
    """
    Generate question.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    stmt = sa.insert(models.ExamUser).values(
        exam_id=exam_model.id,
        user_id=user_model.id,
        status=models.ExamStatus.NOT_STARTED,
        created_at=time_now(),
        updated_at=time_now(),
    )
    select_stmt = (
        sa.select(models.ExamUser)
        .where(models.ExamUser.exam_id == exam_model.id)
        .where(models.ExamUser.user_id == user_model.id)
    )
    async with session_factory() as session:
        await session.execute(stmt)
        await session.commit()

        result = await session.execute(select_stmt)
        exam_user_model = result.unique().scalar_one_or_none()
    try:
        if not exam_user_model:
            raise RuntimeError("Should've created a exams_users")
        yield exam_user_model
    finally:
        async with session_factory() as session:
            await session.delete(exam_user_model)
            await session.commit()


@contextlib.asynccontextmanager
async def group(org: models.Organization) -> typing.AsyncGenerator[models.Group, None]:
    """
    Generate session.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    group_id = uuid.uuid4()
    stmt = sa.insert(models.Group).values(
        id=group_id,
        name="Test Group",
        shift="morning",
        grade=models.Grades.FIRST_FUND,
        organization_id=org.id,
        created_at=time_now(),
        updated_at=time_now(),
    )
    select_stmt = (
        sa.select(models.Group)
        .options(
            orm.joinedload(models.Group.organization),
        )
        .where(models.Group.id == group_id)
    )
    async with session_factory() as session:
        await session.execute(stmt)
        await session.commit()

        result = await session.execute(select_stmt)
        group_model = result.scalar_one_or_none()
    try:
        if not group_model:
            raise RuntimeError("Should've created a group")
        yield group_model
    finally:
        async with session_factory() as session:
            await session.delete(group_model)
            await session.commit()


@contextlib.asynccontextmanager
async def role(scope: str = "test") -> typing.AsyncGenerator[models.Role, None]:
    """
    Generate session.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    role_id = uuid.uuid4()
    stmt = sa.insert(models.Role).values(
        id=role_id,
        name="test role",
        display_name={},
        description={},
        scopes=[scope],
        created_at=time_now(),
        updated_at=time_now(),
    )
    select_stmt = sa.select(models.Role).where(models.Role.id == role_id)
    async with session_factory() as session:
        await session.execute(stmt)
        await session.commit()

        result = await session.execute(select_stmt)
        role_model = result.scalar_one_or_none()
    try:
        if not role_model:
            raise RuntimeError("Should've created a role")
        yield role_model
    finally:
        async with session_factory() as session:
            await session.delete(role_model)
            await session.commit()


@contextlib.asynccontextmanager
async def user(
    role_model: models.Role, group_model: models.Group | None = None
) -> typing.AsyncGenerator[models.User, None]:
    """
    Generate session.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    user_id = uuid.uuid4()
    stmt = sa.insert(models.User).values(
        id=user_id,
        external_id=str(uuid.uuid4()),
        role_id=role_model.id,
        type=models.UserType.FIREBASE,
        name="test-user",
        email_address="test@example.com",
        created_at=time_now(),
        updated_at=time_now(),
    )
    select_stmt = sa.select(models.User).where(models.User.id == user_id)
    async with session_factory() as session:
        await session.execute(stmt)
        if group_model:
            stmt_group = sa.insert(models.UserGroup).values(
                user_id=user_id,
                group_id=group_model.id,
                created_at=time_now(),
                updated_at=time_now(),
            )
            await session.execute(stmt_group)
        await session.commit()

        result = await session.execute(select_stmt)
        user_model = result.unique().scalar_one_or_none()
    try:
        if not user_model:
            raise RuntimeError("Should've created an User")
        yield user_model
    finally:
        async with session_factory() as session:
            await session.delete(user_model)
            await session.commit()


@contextlib.asynccontextmanager
async def user_with_password(
    role_model: models.Role,
) -> typing.AsyncGenerator[models.User, None]:
    """
    Generate session.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    hash_ctx = container.get(context.CryptContext)
    user_id = uuid.uuid4()
    stmt = sa.insert(models.User).values(
        id=user_id,
        role_id=role_model.id,
        type=models.UserType.PASSWORD,
        name="test-user",
        email_address="test@example.com",
        _password=hash_ctx.hash("test"),
        created_at=time_now(),
        updated_at=time_now(),
    )
    select_stmt = sa.select(models.User).where(models.User.id == user_id)
    async with session_factory() as session:
        await session.execute(stmt)
        await session.commit()

        result = await session.execute(select_stmt)
        user_model = result.unique().scalar_one_or_none()
    try:
        if not user_model:
            raise RuntimeError("Should've created an User")
        yield user_model
    finally:
        async with session_factory() as session:
            await session.delete(user_model)
            await session.commit()


@contextlib.asynccontextmanager
async def session_model(
    user_model: models.User,
) -> typing.AsyncGenerator[models.Session, None]:
    """
    Generate session.
    """
    container = create_test_container()
    session_factory = container.get(typings.SessionFactory)
    session_id = uuid.uuid4()
    stmt = sa.insert(models.Session).values(
        id=session_id,
        user_id=user_model.id,
        expires_at=time_now() + datetime.timedelta(hours=1),
    )
    select_stmt = sa.select(models.Session).where(models.Session.id == session_id)
    async with session_factory() as session:
        await session.execute(stmt)
        await session.commit()

        result = await session.execute(select_stmt)
        sess = result.unique().scalar_one_or_none()
    try:
        if not sess:
            raise RuntimeError("Should've created a session")
        yield sess
    finally:
        async with session_factory() as session:
            await session.delete(sess)
            await session.commit()


@contextlib.asynccontextmanager
async def test_client() -> typing.AsyncGenerator[AsyncClient, None]:
    """
    Test client.
    """
    app = api.create_app(create_test_container())
    base_url = "http://api.stt.com"
    async with AsyncClient(app=app, base_url=base_url) as client:
        yield client
