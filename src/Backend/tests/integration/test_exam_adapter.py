"""
Module for testing the exam repository.
"""

import contextlib
import datetime
import math

import hypothesis
import pytest
from api import errors, models, typings
from api.adapters.sqlalchemy import exam
from api.helpers import time_now
from api.routers.exams import schemas
from hypothesis import strategies as st

from tests.helpers import database, strats


def _create_exam_model_from_schema(
    schema_list: list[schemas.ExamCreate],
) -> list[models.Exam]:
    return [
        models.Exam(
            name=schema.name,
            end_date=time_now() + datetime.timedelta(days=30),
            start_date=time_now(),
            grade=models.Grades.FIRST_FUND,
            questions=[
                models.Question(**question.dict(), phrase_id="")
                for question in schema.questions
            ],
        )
        for schema in schema_list
    ]


@pytest.mark.asyncio
@pytest.mark.database
async def test_get_exam_model_query() -> None:
    """
    Test of adapter to get an exam_model from query.
    """
    async with contextlib.AsyncExitStack() as stack:
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        await stack.enter_async_context(database.clear_between_tests())
        exam_model = await stack.enter_async_context(database.exam())
        get_exam_model = exam.GetExam(session_factory)
        response = await get_exam_model(exam_model.id)
        assert response == exam_model


@pytest.mark.asyncio
@pytest.mark.database
@hypothesis.given(
    exam_schema=st.builds(
        schemas.ExamCreate,
        name=strats.safe_text(max_size=50),
        start_date=st.just(time_now()),
        end_date=st.just(time_now() + datetime.timedelta(days=30)),
        questions=st.lists(
            st.builds(
                schemas.Question,
                name=strats.safe_text(max_size=50),
                formatted_data=strats.safe_text(),
                data=strats.safe_text(),
                type=st.sampled_from(models.QuestionType),
                order=st.integers(min_value=0, max_value=20),
            ),
        ),
        grade=st.sampled_from(models.Grades),
    ),
    page_size=st.one_of(st.just(10), st.integers(min_value=1, max_value=5)),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
)
async def test_list_exam_models_query(
    exam_schema: schemas.ExamCreate,
    page_size: int,
) -> None:
    """
    Test of adapter to list exam_models.
    """
    async with contextlib.AsyncExitStack() as stack:
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        await stack.enter_async_context(database.clear_between_tests())
        list_exam_models = exam.ListExams(session_factory)
        async with session_factory() as session:
            exam_model_schemas = [exam_schema] * 10
            schema_models = _create_exam_model_from_schema(exam_model_schemas)
            session.add_all(schema_models)
            await session.commit()

        expected = sorted(schema_models, key=lambda x: x.start_date, reverse=True)
        expected_metadata = typings.PaginationMetadata(
            current_page=1,
            total_pages=math.ceil(len(expected) / page_size),
            total_items=len(expected),
            page_size=page_size,
        )
        expected_paginated = expected[:page_size]

        items, params = await list_exam_models(page_size=page_size)
        assert len(items) == len(expected_paginated)
        assert items == expected_paginated
        assert params == expected_metadata


@pytest.mark.asyncio
@pytest.mark.database
async def test_get_exam_model_repo_query() -> None:
    """
    Test of adapter to get exam_model.
    """
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        fake_exam_model = await stack.enter_async_context(database.exam())
        exam_model = await uow.exam_repository.get(fake_exam_model.id)

        assert exam_model == fake_exam_model, exam_model


@pytest.mark.asyncio
@pytest.mark.database
@hypothesis.given(
    exam_model_schema=st.builds(
        schemas.ExamCreate,
        name=strats.safe_text(max_size=50),
        start_date=st.just(time_now()),
        end_date=st.just(time_now() + datetime.timedelta(days=30)),
        questions=st.lists(
            st.builds(
                schemas.Question,
                name=strats.safe_text(max_size=50),
                formatted_data=strats.safe_text(),
                data=strats.safe_text(),
                order=st.integers(min_value=0, max_value=20),
            )
        ),
        grade=st.sampled_from(models.Grades),
    )
)
async def test_create_exam_model(exam_model_schema: schemas.ExamCreate) -> None:
    """
    Test of adapter to create exam_model.
    """
    exam_model_model = _create_exam_model_from_schema([exam_model_schema])[0]
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        expected = await uow.exam_repository.create(exam_model_model)
        exam_model = await uow.exam_repository.get(expected.id)
        assert expected == exam_model


