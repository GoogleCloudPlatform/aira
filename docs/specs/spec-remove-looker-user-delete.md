# Spec: Remove Unauthenticated Looker User-Deletion Endpoints and `looker-sdk` Admin Client

**Status:** Draft — Doubt-Verified & Awaiting Human Review (Phase 1: Specify)  
**Date:** 2026-11-16  
**Source Intent:** [`docs/intents/intent-remove-looker-user-delete.md`](../intents/intent-remove-looker-user-delete.md)  
**Scope Check (Phase 0):** Single capability (surgical removal of the unauthenticated Looker user-deletion surface, unwired Pub/Sub feeder endpoint, and `looker-sdk` Admin REST client while preserving `GET /api/v1/auth/dashboard` SSO embed URL signing); capability-map decomposition is not required.

---

## Assumptions Surfaced

1. **No live Cloud Scheduler or Pub/Sub push callers depend on the removed Looker routes:** Neither `POST /api/v1/auth/user/looker/_handle` nor `GET /api/v1/auth/users/looker` is wired in `src/IAC/06-message_service.tf` or called anywhere in `src/Frontend/`, `src/Agent/`, or `src/Backend/tests/` (`UNVERIFIED` against manual/out-of-band GCP Console resources; any manual job/subscription would receive `404 Not Found` and should be deleted).
2. **Hard deletion (`404 Not Found`) over stub `410 Gone` handlers:** Deleting both routes outright so Starlette `0.41.3` returns its standard `404 Not Found` (`{"detail": "Not Found"}`) across all HTTP methods is preferred over maintaining dead stub endpoints.
3. **Cloud Build deploys both update existing `backend` services and bootstrap brand-new environments:** Per human confirmation and Google Cloud SDK's `SecretEnvVarChanges` (`googlecloudsdk/command_lib/run/config_changes.py:776-787`, `_PruneMapping`: `if var_or_path in mapping: del mapping[var_or_path]`) and v2 `AdjustContainer` (`googlecloudsdk/command_lib/run/v2/config_changes.py:819-835`, `if env_var.name in self.removes: continue`), pairing `--remove-secrets=LOOKERSDK_BASE_URL,LOOKERSDK_CLIENT_ID,LOOKERSDK_CLIENT_SECRET` with `--update-secrets=...` in `src/Backend/cloudbuild.yaml:50` is a silent no-op when creating a brand-new Cloud Run service and actively detaches `LOOKERSDK_*` before applying `--update-secrets` on existing services (without `clear_others=True` wiping any operator-added secrets).
4. **Resolving stale `user.county` via `getattr(user, "county", None)` preserves the exact Looker `user_attributes` payload:** Migration `80dc3596cd72` dropped `users.county`, leaving `user.county` at `src/Backend/src/api/adapters/google/looker.py:109` broken under both `mypy --strict` (`[attr-defined]`) and runtime `GET /api/v1/auth/dashboard` (`AttributeError`). Using 3-argument `getattr(user, "county", None)` emits `"county": null` (identical to pre-migration `NULL` rows) and passes both `ruff` (`B009` applies only to 2-argument `getattr`) and `mypy --strict`.

---

## 1. Objective

Eliminate an unauthenticated arbitrary Looker user-deletion vulnerability and its unwired batch-deletion feeder route in the `auth` router, and remove Looker Admin REST API credentials and `looker-sdk` from the Backend runtime:

- **`POST /api/v1/auth/user/looker/_handle`** (`src/Backend/src/api/routers/auth/endpoints.py:182-194`, handler `handle_delete_users_pubsub`): Unauthenticated endpoint on a `--allow-unauthenticated` Cloud Run service (`src/Backend/cloudbuild.yaml:52`) that validates `PubsubRequest` (`src/Backend/src/api/routers/schemas.py:17-23`), base64-decodes `body.message.data`, extracts `user_id` via `PubsubDeleteUserData`, and calls `LookerDashboard.delete_looker_user(data.user_id)` -> `self._looker.delete_user(user_id)` (`DELETE /users/{user_id}`), allowing any internet caller to permanently delete non-embed Looker users and administrators via `{"message":{"data":"eyJ1c2VyX2lkIjoiMSJ9","messageId":"1"},"subscription":"sub"}`.
- **`GET /api/v1/auth/users/looker`** (`src/Backend/src/api/routers/auth/endpoints.py:158-179`, handler `set_delete_users_pubsub`): Legacy scheduler endpoint calling `LookerDashboard.get_all_looker_users()` (`search_users(embed_user=True)`) and publishing `DeleteLookerUserMessage` to `settings.get("pubsub_delete_user_topic")`—an unset variable in production that causes `MessagePublisher.publish` (`src/Backend/src/api/adapters/google/pubsub.py:31-36`) to fall back to `self.topic_path` (`_PUBSUB_TOPIC` / `processor_queue`), polluting the exam audio-processing queue.

**Target Users Protected:** Looker administrators, educators, and school/network managers whose Looker accounts, schedules, dashboards, and BI access must not be exposed to unauthenticated deletion or unnecessary Looker Admin API3 credentials inside the public Backend container.

---

## 2. Tech Stack (Locked Versions in Scope)

