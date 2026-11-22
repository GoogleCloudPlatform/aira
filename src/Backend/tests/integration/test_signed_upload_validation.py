"""Integration and regression tests for signed-upload URL validation on
POST /api/v1/processor/signed and defense-in-depth in CloudStorage / exam GET URLs.
"""

from __future__ import annotations

import datetime
import typing
import unittest.mock
import uuid

import pytest
import sqlalchemy as sa
from api import errors, models
from api.adapters.google import cloud_storage
from api.typings import SessionFactory
from httpx import AsyncClient
from passlib import context

if typing.TYPE_CHECKING:
    from tests.conftest import MockStorage


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
    *,
    label: str = "signed",
) -> tuple[models.Organization, models.Group]:
    series = await _get_or_create_series(session_factory, models.Grades.FIRST_FUND)
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
    name: str = "Signed Test User",
) -> tuple[models.User, str]:
    role = models.Role(
        name=f"role-{uuid.uuid4()}",
        display_name={"en-US": "Role"},
        description={"en-US": "Role"},
        scopes=scopes,
    )
    password = f"Pass!{uuid.uuid4().hex[:12]}"
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
            email_address=f"signed-{uuid.uuid4().hex[:10]}@example.com",
            state="PR",
            region="Sul",
        )
        user.set_password(password, hash_ctx)
        session.add(user)
        await session.flush()

        for org in organizations or []:
            session.add(
                models.UserOrganization(user_id=user.id, organization_id=org.id)
            )
        for grp in groups or []:
            session.add(models.UserGroup(user_id=user.id, group_id=grp.id))

        await session.commit()

    return user, password


async def _login_headers(
    client: AsyncClient, email: str, password: str
) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/token",
        json={"email_address": email, "password": password},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_student_signed_upload_rejects_unvalidated_file_type_and_mimetype(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
) -> None:
    """Guards against XSS Content-Type spoofing, path pollution, and MIME mismatches."""
    org, group = await _create_org_and_group(session_factory, label="xss")
    student, password = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
    )
    headers = await _login_headers(
        unauthenticated_client, student.email_address, password
    )

    rejected_cases = [
        # Stored XSS / active web content payloads
        ("html", "text/html"),
        ("htm", "text/html"),
        ("svg", "image/svg+xml"),
        ("js", "application/javascript"),
        ("wav", "text/html"),
        ("wav", "image/svg+xml"),
        ("webm", "text/html"),
        ("mp3", "application/xhtml+xml"),
        # Namespace pollution / path traversal / separators
        ("wav/../../import/USER/evil.csv", "audio/wav"),
        ("foo/bar", "audio/wav"),
        ("wav/nested.html", "audio/wav"),
        ("../evil", "audio/wav"),
        ("..wav", "audio/wav"),
        ("wav..html", "audio/wav"),
        ("wav\\evil", "audio/wav"),
        ("/wav", "audio/wav"),
        # Control characters and header/parameter injection
        ("wav\r\nX-Injected: 1", "audio/wav"),
        ("wav\n", "audio/wav"),
        ("wav\x00", "audio/wav"),
        ("wav\x7f", "audio/wav"),
        ("wav", "audio/wav\r\nX-Injected: 1"),
        ("wav", "audio/wav\x00"),
        ("wav", "audio/wav; charset=utf-8"),
        ("wav", "audio/.."),
        ("wav", "audio\\wav"),
        # Mismatched file_type and audio/* mimetype
        ("wav", "audio/ogg"),
        ("wav", "audio/webm"),
        ("wav", "audio/mpeg"),
        ("ogg", "audio/wav"),
        ("webm", "audio/mpeg"),
        ("mp3", "audio/wav"),
        ("mp3", "audio/webm"),
        # Disallowed extensions / casing / whitespace / non-audio types
        ("WAV", "audio/wav"),
        (" wav", "audio/wav"),
        ("wav ", "audio/wav"),
        ("wav", "AUDIO/WAV"),
        ("", "audio/wav"),
        ("wav", ""),
        ("mp4", "audio/mp4"),
        ("mp4", "video/mp4"),
        ("csv", "text/csv"),
        ("txt", "text/plain"),
        ("x-wav", "audio/x-wav"),
        ("mpeg", "audio/mpeg"),
    ]

    for file_type, mimetype in rejected_cases:
        resp = await unauthenticated_client.post(
            "/api/v1/processor/signed",
            headers=headers,
            json={
                "exam_id": str(uuid.uuid4()),
                "question_id": str(uuid.uuid4()),
                "user_id": str(student.id),
                "file_type": file_type,
                "mimetype": mimetype,
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for file_type={file_type!r}, mimetype={mimetype!r}; "
            f"got {resp.status_code}: {resp.text}"
        )

    # Reject mixed schema fields (extra=forbid)
    mixed_resp = await unauthenticated_client.post(
        "/api/v1/processor/signed",
        headers=headers,
        json={
            "exam_id": str(uuid.uuid4()),
            "question_id": str(uuid.uuid4()),
            "user_id": str(student.id),
            "type": "USER",
            "file_type": "wav",
            "mimetype": "audio/wav",
        },
    )
    assert mixed_resp.status_code == 422
    assert mock_storage.signed_url_calls == []


@pytest.mark.asyncio
async def test_student_signed_upload_accepts_allowlisted_audio_pairs(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
) -> None:
    org, group = await _create_org_and_group(session_factory, label="valid-audio")
    student, password = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
    )
    headers = await _login_headers(
        unauthenticated_client, student.email_address, password
    )

    valid_pairs = [
        ("wav", "audio/wav"),
        ("wav", "audio/x-wav"),
        ("ogg", "audio/ogg"),
        ("webm", "audio/webm"),
        ("mp3", "audio/mpeg"),
        ("mp3", "audio/mp3"),
    ]
    expected_calls: list[tuple[str, str, str]] = []

    for file_type, mimetype in valid_pairs:
        exam_id = uuid.uuid4()
        question_id = uuid.uuid4()
        resp = await unauthenticated_client.post(
            "/api/v1/processor/signed",
            headers=headers,
            json={
                "exam_id": str(exam_id),
                "question_id": str(question_id),
                "user_id": str(student.id),
                "file_type": file_type,
                "mimetype": mimetype,
            },
        )
        assert resp.status_code == 200, resp.text
        expected_calls.append(
            (
                f"{org.id}/{group.id}/{exam_id}|{question_id}|{student.id}.{file_type}",
                mimetype,
                "PUT",
            )
        )

    assert mock_storage.signed_url_calls == expected_calls


