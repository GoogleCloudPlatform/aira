# Intent: Remove Unauthenticated Signup and Email-Check Endpoints

**Status:** Confirmed, Source-Reconciled & Doubt-Verified  
**Date:** 2026-11-13

## Detected Stack & Locked Versions

- **Backend (`src/Backend/pyproject.toml`, `src/Backend/poetry.lock`, `src/Backend/mypy.ini`):** Python `>=3.11,<3.14`, `fastapi` `0.115.6` (`^0.115.0`), `starlette` `0.41.3`, `pydantic` `1.10.19` (`^1.10.9` with `extras = ["email"]`, `email-validator` `2.2.0`), `sqlalchemy` `2.0.37` (`^2.0.25`), `fastapi-injector` `0.6.2` (`^0.6.0`), `fastapi-pagination` `0.12.34` (`^0.12.19`), `passlib` `1.7.4` (`bcrypt` `4.2.1`), `httpx` `0.27.2` (`^0.27.0`), `pytest` `8.3.4`, `pytest-asyncio` `0.23.8` (`asyncio_mode = "strict"` at `pyproject.toml:119`), `ruff` `0.4.10` (`^0.4.1`), `mypy` `1.13.0` (`^1.10.0`, `strict = true` at `mypy.ini:4`).
- **Frontend (`src/Frontend/package.json`, `src/Frontend/pnpm-lock.yaml`):** Node `>=20`, `pnpm` `>=9.0.0` (`packageManager: "pnpm@9.0.2"` at `package.json:5`, `lockfileVersion: '9.0'`), `next` `14.2.2`, `next-intl` `3.9.4`, `typescript` `5.4.2`.

## Background & Security Finding

A security review identified two unauthenticated endpoints in `src/Backend/src/api/routers/users/endpoints.py` (mounted under `/api/v1/users` in `src/Backend/src/api/factory.py:62`):

- **`GET /api/v1/users/check_email/{user_email}`** (`endpoints.py:410-423`, handler `delete`): Has no `fastapi.Security` dependency and returns `200 OK` when the email is unknown vs. raising `UserAlreadyExists` (`409` via `src/Backend/src/api/middleware.py:202-210`) when registered, acting as a direct unauthenticated email-enumeration oracle.
- **`POST /api/v1/users/signup`** (`endpoints.py:347-407`, handler `signup`): Has no `fastapi.Security` dependency, assigns the `user` role in the hardcoded `"Escola Senai"` organization and `"Senai 3EM"` group (from `src/Backend/fixture.py:52-65`), logs raw `user_dict` payloads (including plaintext passwords at `endpoints.py:396`), and immediately activates the account so an unauthenticated caller can obtain a valid student JWT.

## Confirmed Statement of Intent (Reconciled)

- **Outcome:** Delete `POST /api/v1/users/signup` (`src/Backend/src/api/routers/users/endpoints.py:347-407`) and `GET /api/v1/users/check_email/{user_email}` (`src/Backend/src/api/routers/users/endpoints.py:410-423`) outright, along with dead signup-only artifacts:
  - Backend: `SignupUserCreate` (`src/Backend/src/api/routers/users/schemas.py:149-175`), now-unused `errors` and `util` imports in `src/Backend/src/api/routers/users/schemas.py:10-11` and `util` import in `src/Backend/src/api/routers/users/endpoints.py:18`, `UserAlreadyExists` and `InvalidEmail` (`src/Backend/src/api/errors.py:296-320`), and `validate_email` (`src/Backend/src/api/helpers/util.py:47-50`).
  - Frontend: `ENDPOINT_SIGNUP` and `ENDPOINT_CHECK_EMAIL` (`src/Frontend/src/constants/endpoints.ts:27-28`), plus unused signup translation entries (`form.signup` at `form.json:15-25`, `form.signin.create_account` at `form.json:13`, `toast.success.auth.success_signup` at `toast.json:10`, and `toast.errors.auth.signup_user_error` at `toast.json:68`) across `en-US`, `pt-BR`, and `es-ES` under `src/Frontend/src/libs/i18n/languages/` (removing the preceding trailing commas on `form.json:12` and `toast.json:9`).
