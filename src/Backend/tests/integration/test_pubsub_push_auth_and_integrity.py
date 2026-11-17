"""Tests guarding Pub/Sub push OIDC auth, GCS bucket SSRF, and result integrity."""

from __future__ import annotations

import base64
import datetime
import json
import pathlib
import re
import typing
import uuid
from unittest.mock import AsyncMock

import fastapi
import pytest
import sqlalchemy as sa
from api import dependencies, errors, helpers, models
from api.helpers import auth
from api.typings import SessionFactory, Settings
from fastapi.security import http as http_sec
from google.auth import exceptions as google_exceptions
from google.oauth2 import id_token
from httpx import AsyncClient
from passlib import context

if typing.TYPE_CHECKING:
    from tests.conftest import (
        MockAnalyticalResult,
        MockGenAI,
        MockMessagePublisher,
        MockStorage,
    )

EXPECTED_PUBSUB_SA_EMAIL = "sa-123456-pubsub-push@test-project.iam.gserviceaccount.com"
EXPECTED_PUBSUB_SA_SUB = "998877665544332211001"
EXPECTED_PUBSUB_AUDIENCE = "https://backend-test.us-central1.run.app"
VALID_ISSUER = "https://accounts.google.com"


def _make_credentials(
    raw_token: str = "valid-pubsub-oidc-jwt",
) -> http_sec.HTTPAuthorizationCredentials:
    return http_sec.HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=raw_token,
    )


def _valid_pubsub_claims(**overrides: typing.Any) -> dict[str, typing.Any]:
    claims: dict[str, typing.Any] = {
        "iss": VALID_ISSUER,
        "aud": EXPECTED_PUBSUB_AUDIENCE,
        "email": EXPECTED_PUBSUB_SA_EMAIL,
        "email_verified": True,
        "sub": EXPECTED_PUBSUB_SA_SUB,
    }
    claims.update(overrides)
    return claims


def _make_pubsub_envelope(payload: dict[str, typing.Any]) -> dict[str, typing.Any]:
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    return {
        "message": {
            "data": encoded,
            "messageId": f"msg-{uuid.uuid4().hex[:8]}",
        },
        "subscription": "projects/test-project/subscriptions/processor_queue_subs",
    }


async def _seed_exam_user_question(
    session_factory: SessionFactory,
    *,
    euq_status: models.ExamStatus,
    exam_user_status: models.ExamStatus = models.ExamStatus.IN_PROGRESS,
    initial_rating: models.UserRating = models.UserRating.NO_RATING,
    question_type: models.QuestionType = models.QuestionType.WORDS,
    initial_result: list[str] | None = None,
    initial_right_count: int = 0,
    initial_audio_url: str = "",
) -> tuple[models.ExamUserQuestion, models.ExamUser, models.Organization, models.Group]:
    grade = models.Grades.FIRST_FUND
    now = datetime.datetime.now(tz=datetime.UTC)
    suffix = uuid.uuid4().hex[:8]

    async with session_factory() as session:
        series = (
            await session.execute(
                sa.select(models.Series).where(models.Series.name == grade.value)
            )
        ).scalar_one_or_none()
        if series is None:
            series = models.Series(name=grade.value, code=f"S{suffix}")
            session.add(series)
            await session.flush()

        shift = (
            await session.execute(
                sa.select(models.WorkShift).where(models.WorkShift.name == "Manhã")
            )
        ).scalar_one_or_none()
        if shift is None:
            shift = models.WorkShift(name="Manhã", code="MORNING")
            session.add(shift)
            await session.flush()

        org = models.Organization(
            customer_id=None,
            name=f"Org-PubSub-{suffix}",
            region="Sul",
            city="Curitiba",
            state="PR",
        )
        session.add(org)
        await session.flush()

        group = models.Group(
            name=f"Group-PubSub-{suffix}",
            customer_id=None,
            organization_id=org.id,
            series_id=series.id,
            shift_id=shift.id,
        )
        session.add(group)
        await session.flush()

        role = models.Role(
            name=f"student-{suffix}",
            display_name={"en-US": "Student"},
            description={"en-US": "Student"},
            scopes=["user"],
        )
        session.add(role)
        await session.flush()

        student = models.User(
            external_id=None,
            customer_id=None,
            type=models.UserType.PASSWORD,
            role_id=role.id,
            name=f"Student {suffix}",
            email_address=f"student-{suffix}@example.com",
            state="PR",
            region="Sul",
        )
        hash_ctx = context.CryptContext(schemes=["bcrypt"], deprecated="auto")
        student.set_password("Password123!", hash_ctx)
        session.add(student)
        await session.flush()

        question = models.Question(
            name="Q1",
            type=question_type,
            theme=None,
            phrase_id=f"phrase-{suffix}",
            data="casa bola pato",
            formatted_data="casa bola pato",
            order=1,
            answers=[],
        )
        exam = models.Exam(
            name=f"Exam-{suffix}",
            start_date=now - datetime.timedelta(days=1),
            end_date=now + datetime.timedelta(days=7),
            grade=grade,
            questions=[question],
        )
        session.add(exam)
        await session.flush()

        exam_user = models.ExamUser(
            exam_id=exam.id,
            user_id=student.id,
            status=exam_user_status,
            user_rating=initial_rating,
        )
        session.add(exam_user)

        euq = models.ExamUserQuestion(
            user_id=student.id,
            exam_id=exam.id,
            question_id=exam.questions[0].id,
            group_id=group.id,
            organization_id=org.id,
            result=initial_result if initial_result is not None else [],
            right_count=initial_right_count,
            user_accuracy=0.0,
            total_accuracy=0.0,
            audio_url=initial_audio_url,
            ai_feedback=None,
            ai_is_correct=None,
        )
        euq.status = euq_status
        session.add(euq)
        await session.commit()

    return euq, exam_user, org, group