@pytest.mark.asyncio
async def test_signed_upload_auth_and_impersonation_boundaries(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
) -> None:
    # Unauthenticated call fails closed
    unauth_resp = await unauthenticated_client.post(
        "/api/v1/processor/signed",
        json={
            "exam_id": str(uuid.uuid4()),
            "question_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "file_type": "wav",
            "mimetype": "audio/wav",
        },
    )
    assert unauth_resp.status_code == 403

    org, group = await _create_org_and_group(session_factory, label="impersonate")
    student, student_pw = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
        name="Student",
    )
    professor, prof_password = await _create_user_with_scopes(
        session_factory,
        scopes=["user.impersonate"],
        groups=[group],
        organizations=[org],
        name="Professor",
    )

    # Student cannot sign for another user_id
    student_headers = await _login_headers(
        unauthenticated_client, student.email_address, student_pw
    )
    other_user_resp = await unauthenticated_client.post(
        "/api/v1/processor/signed",
        headers=student_headers,
        json={
            "exam_id": str(uuid.uuid4()),
            "question_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "file_type": "wav",
            "mimetype": "audio/wav",
        },
    )
    assert other_user_resp.status_code == 403
    assert mock_storage.signed_url_calls == []

    # Impersonating professor rejects HTML/XSS and accepts allowlisted audio
    prof_headers = await _login_headers(
        unauthenticated_client, professor.email_address, prof_password
    )
    exam_id = uuid.uuid4()
    question_id = uuid.uuid4()

    bad_resp = await unauthenticated_client.post(
        "/api/v1/processor/signed",
        headers=prof_headers,
        json={
            "exam_id": str(exam_id),
            "question_id": str(question_id),
            "user_id": str(student.id),
            "file_type": "html",
            "mimetype": "text/html",
        },
    )
    assert bad_resp.status_code == 422
    assert mock_storage.signed_url_calls == []

    ok_resp = await unauthenticated_client.post(
        "/api/v1/processor/signed",
        headers=prof_headers,
        json={
            "exam_id": str(exam_id),
            "question_id": str(question_id),
            "user_id": str(student.id),
            "file_type": "webm",
            "mimetype": "audio/webm",
        },
    )
    assert ok_resp.status_code == 200
    expected_path = f"{org.id}/{group.id}/{exam_id}|{question_id}|{student.id}.webm"
    assert mock_storage.signed_url_calls == [(expected_path, "audio/webm", "PUT")]