- **User:** School administrators, educators, and students whose tenants and data would otherwise be exposed to unauthenticated account minting and email enumeration.
- **Why now:** Security review flagged leftover `"Escola Senai"` PoC endpoints that act as an unauthenticated email-enumeration oracle, mint active `user`-role sessions on demand, and log plaintext signup payloads.
- **Success:**
  - Regression tests verify (using separate unauthenticated vs. admin tests so `client` and `unauthenticated_client` never collide on `test_app.dependency_overrides`):
    1. Unauthenticated `POST /api/v1/users/signup` returns `405 Method Not Allowed` with header `Allow: GET` (first partial match against `@router.get("/{user_id}")` at `endpoints.py:274` in Starlette `0.41.3` before auth/UUID validation) and creates no user row for that email.
    2. Unauthenticated `GET /api/v1/users/check_email/{email}` returns `404 Not Found` identically for both existing and non-existent **valid email addresses without `/` in the local-part** (and leaks zero enumeration signal for slash-containing local-parts or literal `"exams"` / `"exams-results"`).
    3. Unauthenticated `POST /api/v1/users` is rejected (`403` without `Authorization` header via `HTTPBearer`, `401` on forged Bearer token via `auth.get_token`), while authenticated admin `POST /api/v1/users` (`src/Backend/src/api/routers/users/endpoints.py:294-345`) still creates password users (`200`), validates emails via `pydantic.EmailStr` (`422`), and enforces duplicate-email rejection (`409` `AlreadyExists`).
  - Backend `make test`, `poetry check --lock`, and targeted `ruff check` + `mypy --config-file=mypy.ini --follow-imports=silent` pass with **0 errors** on all clean/new touched files (`src/api/errors.py`, `src/api/helpers/util.py`, `src/api/routers/users/schemas.py`, `tests/integration/test_users_signup_removed.py`) and **zero new** diagnostics in `src/api/routers/users/endpoints.py` or `tests/conftest.py`. *(Note: Repo-wide `make lint` currently fails across 30+ untouched files due to pre-existing lint/type debt outside this scope.)*
  - Frontend `pnpm lint`, `pnpm exec tsc --noEmit`, `pnpm build`, **and** a repo-wide static search covering single quotes, double quotes, and dot-paths (`rg "ENDPOINT_SIGNUP|ENDPOINT_CHECK_EMAIL|success_signup|signup_user_error|create_account|['\"\\.]signup['\"\\.]" src/Frontend/src`) pass.
- **Constraint:** Accounts remain strictly admin-provisioned (`POST /api/v1/users` and CSV batch import `PUT /api/v1/users/batch`) with no DB schema migrations and no changes to existing login/password-reset flows (`POST /api/v1/auth/token`, `/refresh`, `/forgot`, `/reset`).
- **Out of scope:** Public self-registration, email-verification flows, `/auth/*` rate-limiting, pre-existing out-of-scope lint/mypy debt across untouched Backend modules, and the separate authorization findings on `GET /api/v1/exams/{exam_id}/users/{user_id}` (`src/Backend/src/api/routers/exams/endpoints.py:91-142`) and `GET /api/v1/auth/dashboard` (`src/Backend/src/api/routers/auth/endpoints.py:96-111`).

## Technical Decisions & Source-Verified Rationale

1. **No Public Self-Registration in AIRA**
   - Self-service signup is leftover PoC scaffolding, not a product requirement; we will not build email verification, invite gates, or signup rate-limiting.
   - `ENDPOINT_SIGNUP` and `ENDPOINT_CHECK_EMAIL` are never imported outside `src/Frontend/src/constants/endpoints.ts`, `src/Agent/` and `src/IAC/` contain zero references to `signup` or `check_email`, and `src/Frontend/src/components/sign-in/SignIn.tsx` only exposes email/password login and Google SSO (both requiring pre-provisioned user records in `src/Backend/src/api/routers/auth/crud.py:81-126`).

2. **Delete Outright Rather Than Gate Behind Admin Auth or Feature Flags**
   - `POST /api/v1/users` (`endpoints.py:294-345`) already enforces `dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])]`, validates `email_address: pydantic.EmailStr` on `UserCreate` (`users/schemas.py:133`, returning `422` on malformed emails via `pydantic[email]` `1.10.19`), and catches `sqlalchemy.exc.IntegrityError` on `await self._session.flush()` inside `UserRepository.create` (`src/Backend/src/api/adapters/sqlalchemy/user.py:89-92`) to raise `errors.AlreadyExists` (`409`, `src/Backend/src/api/errors.py:102-112`).
   - Keeping `signup` behind `admin` scope or an env toggle would leave dead `"Escola Senai"` / `"Senai 3EM"` fixture coupling and the plaintext-password `logger.info(user_dict)` leak in the codebase.