def _configure_pubsub_oidc(
    test_app: fastapi.FastAPI,
    monkeypatch: pytest.MonkeyPatch,
    *,
    claims: dict[str, typing.Any] | None = None,
) -> None:
    app_settings = test_app.state.injector.get(Settings)
    app_settings["pubsub_service_account_email"] = EXPECTED_PUBSUB_SA_EMAIL
    app_settings["pubsub_audience"] = EXPECTED_PUBSUB_AUDIENCE
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda **_kwargs: claims if claims is not None else _valid_pubsub_claims(),
    )


def _stub_ffmpeg(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[list[str], list[tuple[str, str, bool]]]:
    probe_calls: list[str] = []
    convert_calls: list[tuple[str, str, bool]] = []

    def _fake_metadata(path: str) -> dict[str, typing.Any]:
        probe_calls.append(path)
        return {"sample_rate": "16000", "channels": "1", "duration": 10}

    def _fake_convert(src: str, dst: str, is_prod: bool) -> None:
        convert_calls.append((src, dst, is_prod))
        with open(dst, "wb") as fh:
            fh.write(b"RIFFfakewav")

    monkeypatch.setattr(helpers.util, "get_file_metadata", _fake_metadata)
    monkeypatch.setattr(helpers.util, "convert_audio", _fake_convert)
    return probe_calls, convert_calls


def _stub_stt(
    monkeypatch: pytest.MonkeyPatch, transcript: str = "casa bola pato"
) -> AsyncMock:
    process_mock = AsyncMock(return_value=transcript)
    fake_stt = type("FakeSTT", (), {"process": process_mock})()
    monkeypatch.setattr(
        dependencies,
        "get_speech_to_text",
        lambda version, settings, storage: fake_stt,
    )
    return process_mock


# --- 1. Reproducers for unauthenticated forged Pub/Sub requests ---


@pytest.mark.asyncio
async def test_convert_handle_rejects_unauthenticated_forged_ssrf_request(
    unauthenticated_client: AsyncClient,
    mock_storage: MockStorage,
    mock_publisher: MockMessagePublisher,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reproducer: unauthenticated POST to /convert/_handle cannot SSRF GCS/ffmpeg."""
    probe_calls, convert_calls = _stub_ffmpeg(monkeypatch)
    forged = _make_pubsub_envelope(
        {
            "result_id": str(uuid.uuid4()),
            "phrase_set_id": "x",
            "audio": "https://storage.googleapis.com/victim-other-bucket/path/evil.ogg",
            "words": ["a"],
            "question_type": "phrases",
            "question_theme": None,
        }
    )

    resp = await unauthenticated_client.post(
        "/api/v1/processor/convert/_handle",
        json=forged,
    )

    assert resp.status_code == 403
    assert resp.json() == {"detail": "Not authenticated"}
    assert mock_storage.download_calls == []
    assert mock_storage.upload_file_calls == []
    assert probe_calls == []
    assert convert_calls == []
    assert mock_publisher.published == []


@pytest.mark.asyncio
async def test_process_handle_rejects_unauthenticated_forged_tampering_request(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_gen_ai: MockGenAI,
    mock_analytical: MockAnalyticalResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reproducer: unauthenticated POST to /_handle cannot overwrite student results."""
    stt_mock = _stub_stt(monkeypatch, transcript="tampered words")
    euq, exam_user, org, group = await _seed_exam_user_question(
        session_factory,
        euq_status=models.ExamStatus.FINISHED,
        exam_user_status=models.ExamStatus.FINISHED,
        initial_rating=models.UserRating.FLUENT,
        initial_result=["original", "words"],
        initial_right_count=2,
        initial_audio_url=(
            "https://storage.cloud.google.com/test-bucket/original/audio.wav"
        ),
    )

    forged = _make_pubsub_envelope(
        {
            "result_id": str(euq.id),
            "phrase_set_id": "x",
            "audio": f"test-bucket/{org.id}/{group.id}/evil.wav",
            "words": ["casa", "bola", "pato"],
            "duration": 10,
            "sample_rate": 16000,
            "channels": 1,
            "question_type": models.QuestionType.UNDERSTANDING_CHECK.value,
            "question_theme": None,
        }
    )

    resp = await unauthenticated_client.post(
        "/api/v1/processor/_handle",
        json=forged,
    )

    assert resp.status_code == 403
    assert resp.json() == {"detail": "Not authenticated"}
    assert stt_mock.await_count == 0
    assert mock_gen_ai.evaluate_test_calls == []
    assert mock_analytical.saved == []

    async with session_factory() as session:
        refreshed = (
            await session.execute(
                sa.select(models.ExamUserQuestion).where(
                    models.ExamUserQuestion.id == euq.id
                )
            )
        ).unique().scalar_one()
        assert refreshed.result == ["original", "words"]
        assert refreshed.right_count == 2
        assert refreshed.status == models.ExamStatus.FINISHED
        assert (
            refreshed.audio_url
            == "https://storage.cloud.google.com/test-bucket/original/audio.wav"
        )


# --- 2. Unit tests for auth.validate_pubsub_token (OIDC hardening) ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_settings",
    [
        Settings({"project_id": "test-project"}),
        Settings(
            {"project_id": "test-project", "pubsub_service_account_email": ""}
        ),
        Settings(
            {"project_id": "test-project", "pubsub_service_account_email": "   "}
        ),
        Settings({"pubsub_service_account_email": EXPECTED_PUBSUB_SA_EMAIL}),
        Settings(
            {
                "project_id": "  ",
                "pubsub_audience": "  ",
                "pubsub_service_account_email": EXPECTED_PUBSUB_SA_EMAIL,
            }
        ),
    ],
)
async def test_validate_pubsub_token_fails_closed_when_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
    bad_settings: Settings,
) -> None:
    called = False

    def _should_not_be_called(**_kwargs: typing.Any) -> dict[str, typing.Any]:
        nonlocal called
        called = True
        return _valid_pubsub_claims()

    monkeypatch.setattr(id_token, "verify_oauth2_token", _should_not_be_called)

    with pytest.raises(errors.Forbidden):
        await auth.validate_pubsub_token(
            token=_make_credentials(),
            settings=bad_settings,
        )
    assert called is False