- **Backend (`src/Backend/pyproject.toml`, `poetry.lock`, `mypy.ini`, `Dockerfile`, `Makefile`):** Python `>=3.11,<3.14` (`python:3.11-slim` builder at `Dockerfile:1`, `python:3.11-slim-bookworm` runtime at `Dockerfile:31`), Poetry `2.3.4` (`lock-version = "2.1"` at `poetry.lock:6134`; `POETRY_VERSION=2.0.1` + `poetry-plugin-export==1.8.0` in `Dockerfile:8,22`; `pex` `2.27.1` / `^2.3.1` at `pyproject.toml:80` in `Makefile:6-18` and `Dockerfile:29`), `fastapi` `0.115.6` (`^0.115.0`), `starlette` `0.41.3`, `pydantic` `1.10.19` (`^1.10.9`), `sqlalchemy` `2.0.37` (`^2.0.25`, `asyncpg`), `injector` `0.20.1` (`^0.20.1`), `fastapi-injector` `0.6.2` (`^0.6.0`), `fastapi-pagination` `0.12.34` (`^0.12.19`), `google-cloud-pubsub` `2.25.0` (`^2.18.1`), `httpx` `0.27.2` (`^0.27.0`), `pytest` `8.3.4`, `pytest-asyncio` `0.23.8` (`asyncio_mode = "strict"` at `pyproject.toml:119`), `ruff` `0.4.10` (`^0.4.1`), `mypy` `1.13.0` (`^1.10.0`, `strict = true` at `mypy.ini:4`).
- **Removed Backend Dependency:** `looker-sdk` `24.20.0` (`^24.0.0` at `pyproject.toml:52`) and its sole exclusive transitive dependency `cattrs` `24.1.2` (`poetry.lock:441,2600-2616`).
- **Frontend (`src/Frontend/package.json` — untouched, verified compatible):** `@looker/embed-sdk` `^1.8.5` (`package.json:20`), calling `GET /api/v1/auth/dashboard` (`src/Frontend/src/constants/endpoints.ts:3`, `src/Frontend/src/libs/looker/looker.ts:11-15`).
- **Deployment & Local Stack (`src/Backend/cloudbuild.yaml`, `src/Backend/docker-compose.yaml`):** Google Cloud SDK `gcloud run deploy` (`gcr.io/google.com/cloudsdktool/cloud-sdk`), Docker Compose (`api` + `pubsub` emulator).

---

## 3. Where It Hooks In & Affected Project Structure

### System Hook-In Points

1. **FastAPI Auth Router & OpenAPI Generation (`src/Backend/src/api/factory.py:61` -> `routers/auth/endpoints.py`):**
   - `app.include_router(routers.auth_router, prefix="/api/v1/auth")` mounts `auth_router`.
   - Deleting `@router.get("/users/looker")` (`endpoints.py:158-179`) and `@router.post("/user/looker/_handle")` (`endpoints.py:182-194`) removes both `APIRoute` entries from `auth_router.routes` and from `/openapi.json` `paths`, leaving five literal routes on `auth_router`: `POST /token` (`L28`), `POST /refresh` (`L60`), `GET /dashboard` (`L96`), `POST /forgot` (`L114`), and `POST /reset` (`L141`).
   - Deleting both handlers makes `import base64` (`endpoints.py:7`) and `from api.routers.schemas import PubsubRequest` (`endpoints.py:18`) unused; both imports are removed (`typings` on `L14` remains used by `forgot_password` at `L118`).
   - Because neither `auth_router` (`/api/v1/auth`) nor `base_router` (`/api/v1`, which only defines `GET /healthz` at `routers/endpoints.py:14`) registers any parameterized path convertors, Starlette `0.41.3` `Router.app` (`starlette/routing.py:716-765`) yields `Match.NONE` across all routes (`partial is None`, `redirect_slashes` finds no match) and falls through to `404 Not Found` for every HTTP method on `/api/v1/auth/user/looker/_handle` and `/api/v1/auth/users/looker`.
2. **Auth Schemas & OpenAPI `include_in_schema` Pruning (`src/Backend/src/api/routers/auth/schemas.py`):**
   - `DeleteLookerUserMessage` (`schemas.py:64-70`, stdlib `@dataclasses.dataclass` subclassing `typings.Message`) and `PubsubDeleteUserData` (`schemas.py:73-78`, `pydantic.BaseModel` with `extra=pydantic.Extra.allow`) have zero callers outside the two deleted handlers.
   - Removing them leaves `import dataclasses` (`schemas.py:5`) and `from api import typings` (`schemas.py:12`) unused; both imports are removed.
   - Per FastAPI `0.115.6` `get_fields_from_routes` (`fastapi/openapi/utils.py:425-453`), OpenAPI `components.schemas` collects models only from routes with `include_in_schema=True` (`utils.py:433`). Because `processor_router` sets `include_in_schema=False` on the entire router (`processor/endpoints.py:27`, handlers at `L155-158` and `L359-362`) and `knowledge_base_router`'s `/process-message` sets `include_in_schema=False` (`knowledge_base/endpoints.py:335-337`), `POST /api/v1/auth/user/looker/_handle` was the **sole** `include_in_schema=True` route referencing `PubsubRequest`. Deleting it therefore removes `PubsubRequest` and `PubsubMessage` from `/openapi.json` `components.schemas` as well (`PubsubDeleteUserData` and `DeleteLookerUserMessage` were already absent), while `api.routers.schemas.{PubsubRequest,PubsubMessage}` (`routers/schemas.py:8-24`) remain intact and used at runtime by `processor` and `knowledge_base`.
3. **Hexagonal Port & Google Looker Adapter (`src/Backend/src/api/ports/dashboard.py` & `adapters/google/looker.py`):**
   - `ports.Dashboard` (`ports/dashboard.py:13-38`, re-exported in `ports/__init__.py:7,78`) drops abstract methods `delete_looker_user` (`L28-32`) and `get_all_looker_users` (`L34-38`), plus now-unused `import typing` (`L6`), retaining only `get_signed_url(self, user: models.User, query: datastructures.QueryParams) -> str` (`L18-26`).
   - `LookerDashboard` (`adapters/google/looker.py:61-185`, re-exported in `adapters/google/__init__.py:9,20` and wired in `GoogleModule.provide_looker` at `dependencies.py:674-681` and `InternetlessModule.provide_looker` at `dependencies.py:795-802`) drops `import looker_sdk` (`L15`), `from looker_sdk.sdk.api40 import models as mdls` (`L16`), `self._looker = looker_sdk.init40()` (`L71`), `delete_looker_user` (`L173-178`), and `get_all_looker_users` (`L180-184`).
   - Removing `self._looker = looker_sdk.init40()` eliminates `looker_sdk`'s eager `settings.is_configured()` check (`looker_sdk/__init__.py:57` -> `rtl/transport.py:65-67`, raising `SDKError("Missing required configuration value: base_url")` when `looker.ini` and `LOOKERSDK_BASE_URL` are absent), making `LookerDashboard(looker_host, looker_secret)` pure stdlib initialization.
   - At `looker.py:109`, `"county": user.county` is updated to `"county": getattr(user, "county", None)` so `get_signed_url` does not raise `AttributeError` on `models.User` rows (after migration `80dc3596cd72` dropped `users.county`) and passes `mypy --strict`.
