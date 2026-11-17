"""Integration & regression tests for IDOR protection on
GET /api/v1/exams/{exam_id}/users/{user_id}.
"""

from __future__ import annotations

import datetime
import typing
import uuid

import pytest
import sqlalchemy as sa
from api import models
from api.typings import SessionFactory
from httpx import AsyncClient
from passlib import context

if typing.TYPE_CHECKING:
    from tests.conftest import MockGenAI, MockStorage


async def _get_or_create_series(
    session_factory: SessionFactory, grade: models.Grades
) -> models.Series:
    async with session_factory() as session:
        existing = (
            await session.execute(
                sa.select(models.Series).where(models.Series.name == grade.value)
            )
        ).scalar_one_or_none()
        if existing:
            return existing
        series = models.Series(
            name=grade.value,
            code=f"S{uuid.uuid4().hex[:8]}",
        )
        session.add(series)
        await session.commit()
        return series


async def _get_or_create_shift(session_factory: SessionFactory) -> models.WorkShift:
    async with session_factory() as session:
        existing = (
            await session.execute(
                sa.select(models.WorkShift).where(models.WorkShift.name == "Manhã")
            )
        ).scalar_one_or_none()
        if existing:
            return existing
        shift = models.WorkShift(name="Manhã", code="MORNING")
        session.add(shift)
        await session.commit()
        return shift


async def _create_org_and_group(
    session_factory: SessionFactory,
    grade: models.Grades = models.Grades.FIRST_FUND,
    *,
    label: str = "tenant",
) -> tuple[models.Organization, models.Group]:
    series = await _get_or_create_series(session_factory, grade)
    shift = await _get_or_create_shift(session_factory)
    suffix = uuid.uuid4().hex[:8]
    org = models.Organization(
        customer_id=None,
        name=f"Org-{label}-{suffix}",
        region="Sul",
        city="Curitiba",
        state="PR",
    )
    async with session_factory() as session:
        session.add(org)
        await session.flush()
        group = models.Group(
            name=f"Group-{label}-{suffix}",
            customer_id=None,
            organization_id=org.id,
            series_id=series.id,
            shift_id=shift.id,
        )
        session.add(group)
        await session.commit()
    return org, group


async def _create_user_with_scopes(
    session_factory: SessionFactory,
    scopes: list[str],
    *,
    groups: list[models.Group] | None = None,
    organizations: list[models.Organization] | None = None,
    name: str = "Test User",
) -> tuple[models.User, str, models.Role]:
    role = models.Role(
        name=f"role-{uuid.uuid4()}",
        display_name={"en-US": "Role"},
        description={"en-US": "Role"},
        scopes=scopes,
    )
    email = f"user-{uuid.uuid4()}@example.com"
    password = "Password123!"
    hash_ctx = context.CryptContext(schemes=["bcrypt"], deprecated="auto")

    async with session_factory() as session:
        session.add(role)
        await session.flush()

        user = models.User(
            external_id=None,
            customer_id=None,
            type=models.UserType.PASSWORD,
            role_id=role.id,
            name=name,
            email_address=email,
            state="PR",
            region="Sul",
        )
        user.set_password(password, hash_ctx)
        session.add(user)
        await session.flush()

        for group in groups or []:
            session.add(models.UserGroup(user_id=user.id, group_id=group.id))
        for org in organizations or []:
            session.add(
                models.UserOrganization(user_id=user.id, organization_id=org.id)
            )
        await session.commit()

    return user, password, role


async def _create_exam_with_result(
    session_factory: SessionFactory,
    *,
    student: models.User,
    org: models.Organization,
    group: models.Group,
    grade: models.Grades = models.Grades.FIRST_FUND,
    question_count: int = 1,
    ai_exam_feedback: str | None = None,
    transcript_words: list[str] | None = None,
) -> tuple[models.Exam, list[models.Question]]:
    now = datetime.datetime.now(tz=datetime.UTC)
    questions = [
        models.Question(
            name=f"Question {idx}",
            type=models.QuestionType.WORDS,
            theme=None,
            phrase_id=f"phrase-{uuid.uuid4()}",
            data="casa bola pato",
            formatted_data="casa bola pato",
            order=idx,
            answers=[],
        )
        for idx in range(1, question_count + 1)
    ]
    exam = models.Exam(
        name=f"Exam-{uuid.uuid4().hex[:8]}",
        start_date=now - datetime.timedelta(days=1),
        end_date=now + datetime.timedelta(days=7),
        grade=grade,
        questions=questions,
    )
    spoken = transcript_words if transcript_words is not None else ["casa", "bola"]

    async with session_factory() as session:
        session.add(exam)
        await session.flush()

        exam_user = models.ExamUser(
            exam_id=exam.id,
            user_id=student.id,
            status=models.ExamStatus.FINISHED,
            user_rating=models.UserRating.READER,
            ai_exam_feedback=ai_exam_feedback,
        )
        session.add(exam_user)

        for question in exam.questions:
            euq = models.ExamUserQuestion(
                user_id=student.id,
                exam_id=exam.id,
                question_id=question.id,
                group_id=group.id,
                organization_id=org.id,
                result=spoken,
                right_count=len(spoken),
                user_accuracy=1.0,
                total_accuracy=0.67,
                audio_url=(
                    f"https://storage.cloud.google.com/test-bucket/"
                    f"{org.id}/{group.id}/{exam.id}|{question.id}|{student.id}.wav"
                ),
                ai_feedback="Private reading assessment",
                ai_is_correct=True,
            )
            euq.status = models.ExamStatus.FINISHED
            session.add(euq)

        await session.commit()

    return exam, questions


