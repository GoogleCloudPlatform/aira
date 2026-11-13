# Spec: Remove Unauthenticated Signup and Email-Check Endpoints

**Status:** Draft — Doubt-Verified & Awaiting Human Review (Phase 1: Specify)  
**Date:** 2026-11-13  
**Source Intent:** [`docs/intents/intent-remove-signup-and-check-email.md`](../intents/intent-remove-signup-and-check-email.md)  
**Scope Check (Phase 0):** Single capability (surgical removal of unauthenticated self-signup/enumeration surface and dead signup artifacts); capability-map decomposition is not required.

---

## Assumptions Surfaced

1. **No external consumers depend on `/signup` or `/check_email`:** Neither `POST /api/v1/users/signup` nor `GET /api/v1/users/check_email/{user_email}` is called by external scripts, mobile clients, or API gateways outside this repository (`UNVERIFIED` in live Cloud Run logs; confirmed zero callers across `src/Frontend/`, `src/Agent/`, `src/IAC/`, and `src/Backend/tests/`).
2. **Hard deletion over deprecation responses:** Returning Starlette's standard routing responses (`405` with `Allow: GET` for `POST /api/v1/users/signup`; `404` for `GET /api/v1/users/check_email/{email}` on non-slash valid emails) is preferred over maintaining stub `410 Gone` handlers.
3. **Dead signin CTA translation key is part of dead signup i18n cleanup:** `form.signin.create_account` (`"Don't have an account? Sign up for free"` at `form.json:13` across `en-US`, `pt-BR`, `es-ES`) has zero references in `src/Frontend/src/` and will be removed alongside `form.signup`, `toast.success.auth.success_signup`, and `toast.errors.auth.signup_user_error`, while `toast.errors.auth.email_already_registered` (`toast.json:69`) is left untouched unless requested.
4. **New unauthenticated test fixture uses `httpx.ASGITransport` with strict fixture separation:** Regression tests will introduce a dedicated `unauthenticated_client` fixture using `AsyncClient(transport=ASGITransport(app=test_app), base_url="http://testserver")` per `httpx` `0.27.2` docs rather than refactoring existing `client` usages in `tests/conftest.py`, and will never request `client` and `unauthenticated_client` in the same test function.

---

## 1. Objective

Eliminate two unauthenticated PoC endpoints in the `users` router that expose AIRA tenants to account enumeration and unauthorized student-session minting:

- **`GET /api/v1/users/check_email/{user_email}`** (`src/Backend/src/api/routers/users/endpoints.py:410-423`, handler `delete`): Unauthenticated email-enumeration oracle returning `200 OK` for unknown emails vs. `409` (`UserAlreadyExists`) for registered emails.
- **`POST /api/v1/users/signup`** (`src/Backend/src/api/routers/users/endpoints.py:347-407`, handler `signup`): Unauthenticated self-registration endpoint that mints active `user`-role accounts inside the hardcoded `"Escola Senai"` organization and `"Senai 3EM"` group (`src/Backend/fixture.py:52-65`) and logs raw `user_dict` payloads containing plaintext passwords (`endpoints.py:396`).

**Target Users Protected:** School administrators, educators, and students whose tenant boundaries and PII are protected by admin-only user provisioning (`POST /api/v1/users` and `PUT /api/v1/users/batch`).

---

## 2. Tech Stack (Locked Versions in Scope)

- **Backend (`src/Backend/pyproject.toml`, `poetry.lock`, `mypy.ini`):** Python `>=3.11,<3.14`, `fastapi` `0.115.6` (`^0.115.0`), `starlette` `0.41.3`, `pydantic` `1.10.19` (`^1.10.9`, `extras = ["email"]`, `email-validator` `2.2.0`), `sqlalchemy` `2.0.37` (`^2.0.25`, `asyncpg`), `fastapi-injector` `0.6.2` (`^0.6.0`), `fastapi-pagination` `0.12.34` (`^0.12.19`), `passlib` `1.7.4` (`bcrypt` `4.2.1`), `httpx` `0.27.2` (`^0.27.0`), `pytest` `8.3.4`, `pytest-asyncio` `0.23.8` (`asyncio_mode = "strict"` at `pyproject.toml:119`), `ruff` `0.4.10` (`^0.4.1`), `mypy` `1.13.0` (`^1.10.0`, `strict = true` at `mypy.ini:4`).
- **Frontend (`src/Frontend/package.json`, `pnpm-lock.yaml`):** Node `>=20`, `pnpm` `>=9.0.0` (`packageManager: "pnpm@9.0.2"` at `package.json:5`, `lockfileVersion: '9.0'`), `next` `14.2.2` (App Router), `next-intl` `3.9.4`, `typescript` `5.4.2`.