4. **Python Dependency Graph & PEX/Docker Build (`src/Backend/pyproject.toml` & `poetry.lock`):**
   - Running `poetry remove looker-sdk` removes `looker-sdk = "^24.0.0"` (`pyproject.toml:52`) and prunes `looker-sdk` (`24.20.0`) and `cattrs` (`24.1.2`) from `poetry.lock` (`lock-version = "2.1"`), which automatically excludes them from `poetry export --without-hashes` -> `dist/stt.pex` (`Makefile:6-18` and `Dockerfile:29`).
5. **Local Docker Compose & Cloud Build Deployment (`src/Backend/docker-compose.yaml` & `cloudbuild.yaml`):**
   - `src/Backend/docker-compose.yaml` removes `_PUBSUB_DELETE_USER_TOPIC` (`L42`), `LOOKERSDK_BASE_URL` / `LOOKERSDK_CLIENT_ID` / `LOOKERSDK_CLIENT_SECRET` (`L61-63`) from the `api` service environment, and removes the `delete-looker-user-queue` entry (`L150-155`, third of four JSON array objects, leaving valid JSON before `send-email-queue` at `L156-161`) from the `pubsub` emulator `PUBSUB_CONFIG`.
   - `src/Backend/cloudbuild.yaml:50` removes `LOOKERSDK_BASE_URL=lookersdk_base_url:latest`, `LOOKERSDK_CLIENT_ID=lookersdk_client_id:latest`, and `LOOKERSDK_CLIENT_SECRET=lookersdk_client_secret:latest` from `--update-secrets` and adds `--remove-secrets=LOOKERSDK_BASE_URL,LOOKERSDK_CLIENT_ID,LOOKERSDK_CLIENT_SECRET` to the `gcloud run deploy backend` args list.
6. **Test Harness DI Container (`src/Backend/tests/conftest.py`):**
   - `TestGoogleModule` (`tests/conftest.py:164-186`) currently binds `ports.MessagePublisher`, `ports.StorageFactory`, and `ports.GenAI`, but omits `ports.Dashboard`. Because `fastapi_injector.Injected(ports.Dashboard)` (`fastapi_injector/injected.py:11-20`) resolves `ports.Dashboard` per request and `injector.Injector` (`0.20.1`, `injector/__init__.py:645-648,865-870`) defaults to `auto_bind=True`, calling `GET /api/v1/auth/dashboard` in tests currently fails at request time with `TypeError: Can't instantiate abstract class Dashboard...`.
   - Adding `@injector.provider @injector.singleton def provide_looker(self) -> ports.Dashboard` returning `looker.LookerDashboard(looker_host="looker.example.com", looker_secret="test-looker-secret")` to `TestGoogleModule`—with `from api.adapters.google import looker  # noqa: E402` placed contiguously at `conftest.py:21` immediately below `from api.adapters import memory  # noqa: E402` inside the existing `L19-24` import block—wires the real `LookerDashboard` adapter with zero external dependencies and keeps `tests/conftest.py` at its exact baseline diagnostic count (`15` `ruff` / `14` `mypy`).
   - Existing `TestAuthAndHashingModule` (`conftest.py:237-253`) and `unauthenticated_client` (`conftest.py:324-338`) already exist and require no changes.

### Affected Files Map

```text
src/Backend/
├── cloudbuild.yaml                                         # Modify: drop LOOKERSDK_* from --update-secrets; add --remove-secrets=LOOKERSDK_BASE_URL,LOOKERSDK_CLIENT_ID,LOOKERSDK_CLIENT_SECRET
├── docker-compose.yaml                                     # Modify: drop _PUBSUB_DELETE_USER_TOPIC, LOOKERSDK_*, and delete-looker-user-queue emulator block
├── pyproject.toml                                          # Modify (via poetry remove looker-sdk): remove looker-sdk = "^24.0.0"
├── poetry.lock                                             # Modify (via poetry remove looker-sdk): prune looker-sdk (24.20.0) & cattrs (24.1.2)
├── src/api/
│   ├── adapters/google/looker.py                           # Modify: remove looker_sdk imports, self._looker, delete_looker_user, get_all_looker_users; use getattr(user, "county", None)
│   ├── ports/dashboard.py                                  # Modify: remove delete_looker_user, get_all_looker_users, and unused typing import
│   └── routers/auth/
│       ├── endpoints.py                                    # Modify: remove set_delete_users_pubsub, handle_delete_users_pubsub, and unused base64 & PubsubRequest imports
│       └── schemas.py                                      # Modify: remove DeleteLookerUserMessage, PubsubDeleteUserData, and unused dataclasses & typings imports
└── tests/
    ├── conftest.py                                         # Modify (minimal): bind ports.Dashboard -> LookerDashboard in TestGoogleModule
    └── integration/
        └── test_looker_user_delete_removed.py              # Add: async regression tests for removed Looker routes, symbol removal, & retained /auth/dashboard SSO signing

docs/
├── intents/intent-remove-looker-user-delete.md             # Reference intent (existing)
└── specs/spec-remove-looker-user-delete.md                 # This specification
```

---

## 4. Configuration & Limits

### Configuration

