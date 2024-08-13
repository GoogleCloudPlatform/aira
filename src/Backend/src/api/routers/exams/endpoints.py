"""
Module containing all endpoints related to exam services
"""

# pylint: disable=unused-argument,redefined-outer-name
from __future__ import annotations

import json
import logging
import uuid

import fastapi
import fastapi_injector

from api import dependencies, errors, models, ports, typings
from api.helpers import auth, util
from api.helpers import schemas as util_schemas
from api.helpers import session_manager as sess_mg

from . import crud, schemas

router = fastapi.APIRouter(tags=["exams"])

logger = logging.getLogger(__name__)


@router.get(
    "", dependencies=[fastapi.Security(auth.get_token, scopes=["admin", "exam.list"])]
)
async def list_resources(
    list_data: util_schemas.ListSchema = fastapi.Depends(),
    list_exams: ports.ListExams = fastapi_injector.Injected(ports.ListExams),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
) -> schemas.ExamList:
    """
    List exams.

    Handles requests related to exams being listed.

    :param list_exams: implementation of orgs list.
    """
    session = await session_manager.get_current_session()
    scopes = session.user.role.scopes
    groups = None
    if "exam.list" in scopes:
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


@router.get(
    "/{exam_id}/users/{user_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["exam.list"])],
)
async def get_user_exam(
    get_user_exam: ports.GetUsersExamDetails = fastapi_injector.Injected(
        ports.GetUsersExamDetails
    ),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    exam_id: uuid.UUID = fastapi.Path(...),
    user_id: uuid.UUID = fastapi.Path(...),
) -> schemas.ExamWithQuestionsDataGet:
    """
    Get exams.

    Handles requests related to finding a specific exam.

    :param get_user_exam: implementation exam get query.
    :param exam_id: query param with exam identifier.
    :param user_id: query param with user identifier.
    """
    result = await get_user_exam(exam_id=exam_id, user_id=user_id)

    if not result:
        raise errors.NotFound()

    exam, questions = result[0]
    exam_dict = exam.__dict__
    questions = json.loads(questions)

    for question in questions:
        if question.get("response"):
            signed_audio_url = await storage.generate_signed_url(
                question["response"]["audio_url"].split("/", 4)[-1], "", "GET"
            )
            question["response"]["audio_url"] = signed_audio_url
    exam_dict["questions"] = sorted(questions, key=lambda x: x["order"])

    return schemas.ExamWithQuestionsDataGet(**exam_dict)


@router.post(
    "",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def create(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    body: schemas.ExamCreate = fastapi.Body(...),
) -> schemas.ExamGet:
    """
    Create exams.

    Handles requests related to finding a specific exam.

    :param uow_builder: implementation uow builder.
    :param settings: Settings port.
    :param storage: Storage port.
    :param body: exam creation body.
    """
    async with uow_builder() as uow:
        question_list = []
        for question in body.questions:
            speech = dependencies.get_speech_to_text("v1", settings, storage)
            phrase_id = await crud.build_question_phrase(question, speech)
            question_list.append(
                models.Question(
                    name=question.name,
                    data=question.data,
                    formatted_data=question.formatted_data,
                    phrase_id=phrase_id,
                    type=question.type,
                    order=question.order,
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


@router.patch(
    "/{exam_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def update_exam(
    exam_id: uuid.UUID = fastapi.Path(...),
    body: schemas.ExamPatch = fastapi.Body(...),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
) -> schemas.ExamGet:
    """
    Patch exams.

    Handles requests related to updating a specific exam.

    :param exam_id: query param with exam identifier.
    :param uow_builder: implementation uow builder.
    :param settings: Settings port.
    :param storage: Storage port.
    :param body: exam creation body.
    """
    speech = dependencies.get_speech_to_text("v1", settings, storage)
    async with uow_builder() as uow:
        exam = await uow.exam_repository.get(exam_id=exam_id)
        if util.time_now() >= exam.start_date:
            raise errors.CantEditExam
        body_data = body.dict()
        body_data.pop("questions")
        for q in exam.questions:
            await speech.delete_phrase_set(q.phrase_id)
        exam.questions.clear()
        for question in body.questions:
            phrase_id = await crud.build_question_phrase(question, speech)
            exam.questions.append(
                models.Question(
                    name=question.name,
                    data=question.data,
                    formatted_data=question.formatted_data,
                    phrase_id=phrase_id,
                    type=question.type,
                    order=question.order,
                )
            )
        for k, v in body_data.items():
            setattr(exam, k, v)
        await uow.commit()

    return schemas.ExamGet.from_orm(exam)