---

## 3. Where It Hooks In & Affected Project Structure

### System Hook-In Points

1. **FastAPI Router Table (`src/Backend/src/api/factory.py:62` -> `routers/users/endpoints.py`):**
   - `app.include_router(routers.users_router, prefix="/api/v1/users")` mounts `users_router`.
   - Removing `@router.post("/signup")` (`endpoints.py:347-407`) and `@router.get("/check_email/{user_email}")` (`endpoints.py:410-423`) removes both `APIRoute` entries from `users_router.routes` and from FastAPI's generated `/openapi.json` schema at startup.
   - Because remaining single-segment routes `@router.get("/{user_id}")` (`L274`), `@router.delete("/{user_id}")` (`L426`), and `@router.patch("/{user_id}")` (`L458`) are three separate `APIRoute` objects using Starlette's default `str` path convertor (`"/{user_id}"`), Starlette `0.41.3` `Router.app` matches `POST /api/v1/users/signup` as a `Match.PARTIAL` against the first matching route (`GET /{user_id}` at `L274`), returning `405` with `Allow: GET`. Two-segment `GET /api/v1/users/check_email/{email}` misses all routes (`404`) for every valid email string that does not contain `/` in its local-part.
2. **Pydantic Request Schema & Imports (`src/Backend/src/api/routers/users/schemas.py`):**
   - `SignupUserCreate` (`schemas.py:149-175`) is referenced exclusively by `signup` (`endpoints.py:352`). Removing it leaves `errors` (`schemas.py:10`) and `util` (`schemas.py:11`) unused in `schemas.py` (`from api import models` remains), and `util` (`endpoints.py:18`) unused in `endpoints.py`.
3. **Custom Domain Exceptions & Middleware (`src/Backend/src/api/errors.py` & `middleware.py:202-210`):**
   - `errors.BaseError` subclasses are serialized by `middleware.error_handler`. `UserAlreadyExists` (`errors.py:296-306`) and `InvalidEmail` (`errors.py:309-320`) are raised exclusively by `signup`, `check_email`, and `SignupUserCreate`. Retained admin `POST /api/v1/users` uses `errors.AlreadyExists` (`errors.py:102-112`) and `pydantic.EmailStr`.
4. **Utility Helper (`src/Backend/src/api/helpers/util.py`):**
   - `validate_email` (`util.py:47-50`) is called only in `SignupUserCreate` (`schemas.py:165`) and `signup` (`endpoints.py:374`).
5. **Test Harness & DI Container (`src/Backend/tests/conftest.py`):**
   - `test_app` (`conftest.py:230-270`) wires `TestSettingsModule`, `TestSQLAlchemyModule`, `SQLAlchemyModule`, `SyncModule`, `TestGoogleModule`, `UtilModule`, and `TracingModule`, and `client` (`conftest.py:273-295`) mutates `test_app.dependency_overrides[auth.get_token] = override_get_token` on that function-scoped `test_app`.
   - **Three required `conftest.py` additions for `POST /api/v1/users` & unauthenticated Bearer tests:**
     1. **`CryptContext` provider in `TestSettingsModule`:** Production `SettingsModule.provide_hashing_context` (`dependencies.py:69-77`) provides `context.CryptContext(schemes=["bcrypt"], deprecated="auto")`, whereas `TestSettingsModule` (`conftest.py:250-256`) omits it. Without it, `injector` (`auto_bind=True`) constructs `CryptContext()` with empty `schemes=()`, causing `user.set_password(...)` in `POST /api/v1/users` (`type="password"`) to raise `KeyError('no hash schemes configured for this CryptContext instance')` (`500`). Moreover, because `test_app` sets `"env": "local"`, `factory.py:83-84` registers `start_middleware` (`middleware.py:288-296`), whose `_profiling` middleware calls `pyinstrument.Profiler.start()` without `try/finally: p.stop()` — so an unhandled exception inside `call_next` leaves the global profiler running and crashes all subsequent requests in the test session with `RuntimeError: There is already a profiler running`.
     2. **Module-level singleton `memory.SecretManager()`:** Testing forged `Authorization: Bearer <token>` headers invokes `auth.get_public_key(secrets)` (`auth.py:26-36`), which uses `@aiocache.cached(ttl=None, namespace="public-key")` keyed on `str(secrets)` (`<...SecretManager object at 0x...>`). Because `memory.SecretManager()` (`adapters/memory/secret_manager.py:37-57`) generates a new 2048-bit RSA keypair on every instantiation when `tests/private.pem` does not exist, binding a module-level singleton `_TEST_SECRET_MANAGER = memory.SecretManager()` (and `memory.ExternalAuth()`) in `conftest.py` avoids per-test RSA keygen overhead and prevents stale cached public-key collisions if Python reuses a garbage-collected object address.
     3. **Dedicated `unauthenticated_client` fixture (never co-requested with `client`):** Saves, clears, and restores `test_app.dependency_overrides` around `AsyncClient(transport=ASGITransport(app=test_app), base_url="http://testserver")`. Because `client` and `unauthenticated_client` share the same function-scoped `test_app`, any single test function must request **at most one** of them.