@pytest.mark.asyncio
@pytest.mark.database
async def test_should_raise_already_exists() -> None:
    """
    Test of adapter to create exam_model.
    """
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        exam_model = await stack.enter_async_context(database.exam())
        new_exam_model_same_data = _create_exam_model_from_schema(
            [schemas.ExamCreate.from_orm(exam_model)]
        )[0]
        new_exam_model_same_data.id = exam_model.id
        with pytest.raises(errors.AlreadyExists):
            await uow.exam_repository.create(new_exam_model_same_data)


@pytest.mark.asyncio
@pytest.mark.database
async def test_list_pending_exams() -> None:
    """
    Test of adapter to list pending exams.
    """
    async with contextlib.AsyncExitStack() as stack:
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        user_role = await stack.enter_async_context(database.role("user"))
        org = await stack.enter_async_context(database.organization())
        group_model = await stack.enter_async_context(database.group(org))
        user_model = await stack.enter_async_context(
            database.user(role_model=user_role, group_model=group_model)
        )
        exam_model = await stack.enter_async_context(database.exam())
        list_pending = exam.ListPendingExams(session_factory)

        pending_result, _ = await list_pending(
            user_id=user_model.id, group_id=user_model.groups[0].id
        )
        assert pending_result == [(exam_model, None)]


@pytest.mark.asyncio
@pytest.mark.database
async def test_list_pending_questions() -> None:
    """
    Test of adapter to list pending questions.
    """
    async with contextlib.AsyncExitStack() as stack:
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        user_role = await stack.enter_async_context(database.role("user"))
        org = await stack.enter_async_context(database.organization())
        group = await stack.enter_async_context(database.group(org))
        user = await stack.enter_async_context(
            database.user(role_model=user_role, group_model=group)
        )
        exam_model = await stack.enter_async_context(database.exam())
        question_model = await stack.enter_async_context(database.question(exam_model))
        list_pending = exam.ListPendingQuestions(session_factory)

        pending_result = await list_pending(
            user_id=user.id, group_id=user.groups[0].id, exam_id=exam_model.id
        )
        assert pending_result == [question_model]


@pytest.mark.asyncio
@pytest.mark.database
async def test_get_pending_question() -> None:
    """
    Test of adapter to get pending questions.
    """
    async with contextlib.AsyncExitStack() as stack:
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        user_role = await stack.enter_async_context(database.role("user"))
        org = await stack.enter_async_context(database.organization())
        group = await stack.enter_async_context(database.group(org))
        user = await stack.enter_async_context(
            database.user(role_model=user_role, group_model=group)
        )
        exam_model = await stack.enter_async_context(database.exam())
        question_model = await stack.enter_async_context(database.question(exam_model))
        get_pending = exam.GetPendingQuestion(session_factory)

        pending_result = await get_pending(
            user_id=user.id,
            group_id=user.groups[0].id,
            exam_id=exam_model.id,
            question_id=question_model.id,
        )
        assert pending_result == question_model


@pytest.mark.asyncio
@pytest.mark.database
async def test_question_repo_get() -> None:
    """
    Test of adapter to get pending questions.
    """
    async with contextlib.AsyncExitStack() as stack:
        uow = await stack.enter_async_context(database.uow_ctx())
        exam_model = await stack.enter_async_context(database.exam())
        fake_question_model = await stack.enter_async_context(
            database.question(exam_model)
        )
        question_model = await uow.question_repository.get(fake_question_model.id)

        assert question_model == fake_question_model, question_model


@pytest.mark.asyncio
@pytest.mark.database
async def test_get_question_result() -> None:
    """
    Test of adapter to get exams_users.
    """
    async with contextlib.AsyncExitStack() as stack:
        session_factory = await stack.enter_async_context(
            database.session_factory_ctx()
        )
        user_role = await stack.enter_async_context(database.role("user"))
        org = await stack.enter_async_context(database.organization())
        group = await stack.enter_async_context(database.group(org))
        user_model = await stack.enter_async_context(
            database.user(role_model=user_role, group_model=group)
        )
        exam_model = await stack.enter_async_context(database.exam())
        exam_user_model = await stack.enter_async_context(
            database.exam_user_status(exam_model=exam_model, user_model=user_model)
        )
        get_result = exam.GetExamUserStatus(session_factory)
        result = await get_result(
            user_id=user_model.id, exam_id=exam_model.id, group_id=group.id
        )
        assert result == exam_user_model