async def _login(
    client: AsyncClient, email: str, password: str
) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/token",
        json={"email_address": email, "password": password},
    )
    assert resp.status_code == 200
    data: dict[str, str] = resp.json()
    return data


@pytest.mark.asyncio
async def test_student_cannot_read_another_students_exam_different_tenant(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """IDOR: a student in School A must not read a student's exam in School B,
    mint their signed audio URL, or trigger Gemini exam feedback.
    """
    org_a, group_a = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="school-a"
    )
    org_b, group_b = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="school-b"
    )
    attacker, attacker_pw, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group_a],
        organizations=[org_a],
        name="Attacker Student",
    )
    victim, _, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group_b],
        organizations=[org_b],
        name="Victim Student",
    )
    exam, _ = await _create_exam_with_result(
        session_factory,
        student=victim,
        org=org_b,
        group=group_b,
        grade=models.Grades.FIRST_FUND,
        ai_exam_feedback=None,
        transcript_words=["secret-transcript"],
    )

    tokens = await _login(unauthenticated_client, attacker.email_address, attacker_pw)
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{victim.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []

    async with session_factory() as session:
        victim_exam_user = (
            await session.execute(
                sa.select(models.ExamUser).where(
                    models.ExamUser.exam_id == exam.id,
                    models.ExamUser.user_id == victim.id,
                )
            )
        ).scalar_one()
    assert victim_exam_user.ai_exam_feedback is None


@pytest.mark.asyncio
async def test_student_cannot_read_classmates_exam_same_group(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """IDOR: even within the same group, a student must not read another
    student's exam.
    """
    org, group = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="shared-class"
    )
    attacker, attacker_pw, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
        name="Classmate Attacker",
    )
    victim, _, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
        name="Classmate Victim",
    )
    exam, _ = await _create_exam_with_result(
        session_factory,
        student=victim,
        org=org,
        group=group,
        grade=models.Grades.FIRST_FUND,
        ai_exam_feedback=None,
    )

    tokens = await _login(unauthenticated_client, attacker.email_address, attacker_pw)
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{victim.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []


@pytest.mark.asyncio
async def test_student_cannot_read_exam_outside_their_group_grade(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """A student calling with their own user_id must not access an exam whose
    grade does not match any of their groups (nor trigger Gemini/signed URLs).
    """
    org, group_first = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="grade-1"
    )
    student, password, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group_first],
        organizations=[org],
        name="First Grade Student",
    )
    exam_second_grade, _ = await _create_exam_with_result(
        session_factory,
        student=student,
        org=org,
        group=group_first,
        grade=models.Grades.SECOND_FUND,
        ai_exam_feedback=None,
    )

    tokens = await _login(unauthenticated_client, student.email_address, password)
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam_second_grade.id}/users/{student.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 404
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []


@pytest.mark.asyncio
async def test_student_cannot_read_submission_recorded_in_unassigned_group(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """A student must not access an exam submission recorded under a group
    they do not belong to.
    """
    org_a, group_a = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="assigned-group"
    )
    org_b, group_b = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="other-group"
    )
    student, password, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group_a],
        organizations=[org_a],
        name="Student A",
    )
    exam, _ = await _create_exam_with_result(
        session_factory,
        student=student,
        org=org_b,
        group=group_b,
        grade=models.Grades.FIRST_FUND,
        ai_exam_feedback=None,
    )

    tokens = await _login(unauthenticated_client, student.email_address, password)
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{student.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 404
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []


@pytest.mark.asyncio
async def test_student_with_no_groups_is_rejected(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """Fail closed when a user-scoped caller has no assigned groups."""
    org, group = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="orphan-exam"
    )
    student, password, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[],
        organizations=[],
        name="No Group Student",
    )
    exam, _ = await _create_exam_with_result(
        session_factory,
        student=student,
        org=org,
        group=group,
        grade=models.Grades.FIRST_FUND,
        ai_exam_feedback=None,
    )

    tokens = await _login(unauthenticated_client, student.email_address, password)
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{student.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []


@pytest.mark.asyncio
async def test_professor_cannot_read_student_exam_in_different_tenant(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """Cross-tenant IDOR: an exam.list caller in School A must not read a student's
    exam results from School B, even for the same grade/exam.
    """
    org_a, group_a = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="prof-school-a"
    )
    org_b, group_b = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="victim-school-b"
    )
    professor, prof_pw, _ = await _create_user_with_scopes(
        session_factory,
        scopes=[
            "dashboard.viewer",
            "user.impersonate",
            "user.list",
            "group.list",
            "exam.list",
        ],
        groups=[group_a],
        organizations=[org_a],
        name="Professor School A",
    )
    victim, _, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group_b],
        organizations=[org_b],
        name="Student School B",
    )
    exam, _ = await _create_exam_with_result(
        session_factory,
        student=victim,
        org=org_b,
        group=group_b,
        grade=models.Grades.FIRST_FUND,
        ai_exam_feedback=None,
    )

    tokens = await _login(unauthenticated_client, professor.email_address, prof_pw)
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{victim.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []


@pytest.mark.asyncio
async def test_professor_nonexistent_user_returns_same_403_no_oracle(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """Professor querying an unknown user_id receives 403
    (same as out-of-tenant user).
    """
    org, group = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="prof-oracle"
    )
    professor, prof_pw, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["exam.list"],
        groups=[group],
        organizations=[org],
        name="Professor Oracle",
    )

    tokens = await _login(unauthenticated_client, professor.email_address, prof_pw)
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{uuid.uuid4()}/users/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []


