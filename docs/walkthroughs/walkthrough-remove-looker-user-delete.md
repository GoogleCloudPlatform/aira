# Remove Unauthenticated Looker User Deletion — Implementation Walkthrough

This walkthrough documents the incremental, Test-Driven Development (TDD) implementation of [`docs/specs/spec-remove-looker-user-delete.md`](../specs/spec-remove-looker-user-delete.md) on branch `fix/remove-looker-user-delete`.

---

## 1. Security Summary & Motivation

AIRA embeds Looker dashboards solely through stateless HMAC-SHA1 SSO URL signing (`GET /api/v1/auth/dashboard`) using `_LOOKER_HOST` and `_LOOKER_SECRET`. Two legacy routes on the `auth` router remained exposed even though no GCP Pub/Sub topic, push subscription, or Cloud Scheduler job existed in `src/IAC/`:

1. **`POST /api/v1/auth/user/looker/_handle`** (CWE-306 / CWE-284): Had zero `fastapi.Security(...)` or OIDC push-token validation. Any unauthenticated caller on `--allow-unauthenticated` Cloud Run could base64-encode `{"user_id": "<id>"}` inside a `PubsubRequest` envelope and invoke `LookerDashboard.delete_looker_user(user_id)` -> `looker_sdk.delete_user(user_id)` using admin `LOOKERSDK_CLIENT_ID` / `LOOKERSDK_CLIENT_SECRET` credentials, permanently deleting arbitrary Looker users (including non-embed administrators).
2. **`GET /api/v1/auth/users/looker`**: Listed embed Looker users via `looker_sdk.search_users(embed_user=True)` and published `DeleteLookerUserMessage` payloads to an unprovisioned `pubsub_delete_user_topic`.

In addition, `LookerDashboard.get_signed_url` referenced `user.county`, which had been removed from `models.User` in migration `80dc3596cd72`.

Both endpoints—along with their orphaned auth schemas, `Dashboard` port methods, `LookerDashboard` SDK client/methods, `looker-sdk` dependency (`+ cattrs`), local Compose queue/env vars, and Cloud Run `LOOKERSDK_*` secret mounts—have been permanently removed without introducing a runtime feature flag, while fixing `getattr(user, "county", None)` and preserving `GET /api/v1/auth/dashboard`.

---

## 2. Incremental TDD Slices (`fix/remove-looker-user-delete`)

Each slice was verified with tests, `ruff`, and `mypy --strict` before committing:

### Slice 1 — Characterization Tests & Test Harness (`6eca42e`)
- **Files:** `src/Backend/tests/conftest.py`, `src/Backend/tests/integration/test_looker_user_delete_removed.py`
- **Changes:**
  - Bound `ports.Dashboard` -> `looker.LookerDashboard(looker_host="looker.example.com", looker_secret="test-looker-secret")` on `TestGoogleModule` in `tests/conftest.py`.
  - Added 5 characterization tests pinning pre-removal behavior of `POST /api/v1/auth/user/looker/_handle` (`200` invoking `delete_looker_user("1")`, `422` on minimal envelope), `GET /api/v1/auth/users/looker` (`403` missing header, `200` publishing `DeleteLookerUserMessage` to `mock_publisher`), `/openapi.json` path/schema exposure, and `GET /api/v1/auth/dashboard` (`403`, `401`, and `200` verified HMAC-SHA1 signed URL).

### Slice 2 — Remove `/user/looker/_handle` & `/users/looker` Routes and Orphaned Auth Schemas (`72f545a`)
- **Files:** `src/Backend/src/api/routers/auth/endpoints.py`, `src/Backend/src/api/routers/auth/schemas.py`, `src/Backend/tests/integration/test_looker_user_delete_removed.py`
- **TDD Cycle:**
  - **Red:** Updated Tests 1–3 to assert `404 Not Found` across `POST` (schema-valid and minimal JSON), `GET`, and `DELETE` on `/api/v1/auth/user/looker/_handle`, `404 Not Found` and empty `mock_publisher.published` on `GET /api/v1/auth/users/looker`, OpenAPI path/schema pruning (including `PubsubRequest` / `PubsubMessage` in `/openapi.json` since remaining Pub/Sub routes use `include_in_schema=False`), and absence of `DeleteLookerUserMessage` / `PubsubDeleteUserData`; confirmed `3 failed, 2 passed`.
  - **Green:** Removed `set_delete_users_pubsub`, `handle_delete_users_pubsub`, `import base64`, and `from api.routers.schemas import PubsubRequest` from `auth/endpoints.py`, plus `DeleteLookerUserMessage`, `PubsubDeleteUserData`, `import dataclasses`, and `from api import typings` from `auth/schemas.py`. Confirmed `5 passed`.