6. **Frontend Endpoint Constants & `next-intl` Message Bundles (`src/Frontend/src/`):**
   - `ENDPOINT_SIGNUP` and `ENDPOINT_CHECK_EMAIL` (`src/constants/endpoints.ts:27-28`) have zero imports across `src/Frontend/src/`.
   - `src/libs/i18n/i18n-config.ts:11-25` merges 10 JSON namespaces per locale (`en-US`, `pt-BR`, `es-ES`) at runtime without `IntlMessages` TypeScript augmentation; removing unused `signup` keys in `form.json` and `toast.json` shrinks serialized client message payloads without altering component props or routes. Because `form.signin.create_account` (`form.json:13`) and `toast.success.auth.success_signup` (`toast.json:10`) are the final properties in their enclosing JSON objects across all three locales, the trailing commas on `form.json:12` and `toast.json:9` must also be removed to keep valid JSON.

### Affected Files Map

```text
src/Backend/
├── src/api/
│   ├── errors.py                                      # Modify: delete UserAlreadyExists, InvalidEmail
│   ├── helpers/util.py                                # Modify: delete validate_email()
│   └── routers/users/
│       ├── endpoints.py                               # Modify: delete signup, check_email (delete), unused util import
│       └── schemas.py                                 # Modify: delete SignupUserCreate, unused errors & util imports
└── tests/
    ├── conftest.py                                    # Modify (minimal): bind CryptContext + singleton memory SecretManager, add unauthenticated_client
    └── integration/
        └── test_users_signup_removed.py               # Add: async regression tests for removed routes & retained admin create

src/Frontend/
└── src/
    ├── constants/endpoints.ts                         # Modify: delete ENDPOINT_SIGNUP, ENDPOINT_CHECK_EMAIL
    └── libs/i18n/languages/
        ├── en-US/{form.json,toast.json}               # Modify: delete dead signup keys & fix preceding trailing commas
        ├── pt-BR/{form.json,toast.json}               # Modify: delete dead signup keys & fix preceding trailing commas
        └── es-ES/{form.json,toast.json}               # Modify: delete dead signup keys & fix preceding trailing commas

docs/
├── intents/intent-remove-signup-and-check-email.md    # Reference intent (existing)
└── specs/spec-remove-signup-and-check-email.md        # This specification
```

---

## 4. Configuration & Limits

### Configuration

- **Runtime Environment Variables:** **None added, renamed, or removed.** No feature flag (e.g., `_ENABLE_PUBLIC_SIGNUP`) is introduced; self-signup is permanently absent.
- **Dependency Injection (`src/Backend/src/api/dependencies.py`):** **No changes** to production `Injector` modules (`SettingsModule`, `EngineSQLAlchemy`, `SQLAlchemyModule`, `SyncModule`, `MemoryModule`, `GoogleModule`, `InternetlessModule`, `UtilModule`, `TracingModule`).
- **CORS, Exception, & Profiling Middleware (`src/Backend/src/api/factory.py:42-55, 72-85`):** **No changes** to `InjectorMiddleware`, `CORSMiddleware`, `LoggingMiddleware`, exception handlers, or `start_middleware` (`_profiling` enabled when `env == "local"`).
- **Test Environment Configuration:** Running Backend integration tests requires a disposable PostgreSQL database (`_DATABASE_TEST_URI`, defaulting to `postgresql+asyncpg://fabriciols@localhost:5432/aira_test` in `tests/conftest.py:196-199`, or `db-test` on port `5433` via Docker Compose) and `_ENV=local` (set at `tests/conftest.py:15`).