- **Removed Runtime Environment Variables & Mounted Secrets:**
  - `LOOKERSDK_BASE_URL` (removed from `src/Backend/docker-compose.yaml:61` and unmounted via `--remove-secrets` in `src/Backend/cloudbuild.yaml:50`).
  - `LOOKERSDK_CLIENT_ID` (removed from `src/Backend/docker-compose.yaml:62` and unmounted via `--remove-secrets` in `src/Backend/cloudbuild.yaml:50`).
  - `LOOKERSDK_CLIENT_SECRET` (removed from `src/Backend/docker-compose.yaml:63` and unmounted via `--remove-secrets` in `src/Backend/cloudbuild.yaml:50`).
  - `_PUBSUB_DELETE_USER_TOPIC` (removed from `src/Backend/docker-compose.yaml:42`; already absent from `cloudbuild.yaml` and `env.example`).
- **Retained Looker Runtime Configuration (Unchanged):**
  - `_LOOKER_HOST` (`settings.get("looker_host", "")` via `SettingsModule` underscore-stripping in `src/Backend/src/api/dependencies.py:42-67`; set in `cloudbuild.yaml:51`, `docker-compose.yaml:48`, and `env.example:24`).
  - `_LOOKER_SECRET` (`settings.get("looker_secret", "")`; mounted as `_LOOKER_SECRET=looker_secret:latest` in `cloudbuild.yaml:50`, `docker-compose.yaml:50`, and `env.example:25`).
- **Cloud Build Secret Flag Ordering for Existing & Greenfield Environments (`src/Backend/cloudbuild.yaml:50`):**
  - Pass `"--remove-secrets=LOOKERSDK_BASE_URL,LOOKERSDK_CLIENT_ID,LOOKERSDK_CLIENT_SECRET"` alongside `"--update-secrets=_BUCKET_PATH=bucket_name:latest,_DATABASE_URI=sql_connection_url:latest,_PUBSUB_TOPIC=processor_queue:latest,_BQ_DATASET=dataset_name:latest,_BQ_TABLE_NAME=table_name:latest,_PUBSUB_CONVERT_TOPIC=conversion_queue:latest,_ORIGIN=front_url:latest,_LOOKER_SECRET=looker_secret:latest,/secrets/api/gcs_sa_key=gcs_sa_key:latest,_SENDGRID_KEY=sendgrid_api_key:latest"`.
  - Per `gcloud run deploy` official rules and `googlecloudsdk/command_lib/run/{config_changes.py:776-787,v2/config_changes.py:819-835}`, `--remove-secrets` and `--update-secrets` are compatible in the same command (`--remove-secrets` applied first), acting as a silent no-op when bootstrapping a brand-new Cloud Run service and detaching `LOOKERSDK_*` on existing services.
- **Terraform Secret Manager Resources (`src/IAC/10-Secrets.tf:344-435` & `src/IAC/02-sa_and_iam.tf:79-103`):**
  - **Untouched.** `google_secret_manager_secret.lookersdk_base_url`, `lookersdk_client_id`, `lookersdk_client_secret`, their `google_secret_manager_secret_version` resources (`10-Secrets.tf:344-435`), and project-level Secret Manager IAM bindings (`02-sa_and_iam.tf:79-103`) remain in Terraform so deployment requires zero `terraform apply` destructive changes and Cloud Run revision rollbacks remain non-breaking.
- **Production Dependency Injection (`src/Backend/src/api/dependencies.py:674-681, 795-802`):**
  - **No changes** to `GoogleModule.provide_looker` or `InternetlessModule.provide_looker`, both of which already construct `google.LookerDashboard(looker_secret=settings.get("looker_secret", ""), looker_host=settings.get("looker_host", ""))`.
- **No Feature Flag:** Looker user-deletion endpoints are permanently deleted; no toggle (e.g., `_ENABLE_LOOKER_USER_DELETE`) is introduced.

### Limits & Constraints

- **Rate Limiting & Request Body Size Limits:** Out of scope and unchanged (Starlette `0.41.3` defaults; no custom body-size or `/api/v1/auth/*` rate-limit middleware added).
- **Authentication & Session Limits on Retained `GET /api/v1/auth/dashboard` (`auth/endpoints.py:96-111`):**
  - Requires a valid RS512 Bearer JWT (`TOKEN_DURATION = 60 minutes` in `auth/crud.py:23`) matching `audience=settings.get("project_id")` whose `sub` (`"<session_uuid>:<generation>"`) resolves via `ports.GetSession` to an existing `models.Session` row (`SESSION_DURATION = 10 days` in `auth/crud.py:22`).
  - Declares `dependencies=[fastapi.Security(auth.get_token)]` with **no** RBAC `scopes=[...]` restriction (preserving existing behavior for any authenticated session).
- **Signed Embed URL Limits & Parameters (`LookerDashboard` in `looker.py:30-171`):**
  - `session_length`: Fixed at `3000` seconds (`50` minutes, JSON-encoded `"3000"`).
  - `force_logout_login`: Fixed at `True` (JSON-encoded `"true"`).
  - `nonce`: Per-request 128-bit random hex string (`json.dumps(uuid.uuid4().hex)`, 32 hex chars inside JSON quotes).
  - `time`: Current Unix epoch timestamp in seconds (`json.dumps(int(time.time()))`).
  - `group_ids`: Fixed Looker group `[2]` (`"[2]"`), with AIRA tenant UUIDs serialized as JSON strings inside `user_attributes["group_ids"]` and `user_attributes["organization_ids"]`.
  - `permissions`: Fixed 9-element list (`access_data`, `clear_cache_refresh`, `download_without_limit`, `mobile_app_access`, `schedule_look_emails`, `see_drill_overlay`, `see_lookml_dashboards`, `see_looks`, `see_user_dashboards`).
  - `src` query parameter: Extracted via `query.get("src", "")` (`""` default when omitted) and URL-encoded onto `/login/embed/<quote_plus(src)>`.
  - Signature: Base64-encoded `HMAC-SHA1` digest over the exact 12-line `\n`-delimited `string_to_sign` (`looker_host`, `path`, `nonce`, `current_time`, `session_length`, `external_user_id`, `permissions`, `models`, `group_ids`, `external_group_id`, `user_attributes`, `access_filters`).

