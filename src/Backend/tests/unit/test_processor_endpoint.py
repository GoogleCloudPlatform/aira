"""
Unit tests for `process`
"""

import base64
import json
import typing
import unittest.mock
import uuid

import fastapi
import hypothesis
import pytest
import starlette
from api import models, typings
from api.adapters import google
from api.adapters.memory import exam, result, unit_of_work
from api.domain.service import process_result
from api.helpers import UUIDEncoder
from api.routers import processor
from api.routers import schemas as routers_schemas
from api.routers.processor import schemas
from hypothesis import strategies as st


@pytest.mark.asyncio
@hypothesis.given(
    request=st.builds(
        routers_schemas.PubsubRequest,
        message=st.builds(
            routers_schemas.PubsubMessage,
            data=st.builds(
                schemas.PubsubDataReprocessed,
                audio=st.just("id/teste/lul"),
                duration=st.integers(max_value=120),
                words=st.lists(st.text(), min_size=1),
            ).map(
                lambda x: base64.b64encode(
                    json.dumps(
                        x.dict(),
                        cls=UUIDEncoder,
                    ).encode("utf-8")
                )
            ),
        ),
    ),
)
@hypothesis.settings(
    max_examples=5,
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
)
async def test_processor_process_succesfully(
    request: routers_schemas.PubsubRequest,
    fake_user: models.User,
    fake_group: models.Group,
    fake_exam: models.Exam,
    fake_question: models.Question,
    cloud_storage: google.CloudStorage,
) -> None:
    """
    tests if processor endpoint process correctly.
    """
    speech = unittest.mock.AsyncMock()
    analytical = unittest.mock.AsyncMock()
    analytical.save.return_value = True
    speech.process.return_value = ""
    data = schemas.PubsubDataReprocessed.parse_raw(
        base64.b64decode(request.message.data).decode("utf-8")
    )
    exam_user_question = models.ExamUserQuestion(
        user_id=uuid.uuid4(),
        exam_id=uuid.uuid4(),
        question_id=fake_question.id,
        group_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        result=[],
        right_count=0,
        audio_url="",
        total_accuracy=0.0,
        user_accuracy=0.0,
    )
    exam_user_question.group = fake_group
    exam_user_question.user = fake_user
    exam_user_question.organization = fake_group.organization
    exam_user_question.exam = fake_exam
    exam_user_question.id = data.result_id
    result_repository = result.ResultRepository([exam_user_question])
    question_repository = exam.QuestionRepository([fake_question])
    get_exam_user = exam.GetExamUserStatus(
        [
            models.ExamUser(
                exam_id=exam_user_question.exam_id,
                user_id=exam_user_question.user_id,
                status=models.ExamStatus.IN_PROGRESS,
            )
        ]
    )
    settings = typing.cast(typings.Settings, {})
    uow_builder = unit_of_work.UnitOfWorkBuilder(
        result_repository=result_repository,
        question_repository=question_repository,
    )
    with unittest.mock.patch(
        "api.dependencies.get_speech_to_text", return_value=speech
    ):
        response = await processor.process(
            request=fastapi.Request(
                scope=dict(  # pylint: disable=use-dict-literal
                    type="http",
                    method="POST",
                    path="/test",
                    headers={},
                    route=starlette.routing.Route(
                        path="/test", endpoint=unittest.mock.Mock()
                    ),
                    root_path="",
                )
            ),
            body=request,
            uow_builder=uow_builder,
            settings=settings,
            storage=cloud_storage,
            list_pending=exam.ListPendingQuestions(),
            get_exam_user=get_exam_user,
            analytical=analytical,
        )
    speech.process.assert_called_with(
        phrases_id=data.phrase_set_id,
        path="gs://id/teste/lul",
        desired="lul",
        words=data.words,
        duration=data.duration,
        sample_rate=data.sample_rate,
        channels=data.channels,
        model_type="latest_long",
    )
    assert response.status_code == 200


@pytest.mark.asyncio
@hypothesis.given(
    request=st.builds(
        schemas.CreateUserSignedRequest,
        file_type=st.just("wav"),
    )
)
@hypothesis.settings(
    max_examples=5,
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
)
async def test_successful_signed_url_user(
    request: schemas.CreateUserSignedRequest,
    fake_user_session: models.Session,
) -> None:
    """
    tests if signed url is created successfully.
    """
    sess_manager = unittest.mock.AsyncMock()
    sess_manager.get_current_session.return_value = fake_user_session
    cloud_storage = unittest.mock.AsyncMock()
    group = fake_user_session.user.groups[0]
    group_id = group.id
    organization_id = group.organization_id
    request.user_id = fake_user_session.user_id
    file_path = (
        f"{organization_id}/{group_id}/{request.exam_id}"
        f"|{request.question_id}|{fake_user_session.user_id}.{request.file_type}"
    )
    desired_path = f"https://storage.googleapis.com/{file_path}"
    cloud_storage.generate_signed_url.return_value = desired_path
    response = await processor.create_signed_url(
        session_manager=sess_manager, storage=cloud_storage, body=request
    )
    expected = schemas.SignedUrl(signed_url=desired_path)
    assert response == expected


@pytest.mark.parametrize(
    "actual_words, tts_words, amount", [(["sem"], "cem", 1), (["cela"], "sela", 1)]
)
def test_get_right_count_homophones(
    actual_words: list[str], tts_words: str, amount: int
) -> None:
    with unittest.mock.patch(
        "api.domain.service.phonemes.phonemize_data_list", unittest.mock.MagicMock()
    ) as phonemize_data_list:
        phonemize_data_list.return_value = ["word"]
        right_count, _ = process_result.get_right_count_user_result(
            actual_words, tts_words, "words"
        )
    assert right_count == amount
    assert " ".join(actual_words) != tts_words