@pytest.mark.asyncio
async def test_professor_with_no_groups_is_rejected(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """Fail closed when an exam.list caller has no assigned groups."""
    org, group = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="prof-no-groups"
    )
    professor, prof_pw, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["exam.list"],
        groups=[],
        organizations=[],
        name="Unassigned Professor",
    )
    student, _, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
        name="Assigned Student",
    )
    exam, _ = await _create_exam_with_result(
        session_factory,
        student=student,
        org=org,
        group=group,
        grade=models.Grades.FIRST_FUND,
        ai_exam_feedback=None,
    )

    tokens = await _login(unauthenticated_client, professor.email_address, prof_pw)
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{student.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []


@pytest.mark.asyncio
async def test_professor_cannot_read_student_exam_outside_shared_group(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """Professor sharing Group A (1st grade) with a student must not read that
    student's submission from another school/group (Group B) they do not share.
    """
    org_a, group_a = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="shared-a"
    )
    org_b, group_b = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="unshared-b"
    )
    professor, prof_pw, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["exam.list"],
        groups=[group_a],
        organizations=[org_a],
        name="Professor A",
    )
    student, _, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group_a, group_b],
        organizations=[org_a, org_b],
        name="Dual-School Student",
    )
    exam_in_b, _ = await _create_exam_with_result(
        session_factory,
        student=student,
        org=org_b,
        group=group_b,
        grade=models.Grades.FIRST_FUND,
        ai_exam_feedback=None,
    )

    tokens = await _login(unauthenticated_client, professor.email_address, prof_pw)
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam_in_b.id}/users/{student.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 404
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []


@pytest.mark.asyncio
async def test_live_db_role_downgrade_rejects_stale_jwt(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """If a caller's DB role is downgraded after token issuance,
    live role check denies access.
    """
    org, group = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="downgrade"
    )
    student, password, role = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
        name="Downgraded User",
    )
    exam, _ = await _create_exam_with_result(
        session_factory,
        student=student,
        org=org,
        group=group,
        grade=models.Grades.FIRST_FUND,
        ai_exam_feedback=None,
    )

    tokens = await _login(unauthenticated_client, student.email_address, password)

    async with session_factory() as session:
        db_role = (
            await session.execute(
                sa.select(models.Role).where(models.Role.id == role.id)
            )
        ).scalar_one()
        db_role.scopes = ["dashboard.viewer"]
        await session.commit()

    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{student.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []


@pytest.mark.asyncio
async def test_unauthenticated_wrong_scope_and_revoked_session_rejected(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """Missing auth -> 403; invalid JWT / wrong scope / revoked session -> 401."""
    exam_id = uuid.uuid4()
    user_id = uuid.uuid4()

    no_auth = await unauthenticated_client.get(
        f"/api/v1/exams/{exam_id}/users/{user_id}"
    )
    assert no_auth.status_code == 403

    bad_jwt = await unauthenticated_client.get(
        f"/api/v1/exams/{exam_id}/users/{user_id}",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert bad_jwt.status_code == 401

    viewer, viewer_pw, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["dashboard.viewer"],
        name="Dashboard Only",
    )
    viewer_tokens = await _login(
        unauthenticated_client, viewer.email_address, viewer_pw
    )
    wrong_scope = await unauthenticated_client.get(
        f"/api/v1/exams/{exam_id}/users/{viewer.id}",
        headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"},
    )
    assert wrong_scope.status_code == 401

    org, group = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="revoked"
    )
    student, student_pw, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
        name="Revoked Student",
    )
    student_tokens = await _login(
        unauthenticated_client, student.email_address, student_pw
    )
    async with session_factory() as session:
        await session.execute(
            sa.delete(models.Session).where(models.Session.user_id == student.id)
        )
        await session.commit()

    revoked_resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam_id}/users/{student.id}",
        headers={"Authorization": f"Bearer {student_tokens['access_token']}"},
    )
    assert revoked_resp.status_code == 401
    assert mock_storage.signed_url_calls == []
    assert mock_gen_ai.exam_feedback_calls == []