---

## 5. Error Responses & HTTP Contract

### Post-Deletion Responses on Removed Endpoints

| Request | Auth Header | Status | Headers | Response Body | Source |
|---|---|---|---|---|---|
| `POST /api/v1/auth/user/looker/_handle` (valid `PubsubRequest` JSON `{"message": {"data": "eyJ1c2VyX2lkIjoiMSJ9", "messageId": "1"}, "subscription": "projects/test/subscriptions/sub"}`, minimal/malformed JSON `{"message": {"data": "..."}}`, or empty body) | None or any | `404 Not Found` | Standard JSON headers | `{"detail": "Not Found"}` | Starlette `0.41.3` `Router.app` (`Match.NONE` across all routes -> `Router.not_found`, never `422`) |
| `GET /api/v1/auth/user/looker/_handle` or `DELETE /api/v1/auth/user/looker/_handle` | None or any | `404 Not Found` | Standard JSON headers | `{"detail": "Not Found"}` | Starlette `0.41.3` `Router.not_found` (no `Match.PARTIAL` route exists, so never `405`) |
| `GET /api/v1/auth/users/looker` | None or `Authorization: Bearer <any>` | `404 Not Found` | Standard JSON headers | `{"detail": "Not Found"}` | Starlette `0.41.3` `Router.not_found`; publishes **zero** messages to `ports.MessagePublisher` |
| `POST /api/v1/auth/users/looker` | None or any | `404 Not Found` | Standard JSON headers | `{"detail": "Not Found"}` | Starlette `0.41.3` `Router.not_found` |

### OpenAPI Schema Contract (`GET /openapi.json`)

| OpenAPI Location | Removed / Absent Entries | Retained Entries (Must Remain Present) |
|---|---|---|
| `paths` | `/api/v1/auth/user/looker/_handle`, `/api/v1/auth/users/looker` | `/api/v1/auth/token`, `/api/v1/auth/refresh`, `/api/v1/auth/dashboard`, `/api/v1/auth/forgot`, `/api/v1/auth/reset` |
| `components.schemas` | `PubsubDeleteUserData`, `DeleteLookerUserMessage`, `PubsubRequest`, `PubsubMessage` *(remaining `processor` & `knowledge_base` `PubsubRequest` routes set `include_in_schema=False`)* | `FirebaseLogin`, `EmailPasswordLogin`, `Session`, `ForgotPassword`, `ResetPassword` |

### Retained `GET /api/v1/auth/dashboard` Error & Success Responses (Regression Contract)

| Scenario | Status | Response Body | Handler / Source |
|---|---|---|---|
| Missing `Authorization` header (or bare `Bearer` with no credentials) | `403 Forbidden` | `{"detail": "Not authenticated"}` | `fastapi.security.HTTPBearer` (`helpers/auth.py:52`, `fastapi/security/http.py:308-310`) |
| Non-`Bearer` `Authorization` scheme (e.g., `Basic ...`) | `403 Forbidden` | `{"detail": "Invalid authentication credentials"}` | `fastapi.security.HTTPBearer` (`helpers/auth.py:52`, `fastapi/security/http.py:316-318`) |
| Malformed, expired, wrong-audience, or bad-signature Bearer JWT | `401 Unauthorized` | `{"status_code": 401, "message": "The token is expired and/or invalid.", "code": "token_expired_or_invalid"}` | `errors.TokenExpired` (`helpers/auth.py:124` -> `middleware.error_handler`) |
| Valid RS512 JWT whose `session_id` (`sub.split(":")[0]`) is absent from `sessions` table | `401 Unauthorized` | `{"detail": "You don't have enough permission to do it."}` *(real `auth.get_token` at `auth.py:131-132`)* or `{"status_code": 401, "message": "The token is expired and/or invalid.", "code": "token_expired_or_invalid"}` *(if `auth.get_token` is overridden, via `SessionManager.get_current_session` at `session_manager.py:39-40`)* | `helpers/auth.py:110-132` / `helpers/session_manager.py:39-40` |
| Valid RS512 JWT backed by active `models.Session` row (`?src=/embed/dashboards/1`) | `200 OK` | `{"url": "https://<looker_host>/login/embed/%2Fembed%2Fdashboards%2F1?nonce=...&time=...&session_length=3000&external_user_id=...&permissions=...&models=%5B%5D&group_ids=%5B2%5D&external_group_id=null&user_attributes=...&access_filters=%7B%7D&signature=...&first_name=...&last_name=...&force_logout_login=true"}` | `routers/auth/endpoints.py:96-111` -> `LookerDashboard.get_signed_url` (`looker.py:73-171`) |

---

## 6. What Must Not Change (System Invariants)

1. **Database Schema & Alembic Migrations:** Zero new or modified files under `src/Backend/migrations/versions/`; ORM models (`models/users.py`, `models/sessions.py`, etc.) remain untouched.
2. **All 5 Retained Authentication Endpoints (`src/Backend/src/api/routers/auth/endpoints.py`):**
   - `POST /api/v1/auth/token` (`L28`), `POST /api/v1/auth/refresh` (`L60`), `GET /api/v1/auth/dashboard` (`L96`), `POST /api/v1/auth/forgot` (`L114`), and `POST /api/v1/auth/reset` (`L141`) retain their exact paths, HTTP methods, `fastapi.Security` dependencies, request/response payloads, and behavior.