### Limits & Constraints

- **Rate Limiting:** Out of scope for this change; no rate-limiting middleware is added or modified on `/api/v1/users` or `/api/v1/auth/*`.
- **Request Body Size Limit:** Unchanged (Starlette `0.41.3` default; no custom body-size middleware).
- **RBAC Scope Limit on Provisioning:** User creation via `POST /api/v1/users` requires a valid RS512 session JWT containing the `"admin"` scope (`dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])]`) whose `sub` (`"<session_uuid>:<generation>"`) resolves to an existing row in the `sessions` table via `ports.GetSession` (`auth.py:126-132`, `adapters/sqlalchemy/session_query.py:98-120`).
- **Validation & Database Column Limits on Retained `POST /api/v1/users`:**
  - `email_address`: Validated by `pydantic.EmailStr` (`email-validator` `2.2.0` syntax rules) and stored in `users.email_address` (`VARCHAR(100) UNIQUE NOT NULL`, `src/Backend/src/api/models/users.py:102`).
  - `name`: Non-null `str`, stored in `users.name` (`VARCHAR(100) NOT NULL`, `models/users.py:100`).
  - `password`: Required (`StrictStr`) when `type == "password"`, forbidden when `type == "firebase"` (`src/Backend/src/api/routers/users/crud.py:32-38`).
  - Tenant cardinality (`crud.py:51-65`): Users whose role lacks both `"admin"` and `"dashboard.viewer"` must belong to `>=1` group and `>=1` organization; users with `"user"` scope (when lacking `"admin"` and `"dashboard.viewer"`) are limited to **at most 1** group and **at most 1** organization, and every group's `organization_id` must belong to one of the user's organizations.

---

## 5. Error Responses & HTTP Contract

### Post-Deletion Responses on Removed Endpoints

| Request | Auth Header | Status | Headers | Response Body | Source |
|---|---|---|---|---|---|
| `POST /api/v1/users/signup` (any JSON body or empty body) | None or any | `405 Method Not Allowed` | `Allow: GET` | `{"detail": "Method Not Allowed"}` | Starlette `0.41.3` `Router.app` first `Match.PARTIAL` on `@router.get("/{user_id}")` (`endpoints.py:274`) |
| `GET /api/v1/users/check_email/{email}` (any valid email **without `/` in local-part**, registered or unregistered) | None or any | `404 Not Found` | Standard JSON headers | `{"detail": "Not Found"}` | Starlette `0.41.3` `Router.not_found` (identical response; zero enumeration signal) |
| `GET /api/v1/users/check_email/exams` or `/exams-results` *(2-segment literal collision)* | None | `403 Forbidden` | Standard JSON headers | `{"detail": "Not authenticated"}` | Matches `GET /{user_id}/exams` (`L597`) or `/exams-results` (`L670`); rejected by `HTTPBearer` before `uuid.UUID` parsing or DB lookup |
| `GET /api/v1/users/check_email/{email_with_slash}` *(RFC 5322 `/` or `%2F` in local-part, ASGI-decoded into 3+ segments)* | None | `404`, `403`, or `405` (`Allow: POST`) | Standard JSON headers | Route-dependent (`Not Found` / `Not authenticated` / `Method Not Allowed`) | Never queries `users.email_address`; `403` only on 4-segment `.../exams/{id}/questions` (`L726`), `405` only on 5-segment `.../exams/{id}/questions/{qid}` (`L791`) |

### Retained `POST /api/v1/users` Error & Success Responses (Regression Contract)

