"""
Module containing all endpoints related to exam services
"""
from __future__ import annotations

import logging
import uuid

import fastapi
import fastapi_injector

from api import dependencies, errors, models, ports, typings
from api.helpers import auth
from api.helpers import schemas as util_schemas
from api.helpers import session_manager as sess_mg
from api.helpers import util

from . import schemas

router = fastapi.APIRouter()

logger = logging.getLogger(__name__)


@router.get("", dependencies=[fastapi.Security(auth.get_token)])
async def list_resources(
    list_data: util_schemas.ListSchema = fastapi.Depends(),
    list_exams: ports.ListExams = fastapi_injector.Injected(ports.ListExams),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    list_pending: ports.ListPendingExams = fastapi_injector.Injected(
        ports.ListPendingExams
    ),
) -> schemas.ExamList:
    """
    List exams.

    Handles requests related to exams being listed.

    :param list_exams: implementation of orgs list.
    """
    session = await session_manager.get_current_session()
    scopes = session.user.role.scopes
    if "user" in scopes:
        group_id = session.user.groups[0].id
        if not group_id:
            raise errors.NotFound("group")
        result, pagination_metadata = await list_pending(
            user_id=session.user_id,
            group_id=group_id,
            page_size=list_data.page_size,
            page=list_data.page,
        )
    else:
        groups = None
        if "admin" not in scopes:
            groups = [group.id for group in session.user.groups]
        result, pagination_metadata = await list_exams(
            groups=groups,
            page_size=list_data.page_size,
            page=list_data.page,
            query=list_data.q,
        )

    return schemas.ExamList(
        items=[schemas.Exam.from_orm(item) for item in result],
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get(
    "/{exam_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def get(
    get_exam: ports.GetExam = fastapi_injector.Injected(ports.GetExam),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    exam_id: uuid.UUID = fastapi.Path(...),
) -> schemas.ExamGet:
    """
    Get exams.

    Handles requests related to finding a specific exam.

    :param get_exam: implementation exam get query.
    :param exam_id: query param with exam identifier.
    """
    session = await session_manager.get_current_session()
    groups = None
    if "admin" not in session.user.role.scopes:
        groups = [group.id for group in session.user.groups]
    exam = await get_exam(exam_id=exam_id, groups=groups)
    return schemas.ExamGet.from_orm(exam)


@router.post(
    "",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def create(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    speech: ports.SpeechToText = fastapi_injector.Injected(ports.SpeechToText),
    body: schemas.ExamCreate = fastapi.Body(...),
) -> schemas.ExamGet:
    """
    Create exams.

    Handles requests related to finding a specific exam.

    :param uow_builder: implementation uow builder.
    :param body: exam creation body.
    """
    async with uow_builder() as uow:
        question_list = []
        for question in body.questions:
            text_list: list[str] = []
            match question.type:
                case models.QuestionType.PHRASES:
                    phrase_list = (
                        question.data.split(". ")
                        if ". " in question.data
                        else question.data.split(".")
                    )
                    for phrase in phrase_list:
                        text_list.extend(util.words_recursion(phrase))
                case models.QuestionType.WORDS:
                    text_list = question.data.split(" ")
            phrases = [{"value": text, "boost": 100} for text in text_list]
            phrase_set_id = await speech.create_phrase_set(phrases)
            phrase_id = phrase_set_id.split("/")[-1]
            question_list.append(
                models.Question(
                    name=question.name,
                    data=question.data,
                    phrase_id=phrase_id,
                    type=question.type,
                )
            )
        exam = models.Exam(
            name=body.name,
            questions=question_list,
            grade=body.grade,
            start_date=body.start_date,
            end_date=body.end_date,
        )
        exam_model = await uow.exam_repository.create(exam)
        await uow.commit()
    return schemas.ExamGet.from_orm(exam_model)


@router.get(
    "/{exam_id}/questions",
    dependencies=[fastapi.Security(auth.get_token, scopes=["user"])],
)
async def get_questions(
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    exam_id: uuid.UUID = fastapi.Path(...),
    list_questions: ports.ListQuestionsWithStatus = fastapi_injector.Injected(
        ports.ListQuestionsWithStatus
    ),
) -> list[schemas.QuestionList]:
    """
    List pending questions.

    Handles requests related to questions being listed.

    :param list_questions: implementation of questions list.
    """
    session = await session_manager.get_current_session()
    group_id = session.user.groups[0].id
    results = await list_questions(session.user_id, group_id, exam_id)
    return [
        schemas.QuestionList(
            id=question.id,
            data=question.data,
            name=question.name,
            type=question.type,
            status=question_status.status
            if question_status
            else models.ExamStatus.NOT_STARTED,
        )
        for question, question_status in results
    ]


@router.post(
    "/{exam_id}/questions/{question_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["user"])],
)
# pylint: disable=too-many-locals
async def send_question_data(
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    exam_id: uuid.UUID = fastapi.Path(...),
    question_id: uuid.UUID = fastapi.Path(...),
    get_pending: ports.GetPendingQuestion = fastapi_injector.Injected(
        ports.GetPendingQuestion
    ),
    get_exam_user: ports.GetExamUserStatus = fastapi_injector.Injected(
        ports.GetExamUserStatus
    ),
    session_factory: typings.SessionFactory = fastapi_injector.Injected(
        typings.SessionFactory
    ),
    publisher: ports.MessagePublisher = fastapi_injector.Injected(
        ports.MessagePublisher
    ),
    body: schemas.QuestionPost = fastapi.Body(...),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
) -> fastapi.Response:
    """
    Answer a pending question.

    Handles requests related to questions being listed.

    :param list_pending_questions: implementation of questions list.
    """
    user_session = await session_manager.get_current_session()
    group_id = user_session.user.groups[0].id
    organization_id = user_session.user.organizations[0].id
    async with session_factory() as session:
        question_data = await get_pending(
            user_session.user_id, group_id, exam_id, question_id
        )
        if not question_data:
            raise fastapi.HTTPException(
                status_code=400,
                detail="You already finished this exam/question",
            )

        if not await get_exam_user(
            user_id=user_session.user_id, exam_id=exam_id, group_id=group_id
        ):
            exam_user = models.ExamUser(
                exam_id=exam_id,
                user_id=user_session.user_id,
                status=models.ExamStatus.IN_PROGRESS,
            )
            session.add(exam_user)

        exam_user_question = models.ExamUserQuestion(
            exam_id=exam_id,
            user_id=user_session.user_id,
            question_id=question_id,
            group_id=group_id,
            organization_id=organization_id,
            result=[],
            right_count=0,
            audio_url="",
        )
        session.add(exam_user_question)

        text_list = (
            question_data.data.replace(". ", " ")
            .replace(", ", " ")
            .replace(".", " ")
            .replace(",", " ")
            .strip()
            .split(" ")
        )

        await publisher.publish(
            schemas.QuestionMessage(
                result_id=exam_user_question.id,
                phrase_set_id=question_data.phrase_id,
                audio=body.url,
                words=text_list,
            ),
            topic=settings.get("pubsub_convert_topic"),
        )
        await session.commit()
    return fastapi.Response(status_code=fastapi.status.HTTP_201_CREATED)
