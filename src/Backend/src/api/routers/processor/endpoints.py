"""
Endpoints related to processing speech to text.
"""
import base64
import contextlib
import logging
import os
import typing

import fastapi
import fastapi_injector
from opentelemetry import trace

from api import dependencies, errors, helpers, models, ports, tracing, typings
from api.helpers import auth
from api.helpers import opentelemetry as otel
from api.helpers import session_manager as sess_mg
from api.helpers.schemas import AnalyticalResult as UserResult

from . import schemas

router = fastapi.APIRouter()

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@contextlib.asynccontextmanager
async def otel_pubsub_ctx(
    request: fastapi.Request,
) -> typing.AsyncIterator[None]:
    """
    Attaching pubsub to otel context
    """
    message_body = (await request.json())["message"]
    pubsub_context = otel.extract_from_pubsub_push_message(message_body)
    tracing.get_trace_data(pubsub_context)
    pubsub_span_context = trace.get_current_span(pubsub_context).get_span_context()
    links = None
    if pubsub_span_context.is_valid:
        links = [trace.Link(pubsub_span_context)]

    with tracer.start_as_current_span(
        "Process pubsub message",
        kind=trace.SpanKind.CONSUMER,
        links=links,
    ):
        yield


@router.post("/_handle", response_model=None)
async def process(  # pylint: disable=too-many-locals
    request: fastapi.Request,
    body: schemas.PubsubRequest = fastapi.Body(...),
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    speech: ports.SpeechToText = fastapi_injector.Injected(ports.SpeechToText),
    list_pending: ports.ListPendingQuestions = fastapi_injector.Injected(
        ports.ListPendingQuestions
    ),
    get_exam_user: ports.GetExamUserStatus = fastapi_injector.Injected(
        ports.GetExamUserStatus
    ),
    analytical: ports.AnalyticalResult = fastapi_injector.Injected(
        ports.AnalyticalResult
    ),
) -> fastapi.Response:
    """
    Receive pubsub message.

    Handle request to receive and process the pubsub message and
    connect to speech to text and storage.

    :param body: parsed HTTP request body.
    :param speech: speech instance.
    :param storage: storage instance.

    :return: status_code indicating success or failure.
    """
    async with otel_pubsub_ctx(request):
        data = schemas.PubsubDataReprocessed.parse_raw(
            base64.b64decode(body.message.data.decode("utf-8"))
        )
        logger.info("Start processing data", extra={"result_id": str(data.result_id)})
        file_data = data.audio
        resp = await speech.process(
            phrases_id=data.phrase_set_id,
            path=f"gs://{file_data}",
            desired=file_data.rsplit("/", 1)[1],
            words=data.words,
            duration=data.duration,
            sample_rate=data.sample_rate,
            channels=data.channels,
        )
        async with uow_builder() as uow:
            try:
                user_question = await uow.result_repository.get(data.result_id)
            except errors.NotFound:
                return fastapi.Response(status_code=200)
            user_question.result = resp[1].split(" ")
            user_question.right_count = resp[2]
            user_question.status = models.ExamStatus.FINISHED
            user_question.audio_url = f"https://storage.cloud.google.com/{file_data}"
            question_list = await list_pending(
                user_question.user_id, user_question.group_id, user_question.exam_id
            )
            if len(question_list) == 0:
                exam_user = await get_exam_user(
                    user_id=user_question.user_id,
                    exam_id=user_question.exam_id,
                    group_id=user_question.group_id,
                )
                if not exam_user:
                    logger.warning(
                        "Exam user not found", extra={"result_id": str(data.result_id)}
                    )
                    return fastapi.Response(status_code=200)
                exam_user_merged: models.ExamUser = await uow.merge(exam_user)
                exam_user_merged.status = models.ExamStatus.FINISHED
            result_data = UserResult(
                school_uuid=user_question.organization_id,
                class_grade=user_question.group.grade.value,
                class_name=user_question.group.name,
                class_uuid=user_question.group_id,
                exam_end_date=user_question.exam.end_date,
                exam_start_date=user_question.exam.start_date,
                exam_grade=user_question.group.grade.value,
                exam_name=user_question.exam.name,
                exam_uuid=user_question.exam_id,
                question_amount_words=len(data.words),
                question_uuid=user_question.question_id,
                question_words=data.words,
                response_amount_hits=user_question.right_count,
                response_timestamp=helpers.time_now(),
                response_words=user_question.result,
                school_city=user_question.organization.city,
                school_name=user_question.organization.name,
                school_region=user_question.organization.region,
                student_name=user_question.user.name,
                student_uuid=user_question.user_id,
                student_customer_id=user_question.user.customer_id,
            )
            if not await analytical.save(result_data):
                logger.warning(
                    "Could not save to bigquery.",
                    extra={"result_id": str(data.result_id)},
                )
            await uow.commit()
        return fastapi.Response(status_code=200)


