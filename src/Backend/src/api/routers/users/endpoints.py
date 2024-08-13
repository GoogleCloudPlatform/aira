"""
Module containing all endpoints related to user services
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime

import fastapi
import fastapi_injector
from passlib import context

from api import dependencies, errors, models, ports, typings
from api.helpers import auth, data
from api.helpers import session_manager as sess_mg
from api.helpers.schemas import AnalyticalResult as UserResult
from api.helpers.schemas import ImportData, ListSchema
from api.routers.exams import schemas as exam_schemas

from . import crud, schemas

router = fastapi.APIRouter(tags=["users"])

logger = logging.getLogger(__name__)


@router.get("/me", dependencies=[fastapi.Security(auth.get_token)])
async def get_profile(
    get_user: ports.GetUser = fastapi_injector.Injected(ports.GetUser),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
) -> schemas.UserGet:
    """
    Get current user.
    :param get_user: implementation for get user port.
    :param session_manager: session manager to get current user.
    """
    current_user = await session_manager.get_current_session()
    user = await get_user(user_id=current_user.user_id)
    return schemas.UserGet.from_orm(user)


@router.get(
    "/export",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def export_users(
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    list_users: ports.ListUsers = fastapi_injector.Injected(ports.ListUsers),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    roles: list[uuid.UUID] | None = fastapi.Query(default=None),
    groups: list[uuid.UUID] | None = fastapi.Query(default=None),
    organizations: list[uuid.UUID] | None = fastapi.Query(default=None),
    page_size: int = fastapi.Query(default=-1),
) -> fastapi.Response:
    """
    Export users as csv.

    :param session_manager: implementation of session to get current user.
    :param roles: list of roles uuid.
    :param groups: list of groups uuid.
    :param organizations: list of orgs uuid.
    :param list_users: implementation of users list.
    :param storage: implementation of storage.
    """
    current_session = await session_manager.get_current_session()
    users, _ = await list_users(
        roles=roles, groups=groups, organizations=organizations, page_size=page_size
    )
    url = await data.handle_export(
        objs=users,
        export_keys=[
            "id",
            "customer_id",
            "email_address",
            "name",
            "state",
            "region",
            "county",
            "role_id",
            "groups",
            "organizations",
        ],
        user_id=current_session.user.id,
        exp_type="users",
        storage=storage,
    )
    return fastapi.responses.JSONResponse(content={"url": url})


@router.get("", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])])
async def list_resources(
    roles: list[uuid.UUID] | None = fastapi.Query(default=None),
    groups: list[uuid.UUID] | None = fastapi.Query(default=None),
    organizations: list[uuid.UUID] | None = fastapi.Query(default=None),
    list_data: ListSchema = fastapi.Depends(),
    list_users: ports.ListUsers = fastapi_injector.Injected(ports.ListUsers),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
) -> schemas.UserList:
    """
    List users.

    Handles requests related to users being listed.

    :param roles: roles filter for query.
    :param groups: groups filter for query.
    :param organizations: organizations filter for query.
    :param list_data: common list schema.
    :param list_users: implementation of orgs list.
    :param session_manager: implementation of session to get current user.
    """
    current_session = await session_manager.get_current_session()
    if "admin" not in current_session.user.role.scopes:
        groups = (
            [
                gp.id
                for gp in current_session.user.groups
                if not groups or gp.id in groups
            ]
            if current_session.user.groups
            else None
        )
        organizations = (
            [
                org.id
                for org in current_session.user.organizations
                if not organizations or org.id in organizations
            ]
            if current_session.user.organizations
            else None
        )
    result, pagination_metadata = await list_users(
        roles=roles,
        groups=groups,
        organizations=organizations,
        page_size=list_data.page_size,
        page=list_data.page,
        query=list_data.q,
    )

    return schemas.UserList(
        items=result,
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get(
    "/exams",
    dependencies=[fastapi.Security(auth.get_token, scopes=["user.list"])],
)
async def list_resources_with_exams(
    groups: list[uuid.UUID] | None = fastapi.Query(default=None),
    show_finished: bool = fastapi.Query(default=True),
    list_data: ListSchema = fastapi.Depends(),
    list_users: ports.ListUsersWithExams = fastapi_injector.Injected(
        ports.ListUsersWithExams
    ),
    list_roles: ports.ListRoles = fastapi_injector.Injected(ports.ListRoles),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
) -> schemas.UserWithExamsList:
    """
    List users.

    Handles requests related to users being listed.

    :param groups: groups filter for query.
    :param show_finished: show users with finished exams filter for query.
    :param list_data: common list schema.
    :param list_users: implementation of orgs list.
    :param session_manager: implementation of session to get current user.
    """
    current_session = await session_manager.get_current_session()
    groups = (
        [gp.id for gp in current_session.user.groups if not groups or gp.id in groups]
        if current_session.user.groups
        else []
    )
    organizations = [org.id for org in current_session.user.organizations]

    roles = await list_roles(scope="user")
    role_ids = [role.id for role in roles[0]]

    result, pagination_metadata = await list_users(
        groups=groups,
        organizations=organizations,
        role_ids=role_ids,
        page_size=list_data.page_size,
        page=list_data.page,
        query=list_data.q,
        show_finished=show_finished,
    )

    return schemas.UserWithExamsList(
        items=result,
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get(
    "/dashboard",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin", "exam.list"])],
)
async def list_dashboard(
    request: fastapi.Request,
    analytical: ports.AnalyticalResult = fastapi_injector.Injected(
        ports.AnalyticalResult
    ),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    groups: list[str] | None = fastapi.Query(default=None),
    organizations: list[str] | None = fastapi.Query(default=None),
    school_region: str | None = fastapi.Query(default=None),
    school_city: str | None = fastapi.Query(default=None),
    exam_name: str | None = fastapi.Query(default=None),
    school_name: str | None = fastapi.Query(default=None),
    class_name: str | None = fastapi.Query(default=None),
    exam_start_date: datetime | None = fastapi.Query(default=None),
    exam_end_date: datetime | None = fastapi.Query(default=None),
) -> list[UserResult]:
    current_session = await session_manager.get_current_session()
    if "admin" not in current_session.user.role.scopes:
        groups = (
            [
                str(gp.id)
                for gp in current_session.user.groups
                if not groups or gp.id in groups
            ]
            if current_session.user.groups
            else None
        )
        organizations = (
            [
                str(org.id)
                for org in current_session.user.organizations
                if not organizations or org.id in organizations
            ]
            if current_session.user.organizations
            else None
        )
    return [
        UserResult(**result)
        for result in await analytical.get_student_results(
            school_region=school_region,
            school_city=school_city,
            exam_name=exam_name,
            school_name=school_name,
            class_name=class_name,
            exam_start_date=exam_start_date,
            exam_end_date=exam_end_date,
            organizations=organizations,
            groups=groups,
        )
    ]


@router.get(
    "/{user_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def get(
    get_user: ports.GetUser = fastapi_injector.Injected(ports.GetUser),
    user_id: uuid.UUID = fastapi.Path(...),
) -> schemas.UserGet:
    """
    Get users.

    Handles requests related to finding a specific user.

    :param get_user: implementation user get query.
    :param user_id: query param with user identifier.
    """
    user = await get_user(user_id=user_id)
    return schemas.UserGet.from_orm(user)


@router.post("", dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])])
async def create(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.UserCreate = fastapi.Body(...),
    list_groups: ports.ListGroupsWithoutOrg = fastapi_injector.Injected(
        ports.ListGroupsWithoutOrg
    ),
    list_organizations: ports.ListOrganizations = fastapi_injector.Injected(
        ports.ListOrganizations
    ),
    hash_ctx: context.CryptContext = fastapi_injector.Injected(context.CryptContext),
) -> schemas.UserGet:
    """
    Create user.

    Handles requests related to creating a specific user.

    :param uow_builder: implementation user get query.
    :param body: parsed data for user creation.
    """
    async with uow_builder() as uow:
        groups = await list_groups(
            groups=body.groups,
        )
        orgs, _ = await list_organizations(
            organizations=body.organizations,
            page_size=(
                len(body.organizations)
                if body.organizations is not None and len(body.organizations) > 0
                else 1
            ),
        )
        body_dict = body.dict()
        role = await uow.role_repository.get(role_id=body.role_id)
        user_model = await crud.create_user(
            body_dict=body_dict,
            role=role,
            hash_ctx=hash_ctx,
            groups=groups if body.groups is not None else None,
            organizations=orgs if body.organizations is not None else None,
        )
        await uow.user_repository.create(user_model)
        await uow.commit()

    return schemas.UserGet.from_orm(user_model)


@router.delete(
    "/{user_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def delete(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    user_id: uuid.UUID = fastapi.Path(...),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
) -> fastapi.Response:
    """
    Delete user.

    Handles requests related to deleting a specific user.

    :param uow_builder: implementation user get query.
    :param body: parsed data for user deletion.
    """
    current_user = await session_manager.get_current_session()
    if current_user.user_id == user_id:
        raise errors.CantDeleteYourself()
    async with uow_builder() as uow:
        user = await uow.user_repository.get(user_id)
        await uow.user_repository.delete(user)
        await uow.commit()

    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{user_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def update(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.UserPatch = fastapi.Body(...),
    user_id: uuid.UUID = fastapi.Path(...),
) -> schemas.UserGet:
    """
    Update a user.

    Handles requests related to updating a specific users.

    :param uow_builder: implementation user get query.
    :param user_id: query param with user identifier.
    :param body: parsed data for user patch.
    """
    body_dict = body.dict(exclude_unset=True)

    async with uow_builder() as uow:
        user = await uow.user_repository.get(user_id)
        group_list = []
        org_list = []
        if body.groups:
            group_ids = [group.id for group in user.groups]
            groups = [group for group in body.groups if group not in group_ids]
            if groups:
                group_list = await uow.group_repository.list(group_ids=groups)
        if body.organizations:
            org_ids = [organization.id for organization in user.organizations]
            organizations = [
                organization
                for organization in body.organizations
                if organization not in org_ids
            ]
            if organizations:
                org_list = await uow.organization_repository.list(
                    org_ids=organizations,
                )
        user = await crud.update_user(
            user, body_dict, group_list=group_list, org_list=org_list
        )

        await uow.commit()

    return schemas.UserGet.from_orm(user)


@router.put(
    "/batch",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def import_users_batch(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    storage: ports.Storage = fastapi_injector.Injected(ports.Storage),
    hash_ctx: context.CryptContext = fastapi_injector.Injected(context.CryptContext),
    body: ImportData = fastapi.Body(...),
) -> fastapi.Response:
    """
    Import users.

    Handles requests related to importing a specific users.

    :param session_factory: implementation of session factory.
    :param body: parsed data for user import.
    """

    user_ids, customer_ids, result = await data.handle_import(
        body.url, body.key_relation, storage
    )
    group_ids: list[uuid.UUID] = []
    org_ids: list[uuid.UUID] = []
    cached_role: dict[uuid.UUID, models.Role] = {}
    for v in result.values():
        for user in v:
            try:
                groups_raw = json.loads(user.get("groups", "").replace("'", '"'))
                orgs_raw = json.loads(user.get("organizations", "").replace("'", '"'))
            except (json.decoder.JSONDecodeError, AttributeError):
                user_groups_raw: str = user.get("groups", "")
                groups_raw = user_groups_raw.split(",") if user_groups_raw else []
                user_orgs_raw: str = user.get("organizations", "")
                orgs_raw = user_orgs_raw.split(",") if user_orgs_raw else []
            user["groups"] = [uuid.UUID(gp) for gp in groups_raw]
            user["organizations"] = [uuid.UUID(og) for og in orgs_raw]
            group_ids.extend(
                group_id for group_id in user["groups"] if group_id not in group_ids
            )
            org_ids.extend(
                org_id for org_id in user["organizations"] if org_id not in org_ids
            )
    async with uow_builder() as uow:
        orgs = await uow.organization_repository.list(org_ids=org_ids)
        groups = await uow.group_repository.list(group_ids=group_ids)
        user_list = await uow.user_repository.list(
            user_ids=user_ids, customer_ids=customer_ids
        )
        for user_tmp in user_list:
            if user_tmp.id in result:
                user_data = result.pop(user_tmp.id)[0]
            elif user_tmp.customer_id and user_tmp.customer_id in result:
                user_data = result.pop(user_tmp.customer_id)[0]
            await crud.update_user(
                user_tmp, schemas.UserPatch.parse_obj(user_data).dict(), groups, orgs
            )
        new_users = []
        for user_result in result.values():
            for user in user_result:
                user_groups = [
                    group for group in groups if group.id in user.get("groups", [])
                ]
                user_orgs = [
                    org for org in orgs if org.id in user.get("organizations", [])
                ]
                if "type" not in user:
                    user["type"] = "password" if user.get("password") else "firebase"
                user["external_id"] = None
                role_id = uuid.UUID(user.get("role", user["role_id"]))
                if not (role := cached_role.get(role_id)):
                    role = await uow.role_repository.get(role_id)
                    cached_role[role_id] = role
                new_users.append(
                    await crud.create_user(user, role, hash_ctx, user_groups, user_orgs)
                )
        await uow.add_all(new_users)
        await uow.commit()
    return fastapi.responses.JSONResponse(
        {}, status_code=fastapi.status.HTTP_201_CREATED
    )


############################ EXAM RELATED ENDPOINTS ############################


@router.get(
    "/{user_id}/exams",
    dependencies=[
        fastapi.Security(
            auth.get_token, scopes=["user", "user.impersonate", "user.list"]
        )
    ],
)
async def list_exams_to_process(
    user_id: uuid.UUID = fastapi.Path(...),
    list_data: ListSchema = fastapi.Depends(),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    list_pending: ports.ListPendingExams = fastapi_injector.Injected(
        ports.ListPendingExams
    ),
    list_personifiable: ports.ListPersonifiableUsers = fastapi_injector.Injected(
        ports.ListPersonifiableUsers
    ),
) -> schemas.ExamWithStatusList:
    """
    List exams.

    Handles requests related to exams being listed.

    :param list_exams: implementation of orgs list.
    """
    session = await session_manager.get_current_session()
    scopes = session.user.role.scopes
    if "user" in scopes and user_id == session.user_id:
        if not session.user.groups:
            raise errors.NotFound("group")
        group_id = session.user.groups[0].id
    elif "user.impersonate" in scopes or "user.list" in scopes:
        impersonate_list = await list_personifiable(
            groups=[group.id for group in session.user.groups]
        )
        if not (
            user_tb_imp := next(
                user_imp for user_imp in impersonate_list if user_imp.id == user_id
            )
        ):
            raise errors.Forbidden()
        group_id = user_tb_imp.groups[0].id
    else:
        raise errors.Forbidden()

    result, pagination_metadata = await list_pending(
        user_id=user_id,
        group_id=group_id,
        page_size=list_data.page_size,
        page=list_data.page,
    )

    return schemas.ExamWithStatusList(
        items=[
            schemas.ExamWithStatus.construct(
                id=exam.id,
                name=exam.name,
                start_date=exam.start_date,
                end_date=exam.end_date,
                status=status,
            )
            for exam, status in result
        ],
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get(
    "/{user_id}/exams-results",
    dependencies=[
        fastapi.Security(auth.get_token, scopes=["user.impersonate", "user.list"])
    ],
)
async def list_exams_with_results(
    user_id: uuid.UUID = fastapi.Path(...),
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    exams_with_result: ports.ListExamsWithResults = fastapi_injector.Injected(
        ports.ListExamsWithResults
    ),
    list_personifiable: ports.ListPersonifiableUsers = fastapi_injector.Injected(
        ports.ListPersonifiableUsers
    ),
) -> list[exam_schemas.Exam]:
    """
    List exams results.

    Handles requests related to exams being listed.

    :param list_exams: implementation of orgs list.
    """
    session = await session_manager.get_current_session()
    scopes = session.user.role.scopes
    if "user" in scopes and user_id == session.user_id:
        if not session.user.groups:
            raise errors.NotFound("group")
        group_id = session.user.groups[0].id
    elif "user.impersonate" in scopes or "user.list" in scopes:
        impersonate_list = await list_personifiable(
            groups=[group.id for group in session.user.groups]
        )
        if not (
            user_tb_imp := next(
                user_imp for user_imp in impersonate_list if user_imp.id == user_id
            )
        ):
            raise errors.Forbidden()
        group_id = user_tb_imp.groups[0].id
    else:
        raise errors.Forbidden()

    result = await exams_with_result(
        user_id=user_id,
        group_id=group_id,
    )

    return [exam_schemas.Exam.from_orm(exam) for exam in result]


@router.get(
    "/{user_id}/exams/{exam_id}/questions",
    dependencies=[
        fastapi.Security(auth.get_token, scopes=["user", "user.impersonate"])
    ],
)
async def get_questions(
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    user_id: uuid.UUID = fastapi.Path(...),
    exam_id: uuid.UUID = fastapi.Path(...),
    list_questions: ports.ListQuestionsWithStatus = fastapi_injector.Injected(
        ports.ListQuestionsWithStatus
    ),
    list_personifiable: ports.ListPersonifiableUsers = fastapi_injector.Injected(
        ports.ListPersonifiableUsers
    ),
) -> list[exam_schemas.QuestionList]:
    """
    List pending questions.

    Handles requests related to questions being listed.

    :param list_questions: implementation of questions list.
    """
    session = await session_manager.get_current_session()
    scopes = session.user.role.scopes
    if "user" in scopes and user_id == session.user_id:
        if not session.user.groups:
            raise errors.NotFound("group")
        group_id = session.user.groups[0].id
    elif "user.impersonate" in scopes:
        impersonate_list = await list_personifiable(
            groups=[group.id for group in session.user.groups]
        )
        if not (
            user_tb_imp := next(
                user_imp for user_imp in impersonate_list if user_imp.id == user_id
            )
        ):
            raise errors.Forbidden()
        group_id = user_tb_imp.groups[0].id
    else:
        raise errors.Forbidden()
    results = await list_questions(user_id, group_id, exam_id)
    return [
        exam_schemas.QuestionList(
            id=question.id,
            data=question.data,
            formatted_data=question.formatted_data,
            name=question.name,
            type=question.type,
            status=(
                question_status.status
                if question_status
                else models.ExamStatus.NOT_STARTED
            ),
            order=question.order,
        )
        for question, question_status in results
    ]


@router.post(
    "/{user_id}/exams/{exam_id}/questions/{question_id}",
    dependencies=[
        fastapi.Security(auth.get_token, scopes=["user", "user.impersonate"])
    ],
)
async def send_question_data(
    session_manager: sess_mg.SessionManager = fastapi.Depends(
        dependencies.get_session_manager
    ),
    user_id: uuid.UUID = fastapi.Path(...),
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
    body: exam_schemas.QuestionPost = fastapi.Body(...),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
    list_personifiable: ports.ListPersonifiableUsers = fastapi_injector.Injected(
        ports.ListPersonifiableUsers
    ),
) -> fastapi.Response:
    """
    Answer a pending question.

    Handles requests related to questions being listed.

    :param list_pending_questions: implementation of questions list.
    """
    user_session = await session_manager.get_current_session()
    scopes = user_session.user.role.scopes
    if "user" in scopes and user_id == user_session.user_id:
        if not user_session.user.groups:
            raise errors.NotFound("group")
        group_id = user_session.user.groups[0].id
        organization_id = user_session.user.organizations[0].id
    elif "user.impersonate" in scopes:
        impersonate_list = await list_personifiable(
            groups=[group.id for group in user_session.user.groups]
        )
        if not (
            user_tb_imp := next(
                user_imp for user_imp in impersonate_list if user_imp.id == user_id
            )
        ):
            raise errors.Forbidden()
        group_id = user_tb_imp.groups[0].id
        organization_id = user_tb_imp.organizations[0].id
    else:
        raise errors.Forbidden()
    async with session_factory() as session:
        question_data = await get_pending(user_id, group_id, exam_id, question_id)
        if not question_data:
            raise fastapi.HTTPException(
                status_code=400,
                detail="You already finished this exam/question",
            )

        if not await get_exam_user(user_id=user_id, exam_id=exam_id, group_id=group_id):
            exam_user = models.ExamUser(
                exam_id=exam_id,
                user_id=user_id,
                status=models.ExamStatus.IN_PROGRESS,
            )
            session.add(exam_user)

        exam_user_question = models.ExamUserQuestion(
            exam_id=exam_id,
            user_id=user_id,
            question_id=question_id,
            group_id=group_id,
            organization_id=organization_id,
            result=[],
            right_count=0,
            audio_url="",
            total_accuracy=0.0,
            user_accuracy=0.0,
        )
        session.add(exam_user_question)

        text_list = re.sub(
            r"\s+", " ", re.sub(r"[\[\]\.,\(\)!-\?]", "", question_data.data)
        ).split(" ")

        await publisher.publish(
            exam_schemas.QuestionMessage(
                result_id=exam_user_question.id,
                phrase_set_id=question_data.phrase_id,
                audio=body.url,
                words=text_list,
                question_type=question_data.type.value,
            ),
            topic=settings.get("pubsub_convert_topic"),
        )
        await session.commit()
    return fastapi.Response(status_code=fastapi.status.HTTP_201_CREATED)