@pytest.mark.asyncio
async def test_admin_import_signed_upload_validation_and_rbac(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
) -> None:
    org, group = await _create_org_and_group(session_factory, label="import-acl")
    student, student_pw = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
    )
    admin, admin_pw = await _create_user_with_scopes(
        session_factory,
        scopes=["admin"],
        name="Admin",
    )

    # Student cannot mint admin import URLs even with valid CSV payload
    student_headers = await _login_headers(
        unauthenticated_client, student.email_address, student_pw
    )
    student_resp = await unauthenticated_client.post(
        "/api/v1/processor/signed",
        headers=student_headers,
        json={
            "type": "USER",
            "file_type": "csv",
            "mimetype": "text/csv",
        },
    )
    assert student_resp.status_code == 403
    assert mock_storage.signed_url_calls == []

    admin_headers = await _login_headers(
        unauthenticated_client, admin.email_address, admin_pw
    )
    for bad_ext, bad_mime in [
        ("html", "text/html"),
        ("svg", "image/svg+xml"),
        ("csv", "text/html"),
        ("csv/../../evil", "text/csv"),
        ("..csv", "text/csv"),
        ("csv\r\n", "text/csv"),
        ("csv", "text/csv\r\n"),
        ("wav", "audio/wav"),
    ]:
        bad_resp = await unauthenticated_client.post(
            "/api/v1/processor/signed",
            headers=admin_headers,
            json={
                "type": "USER",
                "file_type": bad_ext,
                "mimetype": bad_mime,
            },
        )
        assert bad_resp.status_code == 422, (
            f"Expected 422 for import file_type={bad_ext!r}, mimetype={bad_mime!r}"
        )
    assert mock_storage.signed_url_calls == []

    # Admin with valid csv + text/csv succeeds
    admin_resp = await unauthenticated_client.post(
        "/api/v1/processor/signed",
        headers=admin_headers,
        json={
            "type": "USER",
            "file_type": "csv",
            "mimetype": "text/csv",
        },
    )
    assert admin_resp.status_code == 200
    assert len(mock_storage.signed_url_calls) == 1
    path, mimetype, method = mock_storage.signed_url_calls[0]
    assert path.startswith("import/USER/")
    assert path.endswith(".csv")
    assert mimetype == "text/csv"
    assert method == "PUT"