| Scenario | Status | Response Body | Handler / Source |
|---|---|---|---|
| Missing `Authorization` header (or bare `Bearer` with no credentials) | `403 Forbidden` | `{"detail": "Not authenticated"}` | `fastapi.security.HTTPBearer` (`auth.py:52`) |
| Non-`Bearer` `Authorization` scheme (e.g., `Basic ...`) | `403 Forbidden` | `{"detail": "Invalid authentication credentials"}` | `fastapi.security.HTTPBearer` (`auth.py:52`) |
| Malformed, expired, or bad-signature Bearer JWT | `401 Unauthorized` | `{"status_code": 401, "message": "The token is expired and/or invalid.", "code": "token_expired_or_invalid"}` | `errors.TokenExpired` (`auth.py:124` -> `middleware.error_handler`) |
| Valid JWT lacking `"admin"` scope (e.g., `"user"` or `"professor"`) or missing/deleted row in `sessions` | `401 Unauthorized` | `{"detail": "You don't have enough permission to do it."}` | `auth.get_token` (`auth.py:110-132`, `session_query.py:117-118`) |
| Admin JWT + invalid `email_address` format in `UserCreate` | `422 Unprocessable Entity` | `{"detail": [{"loc": ["body", "email_address"], "msg": "value is not a valid email address", "type": "value_error.email"}]}` | FastAPI `RequestValidationError` + `pydantic.EmailStr` (`schemas.py:133`) |
| Admin JWT + duplicate `email_address` already in `users` table | `409 Conflict` | `{"status_code": 409, "message": "The entity already exists.", "code": "already_exists"}` | `UserRepository.create` (`adapters/sqlalchemy/user.py:91-92`) -> `errors.AlreadyExists` |
| Admin JWT + valid `UserCreate` payload | `200 OK` | `schemas.UserGet` JSON (`id`, `name`, `email_address`, `groups`, `organizations`, `role_id`, `role`, `state`, `region`, `external_id`, `last_login`, `created_at`, `updated_at`) | `users/endpoints.py:294-345`, `users/schemas.py:18-37, 111-122` |

---

## 6. What Must Not Change (System Invariants)

1. **Database Schema & Migrations:** Zero Alembic revisions added or edited under `src/Backend/migrations/versions/`; `users`, `users_groups`, `users_organizations`, `roles`, `groups`, and `organizations` tables and `models/users.py` remain untouched.
2. **All 14 Retained User Endpoints (`src/Backend/src/api/routers/users/endpoints.py`):**
   - `GET /api/v1/users/me` (`L31`), `GET /api/v1/users/export` (`L48`), `GET /api/v1/users` (`L97`), `GET /api/v1/users/exams` (`L157`), `GET /api/v1/users/dashboard` (`L216`), `GET /api/v1/users/{user_id}` (`L274`), `POST /api/v1/users` (`L294`), `DELETE /api/v1/users/{user_id}` (`L426`), `PATCH /api/v1/users/{user_id}` (`L458`), `PUT /api/v1/users/batch` (`L509`), `GET /api/v1/users/{user_id}/exams` (`L597`), `GET /api/v1/users/{user_id}/exams-results` (`L670`), `GET /api/v1/users/{user_id}/exams/{exam_id}/questions` (`L726`), and `POST /api/v1/users/{user_id}/exams/{exam_id}/questions/{question_id}` (`L791`) retain their exact paths, scopes, request/response schemas, and behavior.
3. **Shared User Creation & Repository Logic:** `src/Backend/src/api/routers/users/crud.py` (`create_user`, `validate_default_user`, `update_user`) and `src/Backend/src/api/adapters/sqlalchemy/user.py` (`UserRepository`) must not be modified.
4. **Local Seed Script (`src/Backend/fixture.py`):** `"Escola Senai"` (`L52-58`) and `"Senai 3EM"` (`L59-65`) seed records remain intact for local development (`make fixture`).
5. **All 7 Authentication & Password-Recovery Endpoints (`src/Backend/src/api/routers/auth/endpoints.py`):** `POST /api/v1/auth/token` (`L28`), `POST /api/v1/auth/refresh` (`L60`), `GET /api/v1/auth/dashboard` (`L96`), `POST /api/v1/auth/forgot` (`L114`), `POST /api/v1/auth/reset` (`L141`), `GET /api/v1/auth/users/looker` (`L158`), and `POST /api/v1/auth/user/looker/_handle` (`L182`) remain unchanged.
6. **Frontend Sign-In Flow (`src/Frontend/src/components/sign-in/SignIn.tsx`):** Email/password login, Google Firebase SSO, and forgot/reset password UI and `form.signin.*` keys (except unused `form.signin.create_account`) remain unchanged.
7. **Out-of-Scope Security Findings:** `GET /api/v1/exams/{exam_id}/users/{user_id}` (`exams/endpoints.py:91-142`), `GET /api/v1/auth/dashboard` (`auth/endpoints.py:96-111`), and `/auth/*` rate-limiting must not be touched in this unit of work.