@pytest.mark.asyncio
async def test_validate_pubsub_token_rejects_attacker_sa_wrong_iss_aud_sub_and_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        {
            "project_id": "test-project",
            "pubsub_audience": EXPECTED_PUBSUB_AUDIENCE,
            "pubsub_service_account_email": EXPECTED_PUBSUB_SA_EMAIL,
            "pubsub_service_account_sub": EXPECTED_PUBSUB_SA_SUB,
        }
    )

    # Blank token -> 401
    with pytest.raises(errors.TokenExpired):
        await auth.validate_pubsub_token(
            token=_make_credentials("   "), settings=settings
        )

    # Wrong issuer / wrong audience -> 401
    for bad_claims in (
        _valid_pubsub_claims(iss="accounts.google.com"),
        _valid_pubsub_claims(iss="https://evil.example.com"),
        _valid_pubsub_claims(aud="https://other.run.app"),
        _valid_pubsub_claims(aud=None),
    ):
        monkeypatch.setattr(
            id_token, "verify_oauth2_token", lambda _c=bad_claims, **_kw: _c
        )
        with pytest.raises(errors.TokenExpired):
            await auth.validate_pubsub_token(
                token=_make_credentials(), settings=settings
            )

    # Verification library exceptions -> 401 (never 500)
    for exc in (
        ValueError("expired"),
        google_exceptions.GoogleAuthError("bad sig"),  # type: ignore[no-untyped-call]
        google_exceptions.TransportError("cert fetch failed"),  # type: ignore[no-untyped-call]
    ):
        def _raise(_e: Exception = exc, **_kw: typing.Any) -> dict[str, typing.Any]:
            raise _e

        monkeypatch.setattr(id_token, "verify_oauth2_token", _raise)
        with pytest.raises(errors.TokenExpired):
            await auth.validate_pubsub_token(
                token=_make_credentials(), settings=settings
            )

    # Attacker SA / unverified email / wrong sub -> 403
    for bad_identity in (
        _valid_pubsub_claims(email="attacker@evil-project.iam.gserviceaccount.com"),
        _valid_pubsub_claims(email_verified=False),
        _valid_pubsub_claims(email_verified="true"),
        _valid_pubsub_claims(sub="000000000000000000000"),
    ):
        monkeypatch.setattr(
            id_token, "verify_oauth2_token", lambda _c=bad_identity, **_kw: _c
        )
        with pytest.raises(errors.Forbidden):
            await auth.validate_pubsub_token(
                token=_make_credentials(), settings=settings
            )

    # Valid pinned SA + aud + sub -> succeeds
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda **_kw: _valid_pubsub_claims(email=EXPECTED_PUBSUB_SA_EMAIL.upper()),
    )
    await auth.validate_pubsub_token(token=_make_credentials(), settings=settings)


