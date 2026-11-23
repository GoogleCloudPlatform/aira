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
from api.helpers import auth, prompt_safety, util
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


async def _resolve_authorized_exam_groups(
    session: models.Session,
    target_user_id: uuid.UUID,
    get_user_query: ports.GetUser,
) -> list[uuid.UUID]:
    """Resolve group IDs the caller is authorized to view for `target_user_id`."""
    role_scopes = (
        session.user.role.scopes if session.user and session.user.role else []
    )
    has_exam_list = "exam.list" in role_scopes
    has_user = "user" in role_scopes
    if not has_exam_list and not has_user:
        raise errors.Forbidden()

    caller_group_ids = (
        [group.id for group in session.user.groups] if session.user else []
    )
    if not caller_group_ids:
        raise errors.Forbidden()

    if not has_exam_list:
        if target_user_id != session.user_id:
            raise errors.Forbidden()
        return caller_group_ids

    if target_user_id == session.user_id:
        return caller_group_ids

    try:
        target_user = await get_user_query(user_id=target_user_id)
    except errors.NotFound as exc:
        raise errors.Forbidden() from exc

    caller_group_id_set = set(caller_group_ids)
    shared_group_ids = [
        group.id for group in target_user.groups if group.id in caller_group_id_set
    ]
    if not shared_group_ids:
        raise errors.Forbidden()
    return shared_group_ids


@router.get(
    "/{exam_id}/users/{user_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["exam.list", "user"])],
)
async def get_user_exam(
    get_user_exam: ports.GetUsersExamDetails = fastapi_injector.Injected(
        ports.GetUsersExamDetails
    ),
    get_user_query: ports.GetUser = fastapi_injector.Injected(ports.GetUser),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    exam_id: uuid.UUID = fastapi.Path(...),
    user_id: uuid.UUID = fastapi.Path(...),
    gen_ai: ports.GenAI = fastapi_injector.Injected(ports.GenAI),
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
) -> schemas.ExamWithQuestionsDataGet:
    """
    Get exams.

    Handles requests related to finding a specific exam.

    :param get_user_exam: implementation exam get query.
    :param exam_id: query param with exam identifier.
    :param user_id: query param with user identifier.
    """
    session = await session_manager.get_current_session()
    allowed_group_ids = await _resolve_authorized_exam_groups(
        session=session,
        target_user_id=user_id,
        get_user_query=get_user_query,
    )

    result = await get_user_exam(
        exam_id=exam_id,
        user_id=user_id,
        groups=allowed_group_ids,
    )

    if not result:
        raise errors.NotFound()

    exam, questions = result[0]
    exam_dict = dict(exam.__dict__)
    questions = json.loads(questions)

    audio_response_types = {
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "webm": "audio/webm",
        "mp3": "audio/mpeg",
    }
    for question in questions:
        response_data = question.get("response")
        if isinstance(response_data, dict):
            if isinstance(response_data.get("ai_feedback"), str):
                response_data["ai_feedback"] = prompt_safety.sanitize_feedback_text(
                    response_data["ai_feedback"],
                    max_length=prompt_safety.MAX_QUESTION_FEEDBACK_LENGTH,
                )
            if response_data.get("audio_url"):
                object_path = response_data["audio_url"].split("/", 4)[-1]
                ext = (
                    object_path.rsplit(".", 1)[-1].lower() if "." in object_path else ""
                )
                safe_response_type = audio_response_types.get(
                    ext, "application/octet-stream"
                )
                signed_audio_url = await storage.generate_signed_url(
                    object_path,
                    "",
                    "GET",
                    response_disposition="attachment",
                    response_type=safe_response_type,
                )
                response_data["audio_url"] = signed_audio_url
    exam_dict["questions"] = sorted(questions, key=lambda x: x["order"])

    async with uow_builder() as uow:
        exam_user = await uow.exam_user_repository.get(exam_id=exam_id, user_id=user_id)
        if not exam_user.ai_exam_feedback:
            exam_feedback = gen_ai.get_exam_feedback(questions)
            exam_user.ai_exam_feedback = prompt_safety.sanitize_feedback_text(
                exam_feedback,
                max_length=prompt_safety.MAX_EXAM_FEEDBACK_LENGTH,
            )

        exam_dict["ai_exam_feedback"] = (
            prompt_safety.sanitize_feedback_text(
                exam_user.ai_exam_feedback,
                max_length=prompt_safety.MAX_EXAM_FEEDBACK_LENGTH,
            )
            if isinstance(exam_user.ai_exam_feedback, str)
            else exam_user.ai_exam_feedback
        )
        await uow.commit()

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
    publisher: ports.MessagePublisher = fastapi_injector.Injected(
        ports.MessagePublisher
    ),
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
                    answers=question.answers,
                    theme=question.theme,
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

        # await publisher.publish(
        #     schemas.SendEmailMessage(grade=body.grade),
        #     topic=settings.get("pubsub_send_email_topic"),
        # )
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
            try:
                await speech.delete_phrase_set(q.phrase_id)
            except Exception as e:
                logger.warning(f"Failed to delete phrase set {q.phrase_id}: {e}")
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
                    answers=question.answers,
                    theme=question.theme,
                )
            )
        for k, v in body_data.items():
            setattr(exam, k, v)
        await uow.commit()

    return schemas.ExamGet.from_orm(exam)