3. **Looker Signed SSO URL-Signing Algorithm & Payload (`src/Backend/src/api/adapters/google/looker.py:25-171`):**
   - `User` helper class (`L25-59`), `LookerDashboard._sign` (`L116-140`, 12-line `string_to_sign` + `hmac.new(..., sha1)` + `base64.b64encode`), `LookerDashboard._to_string` (`L142-171`, query parameter order and `urllib.parse.quote_plus` encoding), and `LookerDashboard.get_signed_url` permissions, `group_ids=[2]`, `session_length=3000`, and `user_attributes` keys (`group_ids`, `organization_ids`, `state`, `region`, `county`) must remain functionally identical (aside from `getattr(user, "county", None)` fixing the dropped column crash at `L109`).
4. **Shared Scheduler Auth & Pub/Sub Request Schemas:**
   - `auth.validate_scheduler_token` (`src/Backend/src/api/helpers/auth.py:82-98`, actively used by `GET /api/v1/processor/sync` at `routers/processor/endpoints.py:514`) must not be modified or deleted.
   - `PubsubMessage` and `PubsubRequest` (`src/Backend/src/api/routers/schemas.py:8-24`, re-exported in `routers/__init__.py:13,34-35` and used by `processor` and `knowledge_base` routers) and `MessagePublisher` (`adapters/google/pubsub.py`) must not be modified.
5. **Production DI Modules (`src/Backend/src/api/dependencies.py`):** `GoogleModule.provide_looker` (`L674-681`), `InternetlessModule.provide_looker` (`L795-802`), and `get_session_manager` (`L886-895`) remain untouched.
6. **Terraform Infrastructure (`src/IAC/`):** `src/IAC/10-Secrets.tf` (`lookersdk_base_url`, `lookersdk_client_id`, `lookersdk_client_secret`, `looker_secret`), `src/IAC/02-sa_and_iam.tf`, and `src/IAC/06-message_service.tf` remain completely untouched.
7. **Frontend Looker Embed Integration (`src/Frontend/`):** Zero edits in `src/Frontend/` (`src/Frontend/package.json`, `src/Frontend/src/constants/endpoints.ts`, `src/Frontend/src/libs/looker/looker.ts`, `src/Frontend/src/components/looker/Looker.tsx`).
8. **Unrelated Locked Python Packages:** All locked versions in `src/Backend/poetry.lock` other than `looker-sdk` (`24.20.0`) and `cattrs` (`24.1.2`) must remain at their exact currently locked versions.

---

## 7. Code Style & Reference Patterns

### Backend: Port & Stdlib-Only `LookerDashboard` Adapter

Keep strict type annotations (`mypy --strict`) and preserve docstrings/comments on retained classes and methods:

```python
# src/Backend/src/api/ports/dashboard.py
"""
Module related to all dashboard stuff.
"""

import abc

from starlette import datastructures

from api import models


class Dashboard(abc.ABC):
    """
    The port for the dashboard functions.
    """

    @abc.abstractmethod
    async def get_signed_url(
        self,
        user: models.User,
        query: datastructures.QueryParams,
    ) -> str:
        """
        Generates signed url to access the dashboard.
        """
```

```python
# src/Backend/src/api/adapters/google/looker.py (constructor & county attribute excerpt)
class LookerDashboard(ports.Dashboard):
    """
    The adapter for dashboard.
    """

    user: User

    def __init__(self, looker_host: str, looker_secret: str):
        self.looker_host = looker_host
        self.looker_secret = looker_secret
```

```python
                "state": user.state,
                "region": user.region,
                "county": getattr(user, "county", None),
```

### Backend: `TestGoogleModule` Provider & `@pytest.mark.asyncio` Regression Pattern

In `src/Backend/tests/conftest.py`, place `from api.adapters.google import looker  # noqa: E402` contiguously at `L21` (immediately after `from api.adapters import memory  # noqa: E402` at `L20` inside the existing `L19-24` import block) so zero new `ruff` (`E402` / `I001`) or `mypy` diagnostics are introduced. Never co-request `client` and `unauthenticated_client` in the same test function:

```python
# src/Backend/tests/conftest.py (excerpt inside L19-24 import block)
from api.adapters import memory  # noqa: E402
from api.adapters.google import looker  # noqa: E402
```

```python
    @injector.provider
    @injector.singleton
    def provide_looker(self) -> ports.Dashboard:
        return looker.LookerDashboard(
            looker_host="looker.example.com",
            looker_secret="test-looker-secret",
        )
```

```python
# src/Backend/tests/integration/test_looker_user_delete_removed.py (excerpt)
@pytest.mark.asyncio
async def test_looker_delete_handle_endpoint_removed(
    unauthenticated_client: AsyncClient,
) -> None:
    encoded = base64.b64encode(b'{"user_id": "1"}').decode("utf-8")
    response = await unauthenticated_client.post(
        "/api/v1/auth/user/looker/_handle",
        json={
            "message": {"data": encoded, "messageId": "1"},
            "subscription": "projects/test/subscriptions/sub",
        },
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
```

---

## 8. Commands

Run all commands from `/Users/fabriciols/Repos/aira/src/Backend` (there is no root task runner):

```bash
cd /Users/fabriciols/Repos/aira/src/Backend

# 1. Remove looker-sdk from pyproject.toml & prune looker-sdk + cattrs from poetry.lock (Poetry 2.x)
poetry remove looker-sdk
poetry check --lock

# 2. Lint & strict typecheck touched files (must report 0 errors on all 5 files below)
poetry run ruff check \
  src/api/routers/auth/endpoints.py \
  src/api/routers/auth/schemas.py \
  src/api/ports/dashboard.py \
  src/api/adapters/google/looker.py \
  tests/integration/test_looker_user_delete_removed.py

MYPYPATH=src poetry run mypy --config-file=mypy.ini --follow-imports=silent \
  src/api/routers/auth/endpoints.py \
  src/api/routers/auth/schemas.py \
  src/api/ports/dashboard.py \
  src/api/adapters/google/looker.py \
  tests/integration/test_looker_user_delete_removed.py

# 3. Verify zero new diagnostics in tests/conftest.py (baseline: 15 ruff / 14 mypy pre-existing errors)
poetry run ruff check tests/conftest.py
MYPYPATH=src poetry run mypy --config-file=mypy.ini --follow-imports=silent tests/conftest.py

# 4. Run targeted integration suite & full Backend test suite
poetry run pytest tests/integration/test_looker_user_delete_removed.py -vvv
make test

# 5. Static verification (relative to src/Backend, no stderr suppression) confirming zero remaining references
! rg "looker_sdk|looker-sdk|LOOKERSDK_|delete_looker_user|get_all_looker_users|DeleteLookerUserMessage|PubsubDeleteUserData|pubsub_delete_user_topic|delete-looker-user-queue|/user/looker/_handle|/users/looker" \
  src tests/conftest.py docker-compose.yaml pyproject.toml poetry.lock cloudbuild.yaml env.example
```