# --- 3. HTTP auth enforcement on both push endpoints ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint",
    ["/api/v1/processor/convert/_handle", "/api/v1/processor/_handle"],
)
async def test_push_handlers_reject_invalid_auth_schemes_and_attacker_tokens(
    test_app: fastapi.FastAPI,
    unauthenticated_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    endpoint: str,
) -> None:
    envelope = _make_pubsub_envelope({"result_id": str(uuid.uuid4())})

    # Non-Bearer -> 403
    resp_basic = await unauthenticated_client.post(
        endpoint,
        json=envelope,
        headers={"Authorization": "Basic dGVzdDp0ZXN0"},
    )
    assert resp_basic.status_code == 403

    # Unconfigured pubsub_service_account_email -> fail closed 403
    monkeypatch.setattr(
        id_token, "verify_oauth2_token", lambda **_kw: _valid_pubsub_claims()
    )
    resp_unconfigured = await unauthenticated_client.post(
        endpoint,
        json=envelope,
        headers={"Authorization": "Bearer valid-looking-token"},
    )
    assert resp_unconfigured.status_code == 403
    assert resp_unconfigured.json()["code"] == "forbidden"

    # Configured SA, attacker Google SA token -> 403 without leaking expected SA
    _configure_pubsub_oidc(
        test_app,
        monkeypatch,
        claims=_valid_pubsub_claims(
            email="attacker@evil-project.iam.gserviceaccount.com"
        ),
    )
    resp_attacker = await unauthenticated_client.post(
        endpoint,
        json=envelope,
        headers={"Authorization": "Bearer attacker-google-oidc"},
    )
    assert resp_attacker.status_code == 403
    assert EXPECTED_PUBSUB_SA_EMAIL not in resp_attacker.text


