"""Regression tests preventing plaintext password and PII disclosure in logs/Sentry."""

from __future__ import annotations

import ast
import datetime
import io
import json
import logging
import logging.config
import typing
import uuid
from pathlib import Path

import pydantic
import pytest
import sentry_sdk
from api import logging_config, models, sentry
from api.routers.auth import schemas as auth_schemas
from api.routers.users import schemas as user_schemas
from api.typings import SessionFactory, Settings
from httpx import AsyncClient
from passlib import context as passlib_context

_BACKEND_SRC = Path(__file__).resolve().parents[2] / "src" / "api"


def _setup_json_log_capture() -> tuple[io.StringIO, list[logging.Handler]]:
    """Attach a stream backed by logging_config's JSON formatter to the root logger."""
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    buf = io.StringIO()
    cfg = logging_config.get_logging_config(level="DEBUG", fmt="json")
    logging.config.dictConfig(cfg)
    for handler in root.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setStream(buf)
    return buf, saved_handlers


def _restore_handlers(saved_handlers: list[logging.Handler]) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    for handler in saved_handlers:
        root.addHandler(handler)


def test_structlog_redacts_user_dict_string_and_extra_credentials() -> None:
    """Reproduces historical users/endpoints.py:396 log leak and structured extras."""
    secret_password = f"PlaintextP@ss!'{uuid.uuid4().hex}"
    secret_email = f"student-{uuid.uuid4().hex}@example.com"
    secret_token = f"eyJhbGciOiJSUzUxMiJ9.{uuid.uuid4().hex}.sig"
    secret_reset = f"reset-{uuid.uuid4().hex}"

    buf, saved_handlers = _setup_json_log_capture()
    try:
        test_logger = logging.getLogger("api.routers.users.endpoints")
        user_dict = {
            "external_id": None,
            "role_id": str(uuid.uuid4()),
            "name": "Test Student",
            "email_address": secret_email,
            "password": secret_password,
            "type": "password",
        }
        # Exact pattern from historical users/endpoints.py:396
        test_logger.info(f"\n\n{user_dict}\n\n")
        # Structured extra dict, Authorization header, and query string secret
        test_logger.info(
            f"Authorization: Bearer {secret_token} https://app.example.com/reset?token={secret_reset}&lang=pt",
            extra={
                "user": user_dict,
                "headers": {
                    "Authorization": f"Bearer {secret_token}",
                    "Set-Cookie": f"session={secret_reset}",
                },
                "token_type": "bearer",
            },
        )
    finally:
        _restore_handlers(saved_handlers)

    output = buf.getvalue()
    assert secret_password not in output
    assert secret_email not in output
    assert secret_token not in output
    assert secret_reset not in output
    assert "[REDACTED]" in output

    records = [json.loads(line) for line in output.strip().splitlines()]
    assert len(records) == 2
    assert records[1]["user"]["password"] == "[REDACTED]"
    assert records[1]["user"]["email_address"] == "[REDACTED]"
    assert records[1]["headers"]["Authorization"] == "[REDACTED]"
    assert records[1]["headers"]["Set-Cookie"] == "[REDACTED]"
    assert records[1]["token_type"] == "bearer"
    assert "lang=pt" in records[1]["event"]
    assert (
        logging_config.redact_string("Your email and/or password are invalid.")
        == "Your email and/or password are invalid."
    )