---

## 9. Testing Strategy

Because `db_engine` (`src/Backend/tests/conftest.py:197-211`) is **session-scoped** without per-test transaction rollback and `Base.metadata.create_all` seeds zero `Role` rows, tests must generate unique UUID-suffixed role names and email addresses (`uuid.uuid4()`) and never co-request `client` and `unauthenticated_client` in the same test function.

Create `src/Backend/tests/integration/test_looker_user_delete_removed.py` covering:

1. **`test_looker_delete_handle_endpoint_removed(unauthenticated_client)`:**
   - Unauthenticated `POST /api/v1/auth/user/looker/_handle` with a schema-valid `PubsubRequest` (`{"message": {"data": base64('{"user_id": "1"}'), "messageId": "1"}, "subscription": "projects/test/subscriptions/sub"}`) and with minimal JSON (`{"message": {"data": base64('{"user_id": "1"}')}}`) both return `404` (`{"detail": "Not Found"}`, never `200` or `422`).
   - `GET /api/v1/auth/user/looker/_handle` and `DELETE /api/v1/auth/user/looker/_handle` also return `404` (`{"detail": "Not Found"}`).
2. **`test_looker_list_users_scheduler_endpoint_removed(unauthenticated_client, mock_publisher)`:**
   - Unauthenticated `GET /api/v1/auth/users/looker` and `GET /api/v1/auth/users/looker` with `Authorization: Bearer fake-scheduler-oidc-token` both return `404` (`{"detail": "Not Found"}`), and `mock_publisher.published` remains empty (`[]`).
3. **`test_openapi_excludes_removed_looker_routes_and_schemas(unauthenticated_client)`:**
   - `GET /openapi.json` returns `200`; `paths` excludes `/api/v1/auth/user/looker/_handle` and `/api/v1/auth/users/looker` while retaining `/api/v1/auth/token`, `/api/v1/auth/refresh`, `/api/v1/auth/dashboard`, `/api/v1/auth/forgot`, and `/api/v1/auth/reset`; `components.schemas` excludes `PubsubDeleteUserData`, `DeleteLookerUserMessage`, `PubsubRequest`, and `PubsubMessage` (since remaining `processor` and `knowledge_base` `PubsubRequest` routes use `include_in_schema=False`) while retaining `FirebaseLogin`, `EmailPasswordLogin`, `Session`, `ForgotPassword`, and `ResetPassword`.
4. **`test_dashboard_endpoint_rejects_unauthenticated_and_forged_tokens(unauthenticated_client)`:**
   - `GET /api/v1/auth/dashboard?src=/embed/dashboards/1` with no `Authorization` header returns `403` (`{"detail": "Not authenticated"}`), and with `Authorization: Bearer invalid.jwt.token` returns `401` (`response.json()["code"] == "token_expired_or_invalid"`).
5. **`test_dashboard_endpoint_returns_valid_hmac_signed_url_for_authenticated_session(unauthenticated_client, session_factory, monkeypatch)`:**
   - Clear `LOOKERSDK_BASE_URL`, `LOOKERSDK_CLIENT_ID`, and `LOOKERSDK_CLIENT_SECRET` via `monkeypatch.delenv(..., raising=False)`.
   - Seed an isolated `models.Role` (`scopes=["dashboard.viewer"]`) and password `models.User` (`external_id=None`, `customer_id=None`, `type=models.UserType.PASSWORD`, `role_id=role.id`, `name="Maria Silva"`, `email_address=email`, `state="SP"`, `region="Sul"`, calling `user.set_password("Password123!", context.CryptContext(schemes=["bcrypt"], deprecated="auto"))`) via `session_factory`.
   - Authenticate via `POST /api/v1/auth/token` (`{"email_address": email, "password": "Password123!"}`) on `unauthenticated_client` (`200 OK`) to create a real `models.Session` row and RS512 `access_token`.
   - Call `GET /api/v1/auth/dashboard?src=/embed/dashboards/1` with `Authorization: Bearer <access_token>` (`200 OK`).
   - Parse the returned `url` via `parsed = urllib.parse.urlsplit(url)` and `pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)` (`assert len(pairs) == len(dict(pairs))` and `params = dict(pairs)`): assert scheme `https`, netloc `looker.example.com`, path `/login/embed/%2Fembed%2Fdashboards%2F1`, `params["session_length"] == "3000"`, `params["external_user_id"] == f'"{user.id}"'`, `params["first_name"] == '"Maria"'`, `params["last_name"] == '"Silva"'`, `params["force_logout_login"] == "true"`, `json.loads(params["user_attributes"]) == {"group_ids": "[]", "organization_ids": "[]", "state": "SP", "region": "Sul", "county": None}`, and recompute the expected `HMAC-SHA1` (`secret="test-looker-secret"`) over the 12-line `string_to_sign` to assert `params["signature"]` matches byte-for-byte.