3. **Exact Post-Deletion Routing Behavior (`Starlette 0.41.3` + `FastAPI 0.115.6`)**
   - **`POST /api/v1/users/signup` -> `405 Method Not Allowed` (`Allow: GET`):** Remaining single-segment routes `@router.get("/{user_id}")` (`endpoints.py:274`), `@router.delete("/{user_id}")` (`L426`), and `@router.patch("/{user_id}")` (`L458`) are three separate `APIRoute` instances using untyped Starlette path syntax `"/{user_id}"` (default `str` convertor matching `[^/]+`, rather than `"/{user_id:uuid}"`) with single-method sets (`{"GET"}`, `{"DELETE"}`, `{"PATCH"}`). Starlette `0.41.3` `Router.app` keeps the **first** `Match.PARTIAL` route (`GET /{user_id}` at `L274`), returning `405` with `Allow: GET` before FastAPI `Security` dependencies or Pydantic `uuid.UUID` path validation run.
   - **`GET /api/v1/users/check_email/{email}` -> `404 Not Found` (for valid emails without `/`):** Under `/api/v1/users`, `"check_email/{email}"` has two segments when `{email}` contains no `/`. The only 2-segment routes on `users_router` are `GET /{user_id}/exams` (`L597`) and `GET /{user_id}/exams-results` (`L670`), so any non-slash valid email fails to match literal `"exams"` / `"exams-results"` and returns `404` regardless of whether the email exists in PostgreSQL.
     - *Non-enumerating edge cases:* (a) Literal `/api/v1/users/check_email/exams` or `/exams-results` matches `/{user_id}/exams` with `user_id="check_email"` and returns `403` via `HTTPBearer` without querying `users.email_address`. (b) Valid RFC 5322 emails containing `/` in the local-part (even URL-encoded `%2F`, which ASGI percent-decodes into `scope["path"]`) expand into 3+ path segments under `/api/v1/users` and return `404` (most segment shapes), `403` (4-segment `.../exams/{exam_id}/questions` at `L726`), or `405` (`Allow: POST` on 5-segment `.../exams/{exam_id}/questions/{question_id}` at `L791`), never querying `users.email_address`.

4. **Remove Dead Signup-Only Code, Unused Imports, & Translations**
   - Backend: Remove `SignupUserCreate`, `UserAlreadyExists`, `InvalidEmail`, and `util.validate_email`, plus the orphaned `util` / `errors` imports in `users/endpoints.py:18` and `users/schemas.py:10-11` so `ruff check` (`F401`) passes.
   - Frontend: Remove `ENDPOINT_SIGNUP` and `ENDPOINT_CHECK_EMAIL` (`endpoints.ts:27-28`) and dead signup i18n keys (`form.signup`, `form.signin.create_account`, `toast.success.auth.success_signup`, `toast.errors.auth.signup_user_error`) in `en-US`, `pt-BR`, and `es-ES` (removing trailing commas on `form.json:12` and `toast.json:9` since `create_account` and `success_signup` are final object keys). Because `src/Frontend/` does **not** declare `global.d.ts` `IntlMessages` augmentation for `next-intl` `3.9.4`, `tsc --noEmit` will not catch missing translation keys; pair `tsc --noEmit` and `pnpm build` with a literal ripgrep check across `src/Frontend/src/`.

5. **Unauthenticated Regression Test Isolation & `conftest.py` DI Bindings**
   - **Shared `test_app.dependency_overrides` state:** `src/Backend/tests/conftest.py:288` sets `test_app.dependency_overrides[auth.get_token] = override_get_token` on the function-scoped `test_app`. Any test function requesting both `client` and `unauthenticated_client` would overwrite `dependency_overrides` on the shared `test_app`; unauthenticated and authenticated assertions must live in separate test functions.
   - **Missing `CryptContext` binding in `TestSettingsModule`:** Production `SettingsModule.provide_hashing_context` (`dependencies.py:69-77`) binds `context.CryptContext(schemes=["bcrypt"], deprecated="auto")`, whereas `TestSettingsModule` (`tests/conftest.py:250-256`) omits it. Without binding `CryptContext` in `TestSettingsModule`, `injector` auto-binds `CryptContext()` with empty `schemes=()`, causing `POST /api/v1/users` (`type="password"`) to raise `KeyError` (`500`) and leaving `pyinstrument.Profiler` in `middleware.py:288-296` active under `env="local"`, which crashes subsequent requests with `RuntimeError: There is already a profiler running`.
   - **Singleton `memory.SecretManager()` for `@aiocache.cached(ttl=None)`:** `auth.get_public_key` (`auth.py:26-36`) caches public keys indefinitely keyed on `str(secrets)` (`<...SecretManager object at 0x...>`), while `memory.SecretManager()` (`adapters/memory/secret_manager.py:37-57`) generates a fresh 2048-bit RSA keypair per instance when `tests/private.pem` is absent. `tests/conftest.py` should reuse a module-level `memory.SecretManager()` singleton across `test_app` instances to avoid per-test RSA generation overhead and memory-address reuse cache collisions.
   - **Session-scoped `db_engine` without per-test rollback:** `db_engine` (`tests/conftest.py:194-209`) runs `drop_all`/`create_all` once per session with zero seeded `Role` rows; tests must seed their own `models.Role` rows and assert email-specific `select(models.User).where(models.User.email_address == ...)` queries rather than total table counts.