# --- 4. Defense-in-depth: bucket allow-list & path traversal validation ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malicious_audio",
    [
        "https://storage.googleapis.com/victim-other-bucket/org/grp/evil.ogg",
        "https://storage.googleapis.com/test-bucket-evil/org/grp/evil.ogg",
        "https://storage.cloud.google.com/other-bucket/org/grp/evil.ogg",
        "http://storage.googleapis.com/test-bucket/org/grp/evil.ogg",
        "https://evil.com/storage.googleapis.com/test-bucket/org/grp/evil.ogg",
        "gs://other-bucket/org/grp/evil.ogg",
        "gs://test-bucket/org/grp/evil.ogg",
        "https://storage.googleapis.com/test-bucket/../../other-bucket/secret.ogg",
        "https://storage.googleapis.com/test-bucket/org/%2e%2e/%2e%2e/secret.ogg",
        "https://storage.googleapis.com/test-bucket/org%2f..%2fsecret.ogg",
        "https://storage.googleapis.com/test-bucket/org\\grp\\evil.ogg",
        "https://storage.googleapis.com/test-bucket/org/grp/evil.ogg?alt=media",
        "https://storage.googleapis.com/test-bucket/org/grp/evil.ogg#frag",
        "https://storage.googleapis.com/test-bucket/org/grp/-flag.ogg",
        "https://storage.googleapis.com/test-bucket/only-one-segment.ogg",
        "https://storage.googleapis.com/test-bucket/",
        "",
    ],
)
async def test_convert_handle_blocks_cross_bucket_ssrf_and_path_traversal(
    test_app: fastapi.FastAPI,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_publisher: MockMessagePublisher,
    monkeypatch: pytest.MonkeyPatch,
    malicious_audio: str,
) -> None:
    """With valid OIDC auth, /convert/_handle rejects cross-bucket/malformed URIs."""
    _configure_pubsub_oidc(test_app, monkeypatch)
    probe_calls, convert_calls = _stub_ffmpeg(monkeypatch)
    euq, _eu, _org, _grp = await _seed_exam_user_question(
        session_factory,
        euq_status=models.ExamStatus.IN_PROGRESS,
    )

    envelope = _make_pubsub_envelope(
        {
            "result_id": str(euq.id),
            "phrase_set_id": "p1",
            "audio": malicious_audio,
            "words": ["casa"],
            "question_type": models.QuestionType.WORDS.value,
            "question_theme": None,
        }
    )

    resp = await unauthenticated_client.post(
        "/api/v1/processor/convert/_handle",
        json=envelope,
        headers={"Authorization": "Bearer valid-pubsub-oidc"},
    )

    assert resp.status_code == 422
    assert mock_storage.download_calls == []
    assert probe_calls == []
    assert convert_calls == []
    assert mock_publisher.published == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malicious_audio",
    [
        "victim-other-bucket/org/grp/evil.wav",
        "test-bucket-evil/org/grp/evil.wav",
        "https://storage.googleapis.com/test-bucket/org/grp/evil.wav",
        "gs://other-bucket/org/grp/evil.wav",
        "test-bucket/../../other-bucket/evil.wav",
        "test-bucket/org/grp/evil.wav?foo=bar",
        "test-bucket/org\\grp\\evil.wav",
        "",
    ],
)
async def test_process_handle_blocks_cross_bucket_and_malformed_audio(
    test_app: fastapi.FastAPI,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_gen_ai: MockGenAI,
    mock_analytical: MockAnalyticalResult,
    monkeypatch: pytest.MonkeyPatch,
    malicious_audio: str,
) -> None:
    """With valid OIDC auth, /_handle rejects non-bucket or malformed audio paths."""
    _configure_pubsub_oidc(test_app, monkeypatch)
    stt_mock = _stub_stt(monkeypatch)
    euq, _eu, _org, _grp = await _seed_exam_user_question(
        session_factory,
        euq_status=models.ExamStatus.IN_PROGRESS,
    )

    envelope = _make_pubsub_envelope(
        {
            "result_id": str(euq.id),
            "phrase_set_id": "p1",
            "audio": malicious_audio,
            "words": ["casa"],
            "duration": 10,
            "sample_rate": 16000,
            "channels": 1,
            "question_type": models.QuestionType.UNDERSTANDING_CHECK.value,
            "question_theme": None,
        }
    )

    resp = await unauthenticated_client.post(
        "/api/v1/processor/_handle",
        json=envelope,
        headers={"Authorization": "Bearer valid-pubsub-oidc"},
    )

    assert resp.status_code == 422
    assert stt_mock.await_count == 0
    assert mock_gen_ai.evaluate_test_calls == []
    assert mock_analytical.saved == []


# --- 5. Defense-in-depth: result_id existence & non-FINISHED status enforcement ---