6. **`test_dead_looker_delete_symbols_and_sdk_removed()`:**
   - Assert `DeleteLookerUserMessage` and `PubsubDeleteUserData` are absent from `api.routers.auth.schemas`, while shared `PubsubRequest` and `PubsubMessage` remain present in `api.routers.schemas`.
   - Assert `delete_looker_user` and `get_all_looker_users` are absent from `ports.Dashboard` and `LookerDashboard`.
   - Instantiate `dashboard = LookerDashboard(looker_host="looker.example.com", looker_secret="secret")` directly without `LOOKERSDK_*` env vars and assert `not hasattr(dashboard, "_looker")`.
   - Assert `importlib.util.find_spec("looker_sdk") is None`.

---

## 10. Boundaries

- **Always:**
  - Restrict edits strictly to the files listed in Section 3.
  - Use Poetry 2.x `poetry remove looker-sdk` so unrelated locked package versions in `poetry.lock` do not drift.
  - Keep `unauthenticated_client` and `client` in separate test functions, decorate async tests with `@pytest.mark.asyncio`, and maintain `0` `ruff` and `0` `mypy --strict` errors across all touched `src/api/` files and the new integration test file (plus zero new diagnostics in `tests/conftest.py`).
  - Preserve shared `auth.validate_scheduler_token` (`helpers/auth.py:82-98`) and `PubsubRequest` / `PubsubMessage` (`routers/schemas.py:8-24`).
- **Ask first:**
  - Modifying `src/IAC/10-Secrets.tf` or any other Terraform file under `src/IAC/`.
  - Changing RBAC scopes, query parameter handling, or the 12-line HMAC-SHA1 signing format on `GET /api/v1/auth/dashboard` / `LookerDashboard`.
  - Modifying any file in `src/Frontend/`, `src/Agent/`, or `src/Backend/Dockerfile`.
  - Fixing pre-existing lint/type errors in untouched Backend files.
- **Never:**
  - Read, log, or commit `.env` files, `src/Backend/aira-sa-local-access-key.json`, `src/IAC/terraform.tfstate*`, `src/IAC/{terraform.tfvars,backend.tf,variables.tf}`, `src/Agent/deploy/deploy.py`, or `local_pubsub_forwarder.py`.
  - Point `_DATABASE_TEST_URI` at a shared or non-disposable database (`tests/conftest.py` executes `Base.metadata.drop_all`).
  - Use Pydantic v2 APIs (`model_dump`, `model_validate`, `ConfigDict`, `@field_validator`) in `src/Backend/`.

---

## 11. Success Criteria

- [ ] `set_delete_users_pubsub` (`auth/endpoints.py:158-179`), `handle_delete_users_pubsub` (`auth/endpoints.py:182-194`), `DeleteLookerUserMessage` (`auth/schemas.py:64-70`), `PubsubDeleteUserData` (`auth/schemas.py:73-78`), `Dashboard.delete_looker_user` / `get_all_looker_users` (`ports/dashboard.py:28-38`), `LookerDashboard._looker` / `delete_looker_user` / `get_all_looker_users` (`adapters/google/looker.py:15-16,71,173-184`), and all orphaned imports are removed.
- [ ] `looker.py:109` uses `getattr(user, "county", None)` and `LookerDashboard` initializes cleanly with zero `looker_sdk` or `LOOKERSDK_*` dependencies.
- [ ] `looker-sdk` (`24.20.0`) and `cattrs` (`24.1.2`) are removed from `src/Backend/pyproject.toml` and `src/Backend/poetry.lock`, and `poetry check --lock` passes.
- [ ] `src/Backend/docker-compose.yaml` drops `_PUBSUB_DELETE_USER_TOPIC`, `LOOKERSDK_BASE_URL`, `LOOKERSDK_CLIENT_ID`, `LOOKERSDK_CLIENT_SECRET`, and the `delete-looker-user-queue` emulator block; `src/Backend/cloudbuild.yaml` drops `LOOKERSDK_*` from `--update-secrets` and passes `--remove-secrets=LOOKERSDK_BASE_URL,LOOKERSDK_CLIENT_ID,LOOKERSDK_CLIENT_SECRET`; `src/IAC/10-Secrets.tf` is untouched.
- [ ] Unauthenticated requests to `POST /api/v1/auth/user/looker/_handle` and `GET /api/v1/auth/users/looker` return `404 Not Found` (`{"detail": "Not Found"}`), publish zero Pub/Sub messages, and are absent from `/openapi.json` (along with `PubsubRequest` / `PubsubMessage` in `components.schemas`, while `api.routers.schemas.{PubsubRequest,PubsubMessage}` remain intact at runtime).
- [ ] `GET /api/v1/auth/dashboard` rejects unauthenticated/forged callers (`403`/`401`) and returns a verified HMAC-SHA1 signed `/login/embed/...` URL (`200`) for a real authenticated session without `looker-sdk`.
- [ ] Targeted `ruff check` and `mypy --config-file=mypy.ini --follow-imports=silent` report **0 errors** across `auth/endpoints.py`, `auth/schemas.py`, `ports/dashboard.py`, `adapters/google/looker.py`, and `tests/integration/test_looker_user_delete_removed.py`, **zero new** diagnostics in `tests/conftest.py`, and `make test` passes.

---

## 12. Resolved Questions

1. **Greenfield vs. Existing Cloud Run Service for `--remove-secrets` (`src/Backend/cloudbuild.yaml:50`):** *Resolved.* `cloudbuild.yaml` is used both to update existing services and to bootstrap new environments; verified in Google Cloud SDK source (`config_changes.py:776-787` and `v2/config_changes.py:819-835`) that `--remove-secrets=LOOKERSDK_BASE_URL,LOOKERSDK_CLIENT_ID,LOOKERSDK_CLIENT_SECRET` is a silent no-op on brand-new services while detaching `LOOKERSDK_*` before `--update-secrets` on existing services.
2. **`TestGoogleModule.provide_looker` Test Fixture Binding (`src/Backend/tests/conftest.py`):** *Resolved.* Confirmed binding minimal config `looker.LookerDashboard(looker_host="looker.example.com", looker_secret="test-looker-secret")` in `TestGoogleModule`.