### Slice 3 — Remove `looker-sdk` Client/Dependency, Port Methods, & Stale `user.county` Access (`8e279d4`)
- **Files:** `src/Backend/src/api/ports/dashboard.py`, `src/Backend/src/api/adapters/google/looker.py`, `src/Backend/pyproject.toml`, `src/Backend/poetry.lock`, `src/Backend/tests/integration/test_looker_user_delete_removed.py`
- **TDD Cycle:**
  - **Red:** Removed characterization workarounds (`LOOKERSDK_BASE_URL` env var and `models.User.county` monkeypatch) from `test_dashboard_returns_valid_hmac_signed_url_for_authenticated_session` and added `test_dead_looker_delete_symbols_and_sdk_removed`; confirmed `2 failed, 4 passed`.
  - **Green:** Removed `delete_looker_user`, `get_all_looker_users`, and unused `typing` from `ports/dashboard.py`; removed `looker_sdk` imports, `self._looker = looker_sdk.init40()`, `delete_looker_user`, and `get_all_looker_users` from `adapters/google/looker.py`; replaced `"county": user.county` with `"county": getattr(user, "county", None)`; and ran `poetry remove looker-sdk` (pruning `looker-sdk 24.20.0` and `cattrs 24.1.2` with zero unrelated lockfile drift). Confirmed `6 passed`.

### Slice 4 — Unmount `LOOKERSDK_*` Secrets & Remove Dead Compose Queue (`af2519c`)
- **Files:** `src/Backend/docker-compose.yaml`, `src/Backend/cloudbuild.yaml`
- **Changes:**
  - Removed `_PUBSUB_DELETE_USER_TOPIC`, `LOOKERSDK_BASE_URL`, `LOOKERSDK_CLIENT_ID`, `LOOKERSDK_CLIENT_SECRET`, and the `delete-looker-user-queue` `PUBSUB_CONFIG` block from `docker-compose.yaml`.
  - Removed `LOOKERSDK_*` mappings from `--update-secrets` and added `--remove-secrets=LOOKERSDK_BASE_URL,LOOKERSDK_CLIENT_ID,LOOKERSDK_CLIENT_SECRET` in `cloudbuild.yaml` (detaching existing Cloud Run secret bindings while remaining a no-op on new-environment deployments).
  - Left `src/IAC/10-Secrets.tf`, `helpers/auth.py` (`validate_scheduler_token`), and `routers/schemas.py` (`PubsubRequest`, `PubsubMessage`) untouched per spec boundaries.

---

## 3. Post-Removal HTTP & OpenAPI Contract

| Request | Auth Header | Status | Body |
|---|---|---|---|
| `POST /api/v1/auth/user/looker/_handle` (valid `PubsubRequest` or minimal JSON) | None or any | `404 Not Found` | `{"detail": "Not Found"}` |
| `GET /api/v1/auth/user/looker/_handle` / `DELETE /api/v1/auth/user/looker/_handle` | None or any | `404 Not Found` | `{"detail": "Not Found"}` |
| `GET /api/v1/auth/users/looker` | None or any Bearer token | `404 Not Found` | `{"detail": "Not Found"}` |
| `GET /api/v1/auth/dashboard?src=/embed/dashboards/1` | Missing | `403 Forbidden` | `{"detail": "Not authenticated"}` |
| `GET /api/v1/auth/dashboard?src=/embed/dashboards/1` | Forged Bearer JWT | `401 Unauthorized` | `{"status_code": 401, ..., "code": "token_expired_or_invalid"}` |
| `GET /api/v1/auth/dashboard?src=/embed/dashboards/1` | Valid session Bearer JWT | `200 OK` | `{"url": "https://looker.example.com/login/embed/..."}` (verified 12-line HMAC-SHA1 signature, `"county": null`) |

---

## 4. Verification Results

- `poetry check --lock`: **Passed** (`exit 0`).
- `poetry run ruff check src/api/routers/auth/endpoints.py src/api/routers/auth/schemas.py src/api/ports/dashboard.py src/api/adapters/google/looker.py tests/integration/test_looker_user_delete_removed.py`: **All checks passed!** (`0` errors).
- `MYPYPATH=src poetry run mypy --config-file=mypy.ini --follow-imports=silent src/api/routers/auth/endpoints.py src/api/routers/auth/schemas.py src/api/ports/dashboard.py src/api/adapters/google/looker.py tests/integration/test_looker_user_delete_removed.py`: **Success: no issues found in 5 source files**.
- `tests/conftest.py` diagnostics check: **Zero new diagnostics** (unchanged baseline of `15` ruff / `14` mypy pre-existing errors).
- `poetry run pytest tests/integration/test_looker_user_delete_removed.py -vvv`: **6 passed**.
- `make test`: **21 passed** across the full Backend test suite (`ports/dashboard.py` and `routers/auth/schemas.py` at `100%` coverage).
- YAML/JSON config validation (`docker-compose.yaml` + `PUBSUB_CONFIG` JSON + `cloudbuild.yaml`): **Passed**.
- `git grep` symbol scan across `src/`, `tests/conftest.py`, `docker-compose.yaml`, `pyproject.toml`, `poetry.lock`, `cloudbuild.yaml`, and `env.example`: **0 residual references** (only the intentional `--remove-secrets=LOOKERSDK_BASE_URL,LOOKERSDK_CLIENT_ID,LOOKERSDK_CLIENT_SECRET` flag in `cloudbuild.yaml:50`).