@router.post("/convert/_handle", response_model=None)
async def convert_audio_type(  # pylint: disable=too-many-locals
    request: fastapi.Request,
    body: schemas.PubsubRequest = fastapi.Body(...),
    publisher: ports.MessagePublisher = fastapi_injector.Injected(
        ports.MessagePublisher
    ),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
) -> fastapi.Response:
    """
    Receive pubsub message.

    Handle request to receive and process the pubsub message and
    connect to speech to text and storage.

    :param body: parsed HTTP request body.
    :param speech: speech instance.
    :param storage: storage instance.

    :return: status_code indicating success or failure.
    """
    async with otel_pubsub_ctx(request):
        data = schemas.PubsubData.parse_raw(
            base64.b64decode(body.message.data.decode("utf-8"))
        )
        logger.debug(
            "Starting audio conversion.", extra={"result_id": str(data.result_id)}
        )
        file_data = data.audio.replace("%7C", "|")
        file_stripped = (
            file_data.replace("https://", "")
            .replace("http://", "")
            .replace("storage.googleapis.com/", "")
        )
        file_path = file_stripped.split("/", 1)[1]
        content_type = await storage.get_blob_content_type(file_path)
        sample_rate = channels = None
        _, file_name = file_path.rsplit("/", 1)
        download_path = await storage.download(f"gs://{file_stripped}", file_name)
        metadata = helpers.util.get_file_metadata(download_path)
        if content_type not in {"audio/wav", "audio/x-wav"}:
            logger.debug(
                "Audio needs to be converted.", extra={"result_id": str(data.result_id)}
            )
            new_name = download_path.rsplit(".")[0] + ".wav"
            helpers.util.convert_audio(
                download_path, new_name, settings.get("env") == "prod"
            )
            metadata = helpers.util.get_file_metadata(new_name)
            file_stripped = await storage.upload_by_file(
                file_path.rsplit(".")[0] + ".wav", new_name
            )
        sample_str: str | None = metadata.get("sample_rate")
        sample_rate = int(sample_str) if sample_str else None

        channels_str: str | None = metadata.get("channels")
        channels = int(channels_str) if channels_str else None
        duration = int(metadata.get("duration", 61))
        os.remove(download_path)
        await publisher.publish(
            schemas.ReprocessedMessage(
                result_id=data.result_id,
                phrase_set_id=data.phrase_set_id,
                audio=file_stripped,
                duration=duration,
                words=[word.strip() for word in data.words if word.strip()],
                sample_rate=sample_rate,
                channels=channels,
            )
        )
        return fastapi.Response(status_code=200)


@router.post(
    "/signed", dependencies=[fastapi.Security(auth.get_token, scopes=["user", "admin"])]
)
async def create_signed_url(
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    body: schemas.CreateUserSignedRequest = fastapi.Body(...),
) -> schemas.SignedUrl:
    """
    Creates a signed url.

    Creates a Signed URL for the frontend to upload a file.

    :param body: parsed HTTP request body.
    :param storage: storage instance.
    :param session_manager: session manager instance.

    :return: signed_url.
    """
    session = await session_manager.get_current_session()
    user = session.user
    match body:
        case schemas.CreateUserSignedRequest() if "user" in user.role.scopes:
            group = user.groups[0]
            group_id = group.id
            organization_id = group.organization_id
            file_path = (
                f"{organization_id}/{group_id}/{body.exam_id}"
                f"|{body.question_id}|{session.user_id}.{body.file_type}"
            )
        case _:
            raise errors.FieldNotNullable()
    signed_url = await storage.generate_signed_url(file_path, body.mimetype)
    return schemas.SignedUrl(signed_url=signed_url)