def test_sentry_scrubs_breadcrumbs_and_excludes_local_vars_on_exception() -> None:
    """Sentry events/breadcrumbs must never receive passwords or frame locals."""
    secret_password = f"SentryPw!{uuid.uuid4().hex}"
    secret_email = f"sentry-{uuid.uuid4().hex}@example.com"
    secret_hash = f"$2b$12$fakehash{uuid.uuid4().hex}"
    secret_reset = f"reset-tok-{uuid.uuid4().hex}"
    arbitrary_local = f"unlabeled-secret-{uuid.uuid4().hex}"

    captured_events: list[dict[str, typing.Any]] = []

    class _CaptureTransport(sentry_sdk.Transport):
        def capture_envelope(self, envelope: typing.Any) -> None:
            for item in envelope:
                if item.headers.get("type") == "event":
                    captured_events.append(json.loads(item.get_bytes().decode("utf-8")))

    sentry.setup(Settings({"project_id": "test-project"}))
    client = sentry_sdk.get_client()
    client.transport = _CaptureTransport()

    test_logger = logging.getLogger("api.routers.users.endpoints")

    def _failing_signup_or_create() -> None:
        raw_secret = arbitrary_local
        body_dict = {
            "name": "Alice",
            "email_address": secret_email,
            "password": secret_password,
        }
        user = models.User(
            external_id=None,
            customer_id=None,
            type=models.UserType.PASSWORD,
            role_id=uuid.uuid4(),
            name="Alice",
            email_address=secret_email,
            state=None,
            region=None,
        )
        user._password = secret_hash  # noqa: SLF001
        user.reset_token = secret_reset
        test_logger.info(f"\n\n{body_dict}\n\n")
        assert raw_secret  # keep local live in frame
        raise RuntimeError(f"boom while handling password={secret_password}")

    try:
        _failing_signup_or_create()
    except RuntimeError as exc:
        sentry_sdk.capture_exception(exc)
    sentry_sdk.flush()

    assert len(captured_events) == 1
    serialized = json.dumps(captured_events[0])
    assert secret_password not in serialized
    assert secret_email not in serialized
    assert secret_hash not in serialized
    assert secret_reset not in serialized
    assert arbitrary_local not in serialized


def test_user_model_and_auth_schemas_hide_credentials_in_repr() -> None:
    """ORM models and Pydantic schemas must never expose secrets in repr/str."""
    secret_password = f"ReprSecret!{uuid.uuid4().hex}"
    secret_hash = f"$2b$12$hash{uuid.uuid4().hex}"
    secret_reset = f"reset-{uuid.uuid4().hex}"
    secret_access = f"access-{uuid.uuid4().hex}"
    secret_refresh = f"refresh-{uuid.uuid4().hex}"
    secret_fb = f"firebase-{uuid.uuid4().hex}"

    user = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        role_id=uuid.uuid4(),
        name="Alice",
        email_address="alice@example.com",
        state=None,
        region=None,
    )
    user._password = secret_hash  # noqa: SLF001
    user.reset_token = secret_reset
    assert secret_hash not in repr(user)
    assert secret_reset not in repr(user)

    user_create = user_schemas.UserCreate(
        role_id=uuid.uuid4(),
        name="Alice",
        email_address="alice@example.com",
        type=models.UserType.PASSWORD,
        password=secret_password,
    )
    assert secret_password not in repr(user_create)
    assert secret_password not in str(user_create)
    # Preserves runtime value and StrictStr behavior
    assert user_create.password == secret_password
    assert user_create.dict()["password"] == secret_password
    with pytest.raises(pydantic.ValidationError):
        user_schemas.UserCreate(
            role_id=uuid.uuid4(),
            name="Alice",
            email_address="alice@example.com",
            type=models.UserType.PASSWORD,
            password=typing.cast(str, 123456),
        )

    login_schema = auth_schemas.EmailPasswordLogin(
        email_address="alice@example.com",
        password=secret_password,
    )
    assert secret_password not in repr(login_schema)
    assert secret_password not in str(login_schema)
    assert login_schema.password == secret_password

    fb_schema = auth_schemas.FirebaseLogin(token=secret_fb)
    assert secret_fb not in repr(fb_schema)
    assert secret_fb not in str(fb_schema)

    reset_schema = auth_schemas.ResetPassword(
        token=secret_reset,
        password=secret_password,
    )
    assert secret_reset not in repr(reset_schema)
    assert secret_password not in repr(reset_schema)

    session_schema = auth_schemas.Session(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        user_name="Alice",
        access_token=secret_access,
        refresh_token=secret_refresh,
        expires_in=datetime.timedelta(minutes=60),
        scopes=["admin"],
    )
    assert secret_access not in repr(session_schema)
    assert secret_refresh not in repr(session_schema)