---

## 7. Code Style & Reference Patterns

### Backend: Retained Admin Endpoint & Pydantic v1 Schema (`fastapi-injector` + Pydantic v1)

Keep Pydantic v1 conventions (`.dict()`, `Schema.from_orm(...)`, `class Config: orm_mode = True`) and `fastapi_injector.Injected(...)`:

```python
# src/Backend/src/api/routers/users/schemas.py (retained UserCreate)
class UserCreate(pydantic.BaseModel):
    role_id: uuid.UUID
    groups: list[uuid.UUID] = pydantic.Field(default_factory=list)
    organizations: list[uuid.UUID] = pydantic.Field(default_factory=list)
    name: str
    email_address: pydantic.EmailStr
    customer_id: str | None = None
    type: models.UserType
    password: pydantic.StrictStr | None = None
    external_id: str | None = None
    state: str | None = None
    region: str | None = None

    class Config:
        orm_mode = True
```

### Backend: Strict-Typed `conftest.py` Bindings & `pytest-asyncio` Regression Pattern

All new async tests and fixtures must use `@pytest.mark.asyncio`, `@pytest_asyncio.fixture`, and full `mypy --strict` type annotations. `TestSettingsModule` must bind `context.CryptContext`, `SecretManager` must use a module-level singleton to stay safe under `@aiocache.cached(ttl=None)`, and `unauthenticated_client` must never be requested alongside `client` in the same test function:

```python
import collections.abc
import fastapi
import injector
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from passlib import context
from api import ports
from api.adapters import memory

_TEST_SECRET_MANAGER = memory.SecretManager()
_TEST_EXTERNAL_AUTH = memory.ExternalAuth()


class TestAuthAndHashingModule(injector.Module):
    @injector.provider
    @injector.singleton
    def provide_secret_manager(self) -> ports.SecretManager:
        return _TEST_SECRET_MANAGER

    @injector.provider
    @injector.singleton
    def provide_external_auth(self) -> ports.ExternalAuth:
        return _TEST_EXTERNAL_AUTH

    @injector.multiprovider
    @injector.singleton
    def provide_hashing_context(self) -> context.CryptContext:
        return context.CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest_asyncio.fixture
async def unauthenticated_client(
    test_app: fastapi.FastAPI,
) -> collections.abc.AsyncIterator[AsyncClient]:
    saved_overrides = dict(test_app.dependency_overrides)
    test_app.dependency_overrides.clear()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://testserver",
        ) as async_client:
            yield async_client
    finally:
        test_app.dependency_overrides.update(saved_overrides)


@pytest.mark.asyncio
async def test_signup_route_removed(unauthenticated_client: AsyncClient) -> None:
    response = await unauthenticated_client.post(
        "/api/v1/users/signup",
        json={
            "name": "Attacker",
            "email_address": "attacker@example.com",
            "password": "Password123!",
            "type": "password",
        },
    )
    assert response.status_code == 405
    assert response.headers["allow"] == "GET"
    assert response.json() == {"detail": "Method Not Allowed"}
```

---

## 8. Commands

Run commands from the target subsystem directory (there is no root build runner):

```bash
# Backend (from src/Backend)
cd /Users/fabriciols/Repos/aira/src/Backend
poetry check --lock
poetry run ruff check src/api/errors.py src/api/helpers/util.py src/api/routers/users/schemas.py tests/integration/test_users_signup_removed.py
poetry run mypy --config-file=mypy.ini --follow-imports=silent src/api/errors.py src/api/helpers/util.py src/api/routers/users/endpoints.py src/api/routers/users/schemas.py tests/integration/test_users_signup_removed.py
poetry run pytest tests/integration/test_users_signup_removed.py -vvv
make test                                      # SQLALCHEMY_WARN_20=1 poetry run pytest -vvv --cov=api --cov-report=term-missing src tests

# Note: Repo-wide `make lint` (`ruff check src tests` + `mypy src tests`) currently fails across 30+
# untouched files due to pre-existing errors (plus 1 pre-existing PLR0912 in users/endpoints.py:797
# and 16 ruff / 14 mypy pre-existing errors in tests/conftest.py). Verify zero new diagnostics in both.

# Frontend (from src/Frontend)
cd /Users/fabriciols/Repos/aira/src/Frontend
pnpm lint
pnpm exec tsc --noEmit
pnpm build
rg "ENDPOINT_SIGNUP|ENDPOINT_CHECK_EMAIL|success_signup|signup_user_error|create_account|['\"\\.]signup['\"\\.]" src/Frontend/src
```