@pytest.mark.asyncio
async def test_convert_and_process_reject_unknown_or_finished_result_id(
    test_app: fastapi.FastAPI,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_publisher: MockMessagePublisher,
    mock_gen_ai: MockGenAI,
    mock_analytical: MockAnalyticalResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject unknown or already-FINISHED result_id before GCS/ffmpeg/STT/Gemini/BQ."""
    _configure_pubsub_oidc(test_app, monkeypatch)
    probe_calls, convert_calls = _stub_ffmpeg(monkeypatch)
    stt_mock = _stub_stt(monkeypatch, transcript="attacker overwrite")

    finished_euq, _eu, org, group = await _seed_exam_user_question(
        session_factory,
        euq_status=models.ExamStatus.FINISHED,
        exam_user_status=models.ExamStatus.FINISHED,
        initial_rating=models.UserRating.FLUENT,
        initial_result=["legit", "reading"],
        initial_right_count=2,
        initial_audio_url=(
            "https://storage.cloud.google.com/test-bucket/legit/audio.wav"
        ),
    )

    for bad_result_id in (uuid.uuid4(), finished_euq.id):
        convert_resp = await unauthenticated_client.post(
            "/api/v1/processor/convert/_handle",
            json=_make_pubsub_envelope(
                {
                    "result_id": str(bad_result_id),
                    "phrase_set_id": "p1",
                    "audio": (
                        f"https://storage.googleapis.com/test-bucket/"
                        f"{org.id}/{group.id}/audio.ogg"
                    ),
                    "words": ["casa"],
                    "question_type": models.QuestionType.WORDS.value,
                    "question_theme": None,
                }
            ),
            headers={"Authorization": "Bearer valid-pubsub-oidc"},
        )
        assert convert_resp.status_code == 422

        process_resp = await unauthenticated_client.post(
            "/api/v1/processor/_handle",
            json=_make_pubsub_envelope(
                {
                    "result_id": str(bad_result_id),
                    "phrase_set_id": "p1",
                    "audio": f"test-bucket/{org.id}/{group.id}/audio.wav",
                    "words": ["casa", "bola"],
                    "duration": 10,
                    "sample_rate": 16000,
                    "channels": 1,
                    "question_type": models.QuestionType.UNDERSTANDING_CHECK.value,
                    "question_theme": None,
                }
            ),
            headers={"Authorization": "Bearer valid-pubsub-oidc"},
        )
        assert process_resp.status_code == 422

    assert mock_storage.download_calls == []
    assert probe_calls == []
    assert convert_calls == []
    assert mock_publisher.published == []
    assert stt_mock.await_count == 0
    assert mock_gen_ai.evaluate_test_calls == []
    assert mock_analytical.saved == []

    # Verify the FINISHED row was completely untouched
    async with session_factory() as session:
        refreshed = (
            await session.execute(
                sa.select(models.ExamUserQuestion).where(
                    models.ExamUserQuestion.id == finished_euq.id
                )
            )
        ).unique().scalar_one()
        assert refreshed.result == ["legit", "reading"]
        assert refreshed.right_count == 2
        assert refreshed.status == models.ExamStatus.FINISHED
        assert (
            refreshed.audio_url
            == "https://storage.cloud.google.com/test-bucket/legit/audio.wav"
        )


# --- 6. Legitimate happy paths (both IN_PROGRESS and NOT_STARTED pending rows) ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pending_status",
    [models.ExamStatus.IN_PROGRESS, models.ExamStatus.NOT_STARTED],
)
async def test_valid_pubsub_pipeline_converts_and_grades_pending_row_once(
    test_app: fastapi.FastAPI,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    mock_publisher: MockMessagePublisher,
    mock_analytical: MockAnalyticalResult,
    monkeypatch: pytest.MonkeyPatch,
    pending_status: models.ExamStatus,
) -> None:
    """Authorized Pub/Sub flow works end-to-end and prevents replay after FINISHED."""
    from api.domain.service import process_result

    _configure_pubsub_oidc(test_app, monkeypatch)
    probe_calls, convert_calls = _stub_ffmpeg(monkeypatch)
    stt_mock = _stub_stt(monkeypatch, transcript="casa bola pato")
    monkeypatch.setattr(
        process_result,
        "get_right_count_user_result",
        lambda words, tts_words, _qt: (len(tts_words.split()), tts_words.split()),
    )

    euq, _eu, org, group = await _seed_exam_user_question(
        session_factory,
        euq_status=pending_status,
        exam_user_status=models.ExamStatus.IN_PROGRESS,
        question_type=models.QuestionType.WORDS,
    )
    encoded_file = f"{euq.exam_id}%7C{euq.question_id}%7C{euq.user_id}.ogg"
    decoded_obj_path = (
        f"{org.id}/{group.id}/{euq.exam_id}|{euq.question_id}|{euq.user_id}.ogg"
    )
    wav_obj_path = (
        f"{org.id}/{group.id}/{euq.exam_id}|{euq.question_id}|{euq.user_id}.wav"
    )

    convert_resp = await unauthenticated_client.post(
        "/api/v1/processor/convert/_handle",
        json=_make_pubsub_envelope(
            {
                "result_id": str(euq.id),
                "phrase_set_id": "phrase-1",
                "audio": (
                    f"https://storage.googleapis.com/test-bucket/"
                    f"{org.id}/{group.id}/{encoded_file}"
                ),
                "words": ["casa", "bola", "pato"],
                "question_type": models.QuestionType.WORDS.value,
                "question_theme": None,
            }
        ),
        headers={"Authorization": "Bearer valid-pubsub-oidc"},
    )
    assert convert_resp.status_code == 200
    assert len(mock_storage.download_calls) == 1
    downloaded_uri, local_filename = mock_storage.download_calls[0]
    assert downloaded_uri == f"gs://test-bucket/{decoded_obj_path}"
    # Local temp filename must be server-generated UUID, never user/URL-derived
    assert "|" not in local_filename
    assert "/" not in local_filename
    assert local_filename.endswith(".ogg")
    assert len(probe_calls) == 2
    assert len(convert_calls) == 1
    assert len(mock_publisher.published) == 1
    reprocessed_msg, _topic = mock_publisher.published[0]
    assert reprocessed_msg.audio == f"test-bucket/{wav_obj_path}"

    # Step 2: /_handle processes the converted audio and finalizes the row
    process_resp = await unauthenticated_client.post(
        "/api/v1/processor/_handle",
        json=_make_pubsub_envelope(
            {
                "result_id": str(euq.id),
                "phrase_set_id": "phrase-1",
                "audio": reprocessed_msg.audio,
                "words": ["casa", "bola", "pato"],
                "duration": 10,
                "sample_rate": 16000,
                "channels": 1,
                "question_type": models.QuestionType.WORDS.value,
                "question_theme": None,
            }
        ),
        headers={"Authorization": "Bearer valid-pubsub-oidc"},
    )
    assert process_resp.status_code == 200
    assert stt_mock.await_count == 1
    assert len(mock_analytical.saved) == 1

    async with session_factory() as session:
        refreshed = (
            await session.execute(
                sa.select(models.ExamUserQuestion).where(
                    models.ExamUserQuestion.id == euq.id
                )
            )
        ).unique().scalar_one()
        assert refreshed.status == models.ExamStatus.FINISHED
        assert refreshed.right_count == 3
        assert (
            refreshed.audio_url
            == f"https://storage.cloud.google.com/test-bucket/{wav_obj_path}"
        )

    # Step 3: Replay of the now-FINISHED result_id is rejected
    replay_resp = await unauthenticated_client.post(
        "/api/v1/processor/_handle",
        json=_make_pubsub_envelope(
            {
                "result_id": str(euq.id),
                "phrase_set_id": "phrase-1",
                "audio": reprocessed_msg.audio,
                "words": ["casa", "bola", "pato"],
                "duration": 10,
                "sample_rate": 16000,
                "channels": 1,
                "question_type": models.QuestionType.WORDS.value,
                "question_theme": None,
            }
        ),
        headers={"Authorization": "Bearer valid-pubsub-oidc"},
    )
    assert replay_resp.status_code == 422
    assert stt_mock.await_count == 1
    assert len(mock_analytical.saved) == 1


# --- 7. Defense-in-depth guards (fail-closed bucket, import/, CloudStorage) ---


@pytest.mark.asyncio
async def test_push_handlers_fail_closed_when_bucket_unconfigured_or_payload_malformed(
    test_app: fastapi.FastAPI,
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    mock_storage: MockStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_pubsub_oidc(test_app, monkeypatch)
    euq, _eu, org, group = await _seed_exam_user_question(
        session_factory,
        euq_status=models.ExamStatus.IN_PROGRESS,
    )

    # Reject admin import/ prefix inside the same bucket
    import_resp = await unauthenticated_client.post(
        "/api/v1/processor/convert/_handle",
        json=_make_pubsub_envelope(
            {
                "result_id": str(euq.id),
                "phrase_set_id": "p1",
                "audio": "https://storage.googleapis.com/test-bucket/import/users/1.csv",
                "words": ["casa"],
                "question_type": models.QuestionType.WORDS.value,
                "question_theme": None,
            }
        ),
        headers={"Authorization": "Bearer valid-pubsub-oidc"},
    )
    assert import_resp.status_code == 422

    # Malformed base64 payload returns 422 cleanly (never 500)
    bad_b64_resp = await unauthenticated_client.post(
        "/api/v1/processor/_handle",
        json={
            "message": {"data": "!!!not-base64!!!", "messageId": "m1"},
            "subscription": "s1",
        },
        headers={"Authorization": "Bearer valid-pubsub-oidc"},
    )
    assert bad_b64_resp.status_code == 422

    # Missing bucket_path fails closed with 403
    app_settings = test_app.state.injector.get(Settings)
    app_settings["bucket_path"] = ""
    no_bucket_resp = await unauthenticated_client.post(
        "/api/v1/processor/convert/_handle",
        json=_make_pubsub_envelope(
            {
                "result_id": str(euq.id),
                "phrase_set_id": "p1",
                "audio": (
                    f"https://storage.googleapis.com/test-bucket/"
                    f"{org.id}/{group.id}/audio.ogg"
                ),
                "words": ["casa"],
                "question_type": models.QuestionType.WORDS.value,
                "question_theme": None,
            }
        ),
        headers={"Authorization": "Bearer valid-pubsub-oidc"},
    )
    assert no_bucket_resp.status_code == 403
    assert mock_storage.download_calls == []


@pytest.mark.asyncio
async def test_cloud_storage_download_enforces_bucket_and_tmp_boundary() -> None:
    """Adapter-level guard: CloudStorage.download rejects cross-bucket and traversal."""
    from api.adapters.google.cloud_storage import CloudStorage

    storage_adapter = CloudStorage.__new__(CloudStorage)
    storage_adapter.storage_path = "test-bucket"
    storage_adapter.audio_path = "/tmp"
    storage_adapter.client = object()  # Must never be touched on rejection

    for bad_uri, bad_name in (
        ("gs://other-bucket/org/grp/file.ogg", "safe.ogg"),
        ("gs://test-bucket-evil/org/grp/file.ogg", "safe.ogg"),
        ("gs://test-bucket/../../other-bucket/file.ogg", "safe.ogg"),
        ("gs://test-bucket/org/grp/file.ogg", "../escape.ogg"),
        ("gs://test-bucket/org/grp/file.ogg", "sub/dir.ogg"),
    ):
        with pytest.raises(errors.InvalidField):
            await storage_adapter.download(bad_uri, bad_name)


# --- 8. OpenAPI and Terraform configuration guards ---


@pytest.mark.asyncio
async def test_pubsub_push_routes_stay_excluded_from_openapi(
    unauthenticated_client: AsyncClient,
) -> None:
    resp = await unauthenticated_client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/api/v1/processor/_handle" not in paths
    assert "/api/v1/processor/convert/_handle" not in paths


def test_terraform_pubsub_push_subscriptions_require_oidc_token() -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    tf_path = repo_root / "IAC" / "06-message_service.tf"
    tf_text = tf_path.read_text(encoding="utf-8")

    for sub_name in ("processor_queue", "conversion_queue"):
        block_match = re.search(
            rf'resource\s+"google_pubsub_subscription"\s+"{sub_name}"\s*\{{(.*?)\n\}}',
            tf_text,
            re.DOTALL,
        )
        assert block_match is not None, f"Missing subscription block for {sub_name}"
        block = block_match.group(1)
        assert "oidc_token" in block, f"{sub_name} push_config missing oidc_token block"
        assert "service_account_email" in block, (
            f"{sub_name} oidc_token missing service_account_email"
        )