@pytest.mark.asyncio
async def test_removed_signup_and_auth_endpoints_do_not_log_passwords(
    unauthenticated_client: AsyncClient,
    session_factory: SessionFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Removed /signup, login, admin create, and reset must never log secrets."""
    role = models.Role(
        name=f"admin-log-guard-{uuid.uuid4()}",
        display_name={"en-US": "Admin"},
        description={"en-US": "Admin"},
        scopes=["admin"],
    )
    hash_ctx = passlib_context.CryptContext(schemes=["bcrypt"], deprecated="auto")
    admin_pw = f"AdminPw!{uuid.uuid4().hex}"
    admin_email = f"admin-log-{uuid.uuid4().hex}@example.com"
    admin_user = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        role_id=role.id,
        name="Seed Admin",
        email_address=admin_email,
        state=None,
        region=None,
    )
    admin_user.set_password(admin_pw, hash_ctx)

    async with session_factory() as session:
        session.add(role)
        await session.flush()
        session.add(admin_user)
        await session.commit()

    signup_pw = f"SignupPw!{uuid.uuid4().hex}"
    create_pw = f"CreatePw!{uuid.uuid4().hex}"
    wrong_pw = f"WrongPw!{uuid.uuid4().hex}"
    reset_pw = f"ResetPw!{uuid.uuid4().hex}"
    reset_tok = f"ResetTok{uuid.uuid4().hex}"
    user_email = f"log-guard-{uuid.uuid4().hex}@example.com"

    with caplog.at_level(logging.DEBUG):
        # 1. Removed /signup endpoint (must remain 405 and never log body)
        signup_resp = await unauthenticated_client.post(
            "/api/v1/users/signup",
            json={
                "name": "Signup Attempt",
                "email_address": user_email,
                "password": signup_pw,
                "type": "password",
            },
        )
        assert signup_resp.status_code == 405

        # 2. Failed and successful login (POST /api/v1/auth/token)
        bad_login = await unauthenticated_client.post(
            "/api/v1/auth/token",
            json={"email_address": admin_email, "password": wrong_pw},
        )
        assert bad_login.status_code == 401

        good_login = await unauthenticated_client.post(
            "/api/v1/auth/token",
            json={"email_address": admin_email, "password": admin_pw},
        )
        assert good_login.status_code == 200
        access_token = good_login.json()["access_token"]

        # 3. Admin user creation (POST /api/v1/users) with real Bearer JWT
        create_resp = await unauthenticated_client.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "role_id": str(role.id),
                "groups": [],
                "organizations": [],
                "name": "Provisioned User",
                "email_address": user_email,
                "type": "password",
                "password": create_pw,
            },
        )
        assert create_resp.status_code == 200
        created_user_id = uuid.UUID(create_resp.json()["id"])

        # 4. Password reset (POST /api/v1/auth/reset)
        async with session_factory() as session:
            db_user = await session.get(models.User, created_user_id)
            assert db_user is not None
            db_user.reset_token = reset_tok
            await session.commit()

        reset_resp = await unauthenticated_client.post(
            "/api/v1/auth/reset",
            json={"token": reset_tok, "password": reset_pw},
        )
        assert reset_resp.status_code == 200

        async with session_factory() as session:
            refreshed = await session.get(models.User, created_user_id)
            assert refreshed is not None
            assert refreshed.check_password(reset_pw, hash_ctx)

    all_logged = "\n".join(
        f"{rec.getMessage()} {rec.__dict__}" for rec in caplog.records
    )
    for secret in (
        signup_pw,
        admin_pw,
        create_pw,
        wrong_pw,
        reset_pw,
        reset_tok,
        access_token,
        admin_email,
        user_email,
    ):
        assert secret not in all_logged


def test_users_router_has_no_credential_or_user_dict_logging() -> None:
    """Static guard preventing logger.info(user_dict) regressions in users router."""
    forbidden_terms = ("user_dict", "body_dict", "password", "email_address")
    for rel_path in ("routers/users/endpoints.py", "routers/users/crud.py"):
        source = (_BACKEND_SRC / rel_path).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_log_call = (
                isinstance(func, ast.Attribute)
                and func.attr
                in {"debug", "info", "warning", "error", "critical", "exception", "log"}
            ) or (isinstance(func, ast.Name) and func.id == "print")
            if is_log_call:
                snippet = ast.unparse(node)
                for forbidden in forbidden_terms:
                    assert forbidden not in snippet, (
                        f"Forbidden sensitive logging in {rel_path}: {snippet}"
                    )
