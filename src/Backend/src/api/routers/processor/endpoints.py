"""
Endpoints related to processing speech to text.
"""

import base64
import datetime
import logging
import os
import urllib.parse
import uuid

import fastapi
import fastapi_injector
from opentelemetry import trace

from api import dependencies, errors, helpers, models, ports, typings
from api.adapters import sere
from api.domain.service import process_result
from api.helpers import auth, util
from api.helpers import session_manager as sess_mg
from api.helpers.schemas import AnalyticalResult as UserResult
from api.routers.schemas import PubsubRequest

from . import schemas

router = fastapi.APIRouter(include_in_schema=False)

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def calculate_user_rating(
    question_data: models.ExamUserQuestion,
    question_type: models.QuestionType,
    current_rating: models.UserRating,
    data_words: list[str],
) -> models.UserRating:
    """
    Calculate user rating based on answered question.
    """
    # ruff: noqa: PLR0911
    if current_rating == models.UserRating.FLUENT:
        return current_rating
    rating_intersection: set[models.UserRating] = {
        models.UserRating.READER,
        models.UserRating.NO_RATING,
    }
    match question_type:
        case models.QuestionType.PHRASES:
            qty_word = len(question_data.result)
            if qty_word > 65 and question_data.right_count / qty_word >= 0.9:
                return models.UserRating.FLUENT
            return current_rating
        case models.QuestionType.COMPLEX_WORDS:
            if question_data.right_count >= 6 and current_rating in rating_intersection:
                return models.UserRating.READER
            if (
                question_data.right_count > 0
                or current_rating == models.UserRating.READER
            ):
                return models.UserRating.PRE_READER_FOUR
            if current_rating == models.UserRating.NO_RATING:
                return models.UserRating.PRE_READER_ONE
            return current_rating
        case models.QuestionType.WORDS:
            if (
                question_data.right_count >= 11
                and current_rating in rating_intersection
            ):
                return models.UserRating.READER
            if question_data.right_count > 0:
                return models.UserRating.PRE_READER_FOUR
            return calculate_pre_reader_rating(question_data.result, data_words)


def calculate_pre_reader_rating(
    sentence: list[str], expected: list[str]
) -> models.UserRating:
    joined_sentence = "".join(sentence).lower()
    joined_expected = "".join(expected).lower()
    levenshtein_rating = levenshtein_distance(joined_sentence, joined_expected)
    max_len = max(len(joined_sentence), len(joined_expected))
    percentage = 100.0
    if max_len != 0:
        percentage = 1 - levenshtein_rating / max_len  # similarity [0,1]

    match util.check_spelling_or_syllables(sentence):
        case 1 if percentage >= 0.1:  # Silabou
            return models.UserRating.PRE_READER_THREE
        case -1 if percentage >= 0.05:  # Soletrou
            return models.UserRating.PRE_READER_TWO
    return models.UserRating.PRE_READER_ONE


def levenshtein_distance(string_one: str, string_two: str) -> int:
    """
    Checks the levenshtein distance between two strings
    For every insertion, deletion or substitution it adds 1 point
    0 points means string_one and string_two are the same string
    """
    if len(string_one) < len(string_two):
        return levenshtein_distance(string_two, string_one)

    if len(string_two) == 0:
        return len(string_one)

    previous_row = list(range(len(string_two) + 1))
    for i, char_one in enumerate(string_one):
        current_row = [i + 1]
        for j, char_two in enumerate(string_two):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (char_one != char_two)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def levenshtein_distance_words(list_one: list[str], list_two: list[str]) -> int:
    """
    Checks the levenshtein distance between two lists of strings
    eg.: ["hello", "wonderful", "world"]  and ["hello", "darling"]
    returns 2 points (1 substitution and 1 deletion)
    """
    distances = [
        [0 for _ in range(len(list_two) + 1)] for _ in range(len(list_one) + 1)
    ]

    for i in range(len(list_one) + 1):
        distances[i][0] = i
    for j in range(len(list_two) + 1):
        distances[0][j] = j

    for i in range(1, len(list_one) + 1):
        for j in range(1, len(list_two) + 1):
            cost = 0 if list_one[i - 1] == list_two[j - 1] else 1
            distances[i][j] = min(
                distances[i - 1][j] + 1,
                distances[i][j - 1] + 1,
                distances[i - 1][j - 1] + cost,
            )

    return distances[-1][-1]