6. **Strict Scope Boundary With Chained Findings & Pre-Existing Repo Lint Debt**
   - The IDOR in `GET /api/v1/exams/{exam_id}/users/{user_id}`, missing RBAC scopes on `GET /api/v1/auth/dashboard`, `/auth/*` rate-limiting, and pre-existing lint/type errors in 30+ unrelated Backend files remain separate work items.

## Surfaced Conflicts Between Official Docs & Existing Code

1. **`httpx.AsyncClient(transport=ASGITransport(app=...))` (Official Docs) vs. `AsyncClient(app=...)` (`tests/conftest.py:290`)**
   - **Official docs (`fastapi` `0.115.6` & `httpx` `0.27.2`):** FastAPI's async testing guide and HTTPX `0.27.0+` deprecate `AsyncClient(app=...)` in favor of `AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`.
   - **Existing codebase:** `src/Backend/tests/conftest.py:290` uses `AsyncClient(app=test_app, base_url="http://testserver")` and suppresses `DeprecationWarning` in `src/Backend/pyproject.toml:131`.
   - **Selected approach:** Construct the new `unauthenticated_client` fixture using `AsyncClient(transport=ASGITransport(app=test_app), base_url="http://testserver")` per `httpx` `0.27.2` docs while leaving existing `client` usages in `conftest.py` untouched, and never co-request `client` and `unauthenticated_client` in the same test.

2. **`@pytest.mark.asyncio` (`pytest-asyncio` `0.23.8` Strict Mode in Repo) vs. `@pytest.mark.anyio` (FastAPI Docs Default)**
   - **Official FastAPI docs:** Examples in FastAPI's *Async Tests* guide use `@pytest.mark.anyio`.
   - **Existing codebase & `pytest-asyncio` `0.23.8` docs:** `src/Backend/pyproject.toml:119` configures `pytest-asyncio` with `asyncio_mode = "strict"`, and `tests/conftest.py:187-191` defines a session-scoped `event_loop` fixture with `@pytest_asyncio.fixture` DB/app fixtures. Under `pytest-asyncio` strict mode, new async regression tests **must** use `@pytest.mark.asyncio` (and `@pytest_asyncio.fixture` for any new async fixture) so they share the session-scoped `asyncio` event loop with `conftest.py` fixtures.

## Official Sources & Citations

- **Starlette Routing (`0.41.3`) — Default `str` Convertor, Route Priority, & `405` Partial Match**
  - Docs: <https://starlette.dev/routing/#path-parameters> and <https://starlette.dev/routing/#route-priority>
    > "By default this will capture characters up to the end of the path or the next `/`. You can use convertors to modify what is captured. The available convertors are: `str` returns a string, and is the default."
    > "Incoming paths are matched against each `Route` in order."
  - Upstream tag source (`0.41.3`): <https://raw.githubusercontent.com/encode/starlette/0.41.3/starlette/routing.py> (`Route.matches`, `Route.handle`, `Router.app`)
    > `# Handle partial matches. These are cases where an endpoint is able to handle the request, but is not a preferred option. We use this in particular to deal with "405 Method Not Allowed".`
- **FastAPI (`0.115.6`) — Path Parameter Evaluation Order & OAuth2 Security Scopes**
  - Path evaluation order: <https://fastapi.tiangolo.com/tutorial/path-params/#order-matters>
    > "Because path operations are evaluated in order, you need to make sure that the path for `/users/me` is declared before the one for `/users/{user_id}`: Otherwise, the path for `/users/{user_id}` would match also for `/users/me`, 'thinking' that it's receiving a parameter `user_id` with a value of `'me'`."
  - Security scopes (`fastapi.Security(..., scopes=["admin"])`): <https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/>
