"""
Unit tests for `exams/endpoints.py`
"""
import datetime
import unittest.mock
import uuid

import hypothesis
import pytest
from hypothesis import strategies as st

from api import errors, models
from api.adapters.memory import exam, unit_of_work
from api.helpers import schemas as util_schemas
from api.helpers import time_now
from api.routers.exams import endpoints as exams_endpoint
from api.routers.exams import schemas


@pytest.mark.asyncio
@hypothesis.given(
    page_size=st.integers(min_value=1, max_value=10),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
    max_examples=8,
)
async def test_list_exams(
    page_size: int,
) -> None:
    """
    tests if auth endpoint calls correctly.
    """
    exams: list[models.Exam] = []
    session_manager = unittest.mock.AsyncMock()
    for i in range(page_size + 1):
        tmp_exam = models.Exam(
            name=f"test-{i}",
            start_date=time_now(),
            end_date=time_now() + datetime.timedelta(days=20),
            grade=models.Grades.FIRST_FUND,
            questions=[],
        )
        tmp_exam.created_at = tmp_exam.updated_at = time_now()
        exams.append(tmp_exam)
    list_exams = exam.ListExams(exams)
    response = await exams_endpoint.list_resources(
        list_data=util_schemas.ListSchema(page_size=page_size, page=1),
        session_manager=session_manager,
        list_exams=list_exams,
        list_pending=exam.ListPendingExams([]),
    )
    tmp_response = [schemas.Exam.from_orm(exam) for exam in exams]
    final_response = tmp_response[:page_size]

    assert len(response.items) == min(page_size, len(final_response))
    assert response.items == final_response
    assert list_exams.called == 1


@pytest.mark.asyncio
async def test_get_exam(
    fake_exam: models.Exam,
    fake_session: models.Session,
) -> None:
    """
    tests if get is behaving properly.
    """
    get_exam = exam.GetExam([fake_exam])
    session_manager = unittest.mock.AsyncMock()
    session_manager.get_current_session.return_value = fake_session

    response = await exams_endpoint.get(
        get_exam=get_exam,
        session_manager=session_manager,
        exam_id=fake_exam.id,
    )
    expected = schemas.ExamGet.from_orm(fake_exam)
    assert response == expected

    # Testing now exam not found

    with pytest.raises(errors.NotFound):
        await exams_endpoint.get(
            get_exam=get_exam,
            session_manager=session_manager,
            exam_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
@hypothesis.given(
    create_exam=st.builds(
        schemas.ExamCreate,
        start_date=st.just(time_now()),
        end_date=st.just(time_now() + datetime.timedelta(days=30)),
    )
)
async def test_create_exam(
    create_exam: schemas.ExamCreate,
) -> None:
    """
    tests if get is behaving properly.
    """
    exam_repo = exam.ExamRepository()
    speech = unittest.mock.AsyncMock()
    speech.create_phrase_set.return_value = "id"
    uow_builder = unit_of_work.UnitOfWorkBuilder(exam_repository=exam_repo)
    response = await exams_endpoint.create(
        uow_builder=uow_builder, speech=speech, body=create_exam
    )
    assert uow_builder.call_count == 1
    assert await exam_repo.get(response.id)