@router.post("/_handle", response_model=None)
async def process(
    request: fastapi.Request,
    body: PubsubRequest = fastapi.Body(...),
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
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
    :param settings: Settings port.
    :param storage: Storage port.

    :return: status_code indicating success or failure.
    """
    logger.info("Starting processing pubsub message.")
    data = schemas.PubsubDataReprocessed.parse_raw(
        base64.b64decode(body.message.data.decode("utf-8"))
    )
    logger.info("Start processing data", extra={"result_id": str(data.result_id)})
    file_data = data.audio
    version = "v2"
    model_type = "latest_long"
    if data.question_type in {
        models.QuestionType.WORDS.value,
        models.QuestionType.COMPLEX_WORDS.value,
    }:
        model_type = "chirp"
        version = "v2chirp"
    speech = dependencies.get_speech_to_text(version, settings, storage)
    tts_words = await speech.process(
        phrases_id=data.phrase_set_id,
        path=f"gs://{file_data}",
        desired=file_data.rsplit("/", 1)[1],
        words=data.words,
        duration=data.duration,
        sample_rate=data.sample_rate,
        channels=data.channels,
        model_type=model_type,
    )

    right_count, user_result = process_result.get_right_count_user_result(
        data.words, tts_words, data.question_type
    )

    async with uow_builder() as uow:
        try:
            user_question = await uow.result_repository.get(data.result_id)
        except errors.NotFound:
            return fastapi.Response(status_code=200)
        user_question.result = user_result
        user_question.right_count = right_count
        user_question.status = models.ExamStatus.FINISHED
        user_question.audio_url = f"https://storage.cloud.google.com/{file_data}"
        len_result = len(user_question.result)
        user_question.user_accuracy = (
            user_question.right_count / len_result if len_result else 0.0
        )
        user_question.total_accuracy = (
            user_question.right_count / len(data.words) if data.words else 0.0
        )
        question_list = await list_pending(
            user_question.user_id, user_question.group_id, user_question.exam_id
        )

        user_rating = models.UserRating.NO_RATING

        exam_user = await get_exam_user(
            user_id=user_question.user_id,
            exam_id=user_question.exam_id,
            group_id=user_question.group_id,
        )
        exam_user_merged: models.ExamUser = await uow.merge(exam_user)
        if len(question_list) == 1:
            if not exam_user:
                logger.warning(
                    "Exam user not found", extra={"result_id": str(data.result_id)}
                )
                return fastapi.Response(status_code=200)
            if exam_user.status == models.ExamStatus.FINISHED:
                logger.warning(
                    "Exam is already done and it's running again.",
                    extra={"result_id": str(data.result_id)},
                )
                return fastapi.Response(status_code=200)
            exam_user_merged.status = models.ExamStatus.FINISHED

        question = await uow.question_repository.get(user_question.question_id)
        user_rating = calculate_user_rating(
            user_question, question.type, exam_user_merged.user_rating, data.words
        )
        exam_user_merged.user_rating = user_rating

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
            school_state=user_question.organization.state,
            school_county=user_question.organization.county,
            student_name=user_question.user.name,
            student_uuid=user_question.user_id,
            student_customer_id=user_question.user.customer_id,
            user_rating=user_rating,
        )
        if err := await analytical.save(result_data):
            logger.warning(
                "Could not save to bigquery.",
                extra={"result_id": str(data.result_id), "errors": err},
            )
        await uow.commit()
    return fastapi.Response(status_code=200)


@router.post("/convert/_handle", response_model=None)
async def convert_audio_type(
    request: fastapi.Request,
    body: PubsubRequest = fastapi.Body(...),
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
    data = schemas.PubsubData.parse_raw(
        base64.b64decode(body.message.data.decode("utf-8"))
    )
    logger.debug("Starting audio conversion.", extra={"result_id": str(data.result_id)})
    file_data = urllib.parse.unquote(data.audio)
    file_stripped = (
        file_data.replace("https://", "")
        .replace("http://", "")
        .replace("storage.googleapis.com/", "")
    )
    file_path = file_stripped.split("/", 1)[1]
    if not await storage.get_blob_size(file_path):
        logger.warning("File with 0 bytes.", extra={"result_id": str(data.result_id)})
        return fastapi.Response(status_code=200)
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
            question_type=data.question_type,
        )
    )
    return fastapi.Response(status_code=200)


@router.get(
    "/sync",
    dependencies=[fastapi.Security(auth.validate_scheduler_token)],
)
async def sync_database(  # noqa: PLR0915
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    sere_api: sere.SereApi = fastapi_injector.Injected(sere.SereApi),
) -> fastapi.Response:
    logger.info("Starting sync database.")
    async with uow_builder() as uow:
        student_role = await uow.role_repository.get(name="user")
        professor_role = await uow.role_repository.get(name="professor")
        # Organization logic
        updated_organizations: dict[str, models.Organization] = {}
        logger.info("Start org endpoint call.")
        organizations = await sere_api.list_organization()
        logger.info("Finished org endpoint call.")
        org_cid_list = [str(org.get("codMec")) for org in organizations]
        cached_orgs = await uow.organization_repository.list(customer_ids=org_cid_list)
        for organization in organizations:
            sync_org = typings.CreateOrUpdateOrganization(
                customer_id=str(organization.get("codMec")),
                name=str(organization.get("descEscola")),
                region=str(organization.get("descNre")),
                city=str(organization.get("descMun")),
                state="PR",
                county=str(organization.get("descMun")),
            )
            updated_org = await uow.organization_repository.create_or_update(
                sync_org, cached_orgs
            )
            if updated_org:
                updated_organizations[str(updated_org.customer_id)] = updated_org

        del organizations, organization, org_cid_list, cached_orgs
        logger.info("Finished org import.")
        # Group logic
        # Nossa referencia de código de seriação, que garante que são turmas
        # do segundo ano são esses: 1211, 988, 356, 1441, 1430, 351, 993
        second_grade_codes = {1211, 988, 356, 1441, 1430, 351, 993}
        updated_groups: dict[str, models.Group] = {}
        logger.info("Start group endpoint call.")
        groups = await sere_api.list_group()
        logger.info("Finished group endpoint call.")
        group_cid_list = [str(group.get("codTurma")) for group in groups]
        cached_groups = await uow.group_repository.list(customer_ids=group_cid_list)
        shift_mapping = {
            "Manhã": models.Shifts.MORNING,
            "Tarde": models.Shifts.AFTERNOON,
            "Noite": models.Shifts.EVENING,
            "Integral": models.Shifts.ALLDAY,
        }
        for group in groups:
            if group.get("codSeriacao") not in second_grade_codes:
                continue
            desc_seriacao = str(group.get("descSeriacao")).strip()
            desc_turma = str(group.get("descTurma")).strip()
            desc_turno = shift_mapping[str(group.get("descTurno")).strip()]
            group_name = f"{desc_seriacao} - {desc_turma} - {desc_turno}"
            sync_group = typings.CreateOrUpdateGroup(
                name=group_name,
                customer_id=str(group.get("codTurma")),
                grade=models.Grades.SECOND_FUND,
                shift=desc_turno,
            )
            updated_group = await uow.group_repository.create_or_update(
                sync_group,
                str(group.get("codMec")),
                updated_organizations,
                cached_groups,
            )
            if updated_group:
                updated_groups[str(updated_group.customer_id)] = updated_group

        del groups, group, cached_groups, group_cid_list
        logger.info("Finished group import.")
        # Student logic
        logger.info("Starting student endpoint paginated call.")
        uow._session.autoflush = False
        processed_users = []
        for nre in range(1, 33):
            logger.info(f"Page {nre}/33")
            students = await sere_api.list_student_paginated(nre)
            student_cid_list = [str(student.get("cgm")) for student in students]
            cached_users = await uow.user_repository.list(customer_ids=student_cid_list)
            for student in students:
                student_user = typings.CreateOrUpdateUser(
                    external_id=None,
                    name=student.get("nome"),
                    email_address=f"{student.get('cgm')}@example.com",
                    customer_id=student.get("cgm"),
                    type=models.UserType.PASSWORD,
                    role_id=student_role.id,
                    county=None,
                    region=None,
                    state=None,
                    orgs_customer_id=None,
                    groups_customer_id=None,
                )
                if student.get("cgm") in processed_users:
                    continue
                processed_users.append(student.get("cgm"))
                await uow.user_repository.create_or_update_student(
                    student_user,
                    str(student.get("codTurma")),
                    updated_groups,
                    cached_users,
                )
            del students, student, cached_users, student_cid_list
        del processed_users
        logger.info("Finished student import.")
        # Professor logic
        logger.info("Start professor endpoint call.")
        professors = await sere_api.list_professor()
        logger.info("Finished professor endpoint call.")
        to_be_processed: dict[str, typings.CreateOrUpdateUser] = {}
        for professor in professors:
            if not professor.get("nomeProfessor") or not professor.get(
                "emailProfessor"
            ):
                continue
            if professor["cpfProfessor"] not in to_be_processed:
                professor_user = typings.CreateOrUpdateUser(
                    external_id=None,
                    name=str(professor.get("nomeProfessor")),
                    email_address=professor.get(
                        "emailProfessor", f"{uuid.uuid4()}@example.com"
                    ),
                    customer_id=professor.get("cpfProfessor"),
                    type=models.UserType.PASSWORD,
                    role_id=professor_role.id,
                    county=None,
                    region=None,
                    state=None,
                    groups_customer_id=[str(professor.get("codTurma"))],
                    orgs_customer_id=[str(professor.get("codMec"))],
                )
                to_be_processed[professor["cpfProfessor"]] = professor_user
            else:
                cur_prof_schema = to_be_processed[professor["cpfProfessor"]]
                assert cur_prof_schema.groups_customer_id is not None
                assert cur_prof_schema.orgs_customer_id is not None
                if (
                    professor.get("codTurma")
                    and str(professor["codTurma"])
                    not in cur_prof_schema.groups_customer_id
                ):
                    cur_prof_schema.groups_customer_id.append(
                        str(professor["codTurma"])
                    )
                if (
                    professor.get("codMec")
                    and str(professor["codMec"]) not in cur_prof_schema.orgs_customer_id
                ):
                    cur_prof_schema.orgs_customer_id.append(str(professor["codMec"]))
        del professors, professor
        cached_profs = await uow.user_repository.list(
            customer_ids=list(to_be_processed.keys())
        )
        for prof in to_be_processed.values():
            await uow.user_repository.create_or_update_professor(
                prof,
                prof.groups_customer_id or [],
                prof.orgs_customer_id or [],
                updated_organizations,
                updated_groups,
                cached_profs,
            )
        del (
            prof,
            to_be_processed,
            updated_organizations,
            updated_groups,
            cached_profs,
        )
        logger.info("Finished professor import.")
        await uow.commit()
    logger.info("Sync finished.")
    return fastapi.Response(status_code=200)


@router.post(
    "/signed",
    dependencies=[
        fastapi.Security(auth.get_token, scopes=["user", "user.impersonate", "admin"])
    ],
)
async def create_signed_url(
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    body: (
        schemas.CreateUserSignedRequest | schemas.CreateImportSignedRequest
    ) = fastapi.Body(...),
    list_personifiable: ports.ListPersonifiableUsers = fastapi_injector.Injected(
        ports.ListPersonifiableUsers
    ),
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
        case schemas.CreateUserSignedRequest() if (
            "user" in user.role.scopes or "user.impersonate" in user.role.scopes
        ):
            user_id = body.user_id
            if "user.impersonate" in user.role.scopes:
                impersonate_list = await list_personifiable(
                    groups=[group.id for group in session.user.groups]
                )
                if not (
                    user_tb_imp := next(
                        user_imp
                        for user_imp in impersonate_list
                        if user_imp.id == user_id
                    )
                ):
                    raise errors.Forbidden()
                group = user_tb_imp.groups[0]
            else:
                if session.user_id != user_id:
                    raise errors.Forbidden()
                group = user.groups[0]
            group_id = group.id
            organization_id = group.organization_id
            file_path = (
                f"{organization_id}/{group_id}/{body.exam_id}"
                f"|{body.question_id}|{user_id}.{body.file_type}"
            )
        case schemas.CreateImportSignedRequest() if "admin" in user.role.scopes:
            current_date = datetime.datetime.now().strftime("%Y%m%d")
            file_path = (
                f"import/{body.type.value}"
                f"/{current_date}|{uuid.uuid4().hex}.{body.file_type}"
            )
        case _:
            raise errors.FieldNotNullable()
    signed_url = await storage.generate_signed_url(file_path, body.mimetype)
    return schemas.SignedUrl(signed_url=signed_url)