@pytest.mark.asyncio
async def test_student_can_read_own_exam_in_own_group(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """Happy path: a student can read their own exam belonging to their group,
    receives a signed GET URL for audio, and generates + persists AI feedback once.
    """
    org, group = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="happy-student"
    )
    student, password, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
        name="Happy Student",
    )
    exam, _ = await _create_exam_with_result(
        session_factory,
        student=student,
        org=org,
        group=group,
        grade=models.Grades.FIRST_FUND,
        question_count=2,
        ai_exam_feedback=None,
        transcript_words=["casa", "bola"],
    )

    tokens = await _login(unauthenticated_client, student.email_address, password)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    first_resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{student.id}",
        headers=headers,
    )
    assert first_resp.status_code == 200
    body = first_resp.json()
    assert body["id"] == str(exam.id)
    assert body["ai_exam_feedback"] == "feedback"
    assert len(body["questions"]) == 2
    assert [q["order"] for q in body["questions"]] == [1, 2]
    assert body["questions"][0]["response"]["result"] == ["casa", "bola"]
    assert body["questions"][0]["response"]["audio_url"].endswith("?signed=true")
    assert len(mock_storage.signed_url_calls) == 2
    assert all(method == "GET" for _, _, method in mock_storage.signed_url_calls)
    assert len(mock_gen_ai.exam_feedback_calls) == 1

    # Second read reuses persisted ai_exam_feedback without calling Gemini again.
    second_resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{student.id}",
        headers=headers,
    )
    assert second_resp.status_code == 200
    assert second_resp.json()["ai_exam_feedback"] == "feedback"
    assert len(mock_gen_ai.exam_feedback_calls) == 1


@pytest.mark.asyncio
async def test_professor_can_read_shared_group_exam_without_duplicate_questions(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_gen_ai: MockGenAI,
) -> None:
    """Happy path: a professor teaching multiple classes of the same grade can read
    their student's exam without duplicating questions in json_agg.
    """
    org, group_1 = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="prof-class-1"
    )
    _, group_2 = await _create_org_and_group(
        session_factory, models.Grades.FIRST_FUND, label="prof-class-2"
    )
    professor, prof_pw, _ = await _create_user_with_scopes(
        session_factory,
        scopes=[
            "dashboard.viewer",
            "user.impersonate",
            "user.list",
            "group.list",
            "exam.list",
        ],
        groups=[group_1, group_2],
        organizations=[org],
        name="Multi-Class Professor",
    )
    student, _, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group_1, group_2],
        organizations=[org],
        name="Class 1 Student",
    )
    exam, _ = await _create_exam_with_result(
        session_factory,
        student=student,
        org=org,
        group=group_1,
        grade=models.Grades.FIRST_FUND,
        question_count=2,
        ai_exam_feedback="Existing feedback",
    )

    tokens = await _login(unauthenticated_client, professor.email_address, prof_pw)
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{student.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(exam.id)
    assert body["ai_exam_feedback"] == "Existing feedback"
    assert len(body["questions"]) == 2
    assert [q["order"] for q in body["questions"]] == [1, 2]
    assert len(mock_storage.signed_url_calls) == 2
    assert mock_gen_ai.exam_feedback_calls == []