- **FastAPI (`0.115.6`) — Dependency Overrides in Tests**
  - Docs: <https://fastapi.tiangolo.com/advanced/testing-dependencies/#use-the-app-dependency-overrides-attribute>
    > "For these cases, your FastAPI application has an attribute `app.dependency_overrides`, it is a simple `dict`... Then you can reset your overrides (remove them) by setting `app.dependency_overrides` to be an empty `dict`: `app.dependency_overrides = {}`"
- **FastAPI (`0.115.6`) & HTTPX (`0.27.2`) — Async ASGI Testing & `ASGITransport`**
  - FastAPI Async Tests: <https://fastapi.tiangolo.com/advanced/async-tests/#httpx>
    > `async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:`
  - HTTPX Transports: <https://www.python-httpx.org/advanced/transports/#asgi-transport>
  - HTTPX `0.27.2` Changelog (`0.27.0` deprecation): <https://raw.githubusercontent.com/encode/httpx/0.27.2/CHANGELOG.md>
    > "The `app=...` shortcut has been deprecated. Use the explicit style of `transport=httpx.WSGITransport()` or `transport=httpx.ASGITransport()` instead."
- **`pytest-asyncio` (`0.23.8`) — Strict Discovery Mode**
  - Docs: <https://pytest-asyncio.readthedocs.io/en/v0.23.8/concepts.html#strict-mode>
    > "In strict mode pytest-asyncio will only run tests that have the `asyncio` marker and will only evaluate async fixtures decorated with `@pytest_asyncio.fixture`. Test functions and fixtures without these markers and decorators will not be handled by pytest-asyncio."
- **`fastapi-injector` (`0.6.2`) — `Injected` Wrapper Over `Depends`**
  - Upstream tag docs: <https://raw.githubusercontent.com/matyasrichter/fastapi-injector/0.6.2/README.md>
    > "Under the hood, `Injected` is `Depends`, so you can use it anywhere `Depends` can be used."
- **Pydantic (`1.10.19`) — `EmailStr` Validation on `UserCreate`**
  - Docs: <https://docs.pydantic.dev/1.10/usage/types/#pydantic-types>
    > "`EmailStr`: requires `email-validator` to be installed; the input string must be a valid email address, and the output is a simple string"
- **SQLAlchemy (`2.0.37`) — `Session.flush()` Constraint Enforcement**
  - Docs: <https://docs.sqlalchemy.org/en/20/orm/session_basics.html#flushing>
    > "A `Session` flush can be forced at any time by calling the `Session.flush()` method."
- **`next-intl` (`3.9.4`) — Optional `IntlMessages` TypeScript Augmentation**
  - v3 Docs: <https://v3.next-intl.dev/docs/workflows/typescript#messages>
    > "Messages can be strictly typed to ensure you’re using valid keys... To enable this validation, add a global type definition file in your project root (e.g. `global.d.ts`): `declare global { interface IntlMessages extends Messages {} }`"

## Unverified Items (`UNVERIFIED`)

- **`UNVERIFIED` — Out-of-repo HTTP callers & live environment traffic:** In-repo searches across `src/Frontend/`, `src/Agent/`, `src/IAC/`, and `src/Backend/tests/` found zero callers of `POST /api/v1/users/signup` or `GET /api/v1/users/check_email/{user_email}`, but official docs and local source cannot confirm whether external scripts, third-party integrations, or live Cloud Run traffic invoke these routes (gitignored `src/IAC/terraform.tfvars` and GCP Cloud Logging were not inspected).
- **`UNVERIFIED` — External `/openapi.json` contract consumers:** FastAPI `0.115.6` automatically removes deleted routes and unreferenced Pydantic models (`SignupUserCreate`) from `/openapi.json`; whether any external client generator or contract test outside this repository pins those OpenAPI entries cannot be confirmed from docs or repo code.
- **`UNVERIFIED` — Dynamic/template-literal `next-intl` key lookups:** Because `IntlMessages` global type augmentation is not enabled in `src/Frontend/` and `next-intl` `3.9.4` provides no build-time unused/missing-key compiler error without it, confirming `form.signup`, `form.signin.create_account`, `toast.success.auth.success_signup`, and `toast.errors.auth.signup_user_error` are unused relies on static repo search rather than a framework compiler guarantee.
- **`UNVERIFIED` — `fastapi-pagination` (`0.12.34`) `add_pagination(app)` internals:** Official `fastapi-pagination` `0.12.34` docs were not fetched to verify internal route inspection during `fastapi_pagination.add_pagination(app)` (`src/Backend/src/api/factory.py:79`); in-repo inspection shows neither deleted endpoint uses `Page[...]` response models.