---

## 9. Testing Strategy

Because `db_engine` (`tests/conftest.py:194-209`) is **session-scoped** without per-test transaction rollback and `Base.metadata.create_all` seeds zero `Role` rows, every test must use unique email addresses (`uuid.uuid4()`), seed its own `models.Role` when persisting users, and filter DB assertions by specific `email_address` rather than asserting total table row count `== 0`.

- **Backend Integration Tests (`src/Backend/tests/integration/test_users_signup_removed.py`):**
  1. `test_signup_endpoint_removed(unauthenticated_client, session_factory)`: Unauthenticated `POST /api/v1/users/signup` with unique `email_address` returns `405` with header `Allow: GET` and body `{"detail": "Method Not Allowed"}`, and `select(models.User).where(models.User.email_address == target_email)` returns `None`.
  2. `test_check_email_endpoint_removed_no_enumeration(unauthenticated_client, session_factory)`: Seed a `models.Role` (`scopes=["admin"]`) and a `models.User` (`external_id=None`, `customer_id=None`, `type=models.UserType.PASSWORD`, `role_id=role.id`, `name=...`, `email_address=existing_email`, `state=None`, `region=None`) via `session_factory`; assert unauthenticated `GET /api/v1/users/check_email/{existing_email}` and `GET /api/v1/users/check_email/{unknown_email}` (for non-slash valid emails) both return `404` with identical `{"detail": "Not Found"}` payloads, and `GET /api/v1/users/check_email/exams` returns `403` (`{"detail": "Not authenticated"}`).
  3. `test_openapi_excludes_removed_signup_routes_and_schema(unauthenticated_client)`: `GET /openapi.json` returns `200` and does not contain `/api/v1/users/signup`, `/api/v1/users/check_email/{user_email}`, or `components.schemas.SignupUserCreate`.
  4. `test_admin_create_user_rejects_unauthenticated(unauthenticated_client)`: *(Separate test from #5 so `unauthenticated_client` and `client` never share `test_app`.)* `POST /api/v1/users` with no `Authorization` header returns `403` (`{"detail": "Not authenticated"}`), and with a forged `Authorization: Bearer invalid.jwt.token` header returns `401` (`code == "token_expired_or_invalid"`).
  5. `test_admin_create_user_preserves_validation_and_uniqueness(client, session_factory)`: Seed an admin `models.Role` (`scopes=["admin"]`, so `validate_default_user` does not require `groups`/`organizations`) via `session_factory`; verify authenticated admin `POST /api/v1/users` with `type="password"` and valid `password` creates the user (`200`, returning `schemas.UserGet`), rejects malformed `email_address` (`422`, `type == "value_error.email"`), and rejects a second `POST /api/v1/users` with the same `email_address` (`409`, `code == "already_exists"`).
- **Frontend Verification (`src/Frontend/`):**
  - No Jest/Vitest runner is configured in `src/Frontend/package.json`.
  - Verify TypeScript symbol removal via `pnpm exec tsc --noEmit`, ESLint via `pnpm lint`, Next.js production bundle & JSON validity across all three locales via `pnpm build`, and static i18n key absence (returning exit code `1` / zero matches) via `rg "ENDPOINT_SIGNUP|ENDPOINT_CHECK_EMAIL|success_signup|signup_user_error|create_account|['\"\\.]signup['\"\\.]" src/Frontend/src`.

---

## 10. Boundaries

- **Always:**
  - Keep all edits scoped to the files listed in Section 3.
  - Remove dead i18n keys identically across **all three** locale bundles (`en-US`, `pt-BR`, `es-ES`), stripping trailing commas on `form.json:12` and `toast.json:9` so JSON parsing succeeds.
  - Decorate every new async test with `@pytest.mark.asyncio` and async fixture with `@pytest_asyncio.fixture`, never co-request `client` and `unauthenticated_client` in the same test function, and ensure full strict type annotations on all new code.
- **Ask first:**
  - Touching any existing fixture behavior in `src/Backend/tests/conftest.py` beyond binding `CryptContext` + singleton `memory.SecretManager`/`ExternalAuth` in `test_app` and adding `unauthenticated_client`.
  - Removing `toast.errors.auth.email_already_registered` (`toast.json:69`) or any other translation key not listed in Section 3.
  - Fixing pre-existing lint/mypy errors in out-of-scope Backend files or modifying any dependency version in `pyproject.toml`, `poetry.lock`, `package.json`, or `pnpm-lock.yaml`.
- **Never:**
  - Read, log, or commit `.env` files, `src/Backend/aira-sa-local-access-key.json`, `src/IAC/terraform.tfstate*`, `src/IAC/{terraform.tfvars,backend.tf,variables.tf}`, `src/Agent/deploy/deploy.py`, or `local_pubsub_forwarder.py`.
  - Point `_DATABASE_TEST_URI` at a shared/non-disposable database (`tests/conftest.py` runs `metadata.drop_all`).
  - Use Pydantic v2 APIs (`model_dump`, `model_validate`, `ConfigDict`, `@field_validator`) in `src/Backend/`.
  - Modify out-of-scope endpoints (`/exams/{exam_id}/users/{user_id}`, `/auth/dashboard`, `/auth/*`).

---

## 11. Success Criteria

- [ ] `signup` (`endpoints.py:347-407`), `delete` / `check_email` (`endpoints.py:410-423`), `SignupUserCreate` (`schemas.py:149-175`), `UserAlreadyExists` (`errors.py:296-306`), `InvalidEmail` (`errors.py:309-320`), `validate_email` (`util.py:47-50`), and orphaned `util`/`errors` imports are completely removed from `src/Backend/src/`.
- [ ] `ENDPOINT_SIGNUP`, `ENDPOINT_CHECK_EMAIL`, `form.signup`, `form.signin.create_account`, `toast.success.auth.success_signup`, and `toast.errors.auth.signup_user_error` are removed across `src/Frontend/src/` (`en-US`, `pt-BR`, `es-ES`) with valid JSON formatting.
- [ ] Unauthenticated `POST /api/v1/users/signup` returns `405` (`Allow: GET`) without creating a DB record for that email, and `GET /api/v1/users/check_email/{email}` returns `404` identically for existing and unknown valid non-slash emails.
- [ ] `/openapi.json` contains neither deleted path nor `SignupUserCreate`.
- [ ] Retained `POST /api/v1/users` rejects unauthenticated callers (`403`/`401`) and continues to create password users (`200`), reject invalid emails (`422`), and reject duplicate emails (`409` `already_exists`) for `"admin"` callers.
- [ ] Backend `make test`, `poetry check --lock`, and targeted `ruff check` + `mypy --config-file=mypy.ini --follow-imports=silent` pass with 0 errors on clean/new files (`errors.py`, `helpers/util.py`, `users/schemas.py`, `test_users_signup_removed.py`) and zero new diagnostics on `users/endpoints.py` and `tests/conftest.py`.
- [ ] Frontend `pnpm lint`, `pnpm exec tsc --noEmit`, `pnpm build`, and the static `rg` check pass in `src/Frontend/`.

---

## 12. Open Questions

1. **Dead Sign-In CTA Key (`form.signin.create_account`) vs. `email_already_registered`:** Confirm whether removing `form.signin.create_account` (`"Don't have an account? Sign up for free"` at `form.json:13`) while keeping `toast.errors.auth.email_already_registered` (`toast.json:69`, also currently unreferenced in `src/Frontend/src/`) matches your preference, or if both should be removed.
2. **Test Harness Additions (`tests/conftest.py`):** Confirm Assumption 4 and Section 3.5 — binding `CryptContext` + a module-level singleton `memory.SecretManager`/`ExternalAuth` in `test_app` and adding `unauthenticated_client` (with `ASGITransport(app=test_app)`) while leaving existing `client` usages unchanged.