@pytest.mark.asyncio
async def test_exam_details_signed_get_url_sets_safe_attachment_headers(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
) -> None:
    """Defense-in-depth: signed GET URLs returned to teachers force attachment
    disposition and a safe audio/octet-stream Content-Type override so even legacy
    poisoned objects (.html/.svg) cannot render active content in a browser.
    """
    org, group = await _create_org_and_group(session_factory, label="get-headers")
    student, _ = await _create_user_with_scopes(
        session_factory,
        scopes=["user"],
        groups=[group],
        organizations=[org],
        name="Student",
    )
    professor, prof_pw = await _create_user_with_scopes(
        session_factory,
        scopes=["exam.list"],
        groups=[group],
        organizations=[org],
        name="Teacher",
    )

    now = datetime.datetime.now(datetime.UTC)
    exam = models.Exam(
        name=f"Exam-{uuid.uuid4().hex[:8]}",
        grade=models.Grades.FIRST_FUND,
        start_date=now - datetime.timedelta(days=1),
        end_date=now + datetime.timedelta(days=1),
        questions=[
            models.Question(
                name="Q1",
                data="casa bola",
                formatted_data="casa bola",
                phrase_id="p1",
                type=models.QuestionType.WORDS,
                order=1,
                answers=[],
                theme=None,
            ),
            models.Question(
                name="Q2",
                data="pato gato",
                formatted_data="pato gato",
                phrase_id="p2",
                type=models.QuestionType.WORDS,
                order=2,
                answers=[],
                theme=None,
            ),
        ],
    )
    async with session_factory() as session:
        session.add(exam)
        await session.flush()
        exam_user = models.ExamUser(
            exam_id=exam.id,
            user_id=student.id,
            status=models.ExamStatus.FINISHED,
            user_rating=models.UserRating.READER,
            ai_exam_feedback="cached",
        )
        session.add(exam_user)
        euq_wav = models.ExamUserQuestion(
            user_id=student.id,
            exam_id=exam.id,
            question_id=exam.questions[0].id,
            group_id=group.id,
            organization_id=org.id,
            result=["casa"],
            right_count=1,
            user_accuracy=1.0,
            total_accuracy=0.5,
            audio_url=(
                f"https://storage.cloud.google.com/test-bucket/"
                f"{org.id}/{group.id}/{exam.id}|{exam.questions[0].id}|{student.id}.wav"
            ),
            ai_feedback="ok",
            ai_is_correct=True,
        )
        euq_wav.status = models.ExamStatus.FINISHED
        euq_legacy_html = models.ExamUserQuestion(
            user_id=student.id,
            exam_id=exam.id,
            question_id=exam.questions[1].id,
            group_id=group.id,
            organization_id=org.id,
            result=["pato"],
            right_count=1,
            user_accuracy=1.0,
            total_accuracy=0.5,
            audio_url=(
                f"https://storage.cloud.google.com/test-bucket/"
                f"{org.id}/{group.id}/{exam.id}|{exam.questions[1].id}|{student.id}.html"
            ),
            ai_feedback="ok",
            ai_is_correct=True,
        )
        euq_legacy_html.status = models.ExamStatus.FINISHED
        session.add(euq_wav)
        session.add(euq_legacy_html)
        await session.commit()

    headers = await _login_headers(
        unauthenticated_client, professor.email_address, prof_pw
    )
    resp = await unauthenticated_client.get(
        f"/api/v1/exams/{exam.id}/users/{student.id}",
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(mock_storage.signed_url_calls) == 2
    options_by_path = {
        call[0]: opts
        for call, opts in zip(
            mock_storage.signed_url_calls, mock_storage.signed_url_options, strict=True
        )
    }
    wav_opts = next(v for k, v in options_by_path.items() if k.endswith(".wav"))
    html_opts = next(v for k, v in options_by_path.items() if k.endswith(".html"))
    assert wav_opts == {
        "response_disposition": "attachment",
        "response_type": "audio/wav",
    }
    assert html_opts == {
        "response_disposition": "attachment",
        "response_type": "application/octet-stream",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "mimetype", "method", "response_disposition", "response_type"),
    [
        ("../evil.wav", "audio/wav", "PUT", None, None),
        ("org/group/../../evil.wav", "audio/wav", "PUT", None, None),
        ("/leading/slash.wav", "audio/wav", "PUT", None, None),
        ("trailing/slash/", "audio/wav", "PUT", None, None),
        ("org//empty.wav", "audio/wav", "PUT", None, None),
        ("org\\back\\slash.wav", "audio/wav", "PUT", None, None),
        ("org/group/file\r\n.wav", "audio/wav", "PUT", None, None),
        ("org/group/file\x00.wav", "audio/wav", "PUT", None, None),
        ("", "audio/wav", "PUT", None, None),
        ("org/group/file.wav", "", "PUT", None, None),
        ("org/group/file.wav", "audio/wav\r\nX: 1", "PUT", None, None),
        ("org/group/file.wav", "audio/wav; charset=utf-8", "PUT", None, None),
        ("org/group/file.wav", "audio/..", "PUT", None, None),
        ("org/group/file.wav", "", "GET", "attachment\r\nX: 1", None),
        ("org/group/file.wav", "", "GET", "attachment", "text/html\r\n"),
    ],
)
async def test_cloud_storage_generate_signed_url_rejects_unsafe_inputs(
    path: str,
    mimetype: str,
    method: str,
    response_disposition: str | None,
    response_type: str | None,
) -> None:
    """Defense-in-depth at CloudStorage.generate_signed_url adapter."""
    with unittest.mock.patch(
        "api.adapters.google.cloud_storage.storage.Client"
    ) as mock_client_cls:
        adapter = cloud_storage.CloudStorage(
            project_id="test-project",
            storage_path="test-bucket",
            creds_path="",
        )
        with pytest.raises(errors.InvalidField):
            await adapter.generate_signed_url(
                path,
                mimetype,
                method=method,
                response_disposition=response_disposition,
                response_type=response_type,
            )
        mock_client_cls.return_value.bucket.return_value.blob.assert_not_called()


@pytest.mark.asyncio
async def test_cloud_storage_generate_signed_url_forwards_get_safety_headers() -> None:
    with unittest.mock.patch(
        "api.adapters.google.cloud_storage.storage.Client"
    ) as mock_client_cls:
        mock_blob = mock_client_cls.return_value.bucket.return_value.blob.return_value
        mock_blob.generate_signed_url.return_value = (
            "https://storage.googleapis.com/b/f?sig=1"
        )

        adapter = cloud_storage.CloudStorage(
            project_id="test-project",
            storage_path="test-bucket",
            creds_path="",
        )
        url = await adapter.generate_signed_url(
            "org/group/file.wav",
            "",
            method="GET",
            response_disposition="attachment",
            response_type="audio/wav",
        )
        assert url == "https://storage.googleapis.com/b/f?sig=1"
        _, kwargs = mock_blob.generate_signed_url.call_args
        assert kwargs["method"] == "GET"
        assert kwargs["content_type"] is None
        assert kwargs["response_disposition"] == "attachment"
        assert kwargs["response_type"] == "audio/wav"
