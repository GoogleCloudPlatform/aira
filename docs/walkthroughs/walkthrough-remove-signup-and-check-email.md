# Remove Unauthenticated Self-Signup & Email Enumeration — Implementation Walkthrough

This walkthrough documents the incremental, Test-Driven Development (TDD) implementation of [`docs/specs/spec-remove-signup-and-check-email.md`](../specs/spec-remove-signup-and-check-email.md) on branch `fix/remove-signup-and-check-email`.

---

## 1. Security Summary & Motivation

AIRA operates under an administrator-provisioned identity model (`POST /api/v1/users` restricted to `scopes=["admin"]` and `PUT /api/v1/users/batch` restricted to `scopes=["sync"]`). Two legacy unauthenticated routes remained active on the `users` router even though no Frontend UI referenced them:

1. **`POST /api/v1/users/signup`** (CWE-306 / CWE-284): Allowed any unauthenticated caller to mint an active `"user"`-role account in `"Escola Senai"` / `"Senai 3EM"` and subsequently exchange those credentials at `POST /api/v1/auth/token` for a valid session JWT.
2. **`GET /api/v1/users/check_email/{user_email}`** (CWE-204 / CWE-200): Acted as an unauthenticated email-enumeration oracle, returning `409 Conflict` (`user_already_exists`) for registered emails and `200 OK` for unknown emails across all roles (students, professors, managers, and administrators).

Both endpoints—along with their orphaned Backend schema, exception classes, email helper, and unused Frontend endpoint/i18n definitions—have been permanently removed without introducing a runtime feature flag.

---

## 2. Incremental TDD Slices (`fix/remove-signup-and-check-email`)

Each slice was verified with tests, `ruff`, and `mypy --strict` before committing:

### Slice 1 — Characterization Tests & Test Harness (`5937243`)
- **Files:** `src/Backend/tests/conftest.py`, `src/Backend/tests/integration/test_users_signup_removed.py`
- **Changes:**
  - Added module-level singleton `_TEST_SECRET_MANAGER` (`memory.SecretManager()`) and `_TEST_EXTERNAL_AUTH` (`memory.ExternalAuth()`), plus `TestAuthAndHashingModule` providing `ports.SecretManager`, `ports.ExternalAuth`, and `passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")` inside `test_app`.
  - Added `unauthenticated_client` (`ASGITransport(app=test_app)`) clearing `dependency_overrides` for isolated unauthenticated request testing without sharing `test_app` with `client`.
  - Added 5 characterization tests pinning pre-removal behavior of `POST /api/v1/users/signup` (`200`, `409 user_already_exists`, `400 invalid_email`), `GET /api/v1/users/check_email/{email}` (`200` vs `409`), `/openapi.json` schema exposure, and retained `POST /api/v1/users` RBAC/validation (`403`, `401`, `200`, `422`, `409 already_exists`).

### Slice 2 — Remove `/signup` and `/check_email/{user_email}` Routes (`35bb432`)
- **Files:** `src/Backend/src/api/routers/users/endpoints.py`, `src/Backend/tests/integration/test_users_signup_removed.py`
- **TDD Cycle:**
  - **Red:** Replaced the 3 legacy characterization assertions with post-removal assertions (`test_signup_endpoint_removed`, `test_check_email_endpoint_removed_no_enumeration`, `test_openapi_excludes_removed_signup_routes_and_schema`) and confirmed `3 failed, 2 passed`.
  - **Green:** Deleted `@router.post("/signup")`, `@router.get("/check_email/{user_email}")` (`delete`), and the orphaned `util` import from `src/Backend/src/api/routers/users/endpoints.py`. Confirmed `5 passed`.

### Slice 3 — Remove Orphaned Backend Schema, Exceptions, & Email Helper (`795e8ea`)
- **Files:** `src/Backend/src/api/routers/users/schemas.py`, `src/Backend/src/api/errors.py`, `src/Backend/src/api/helpers/util.py`, `src/Backend/tests/integration/test_users_signup_removed.py`
- **TDD Cycle:**
  - **Red:** Added `test_dead_signup_symbols_removed_from_backend` asserting absence of `SignupUserCreate`, `UserAlreadyExists`, `InvalidEmail`, and `util.validate_email`; confirmed `1 failed`.
  - **Green:** Removed `SignupUserCreate` and unused `errors`/`util` imports from `users/schemas.py`, `UserAlreadyExists` and `InvalidEmail` from `errors.py`, and `validate_email` from `helpers/util.py`. Confirmed `6 passed` and `make test` (`15 passed`).

### Slice 4 — Remove Dead Frontend Constants & Signup i18n Keys (`8eb71b5`)
- **Files:**
  - `src/Frontend/src/constants/endpoints.ts`
  - `src/Frontend/src/libs/i18n/languages/{en-US,pt-BR,es-ES}/form.json`
  - `src/Frontend/src/libs/i18n/languages/{en-US,pt-BR,es-ES}/toast.json`
- **Changes:**
  - Removed `ENDPOINT_SIGNUP` and `ENDPOINT_CHECK_EMAIL` from `endpoints.ts`.
  - Removed `form.signin.create_account` (stripping trailing comma on `button_reset_password`) and the `form.signup` object across `en-US`, `pt-BR`, and `es-ES`.
  - Removed `toast.success.auth.success_signup` (stripping trailing comma on `success_reset_password`) and `toast.errors.auth.signup_user_error` across `en-US`, `pt-BR`, and `es-ES`, while keeping `toast.errors.auth.email_already_registered` intact per Spec Assumption 3.

---

## 3. Post-Removal HTTP Contract

| Request | Auth Header | Status & Headers | Body |
|---|---|---|---|
| `POST /api/v1/users/signup` | None or any | `405 Method Not Allowed` (`Allow: GET`) | `{"detail": "Method Not Allowed"}` |
| `GET /api/v1/users/check_email/{email}` (existing or unknown valid non-slash email) | None or any | `404 Not Found` | `{"detail": "Not Found"}` |
| `GET /api/v1/users/check_email/exams` | None | `403 Forbidden` | `{"detail": "Not authenticated"}` |
| `POST /api/v1/users` | Missing | `403 Forbidden` | `{"detail": "Not authenticated"}` |
| `POST /api/v1/users` | Forged Bearer JWT | `401 Unauthorized` | `{"status_code": 401, ..., "code": "token_expired_or_invalid"}` |
| `POST /api/v1/users` | Valid `"admin"` JWT | `200` / `422` / `409` | Unchanged `UserGet` / `value_error.email` / `already_exists` |

---

## 4. Verification Results

### Backend (`src/Backend`)
- `poetry check --lock`: **Passed** (`exit 0`).
- `poetry run ruff check src/api/errors.py src/api/helpers/util.py src/api/routers/users/schemas.py tests/integration/test_users_signup_removed.py`: **All checks passed!** (`0` errors).
- `poetry run ruff check src/api/routers/users/endpoints.py tests/conftest.py`: **Zero new diagnostics** (only pre-existing `PLR0912` on `endpoints.py:718` and 15 pre-existing diagnostics on `tests/conftest.py`, down from 16).
- `poetry run mypy --config-file=mypy.ini --follow-imports=silent src/api/errors.py src/api/helpers/util.py src/api/routers/users/endpoints.py src/api/routers/users/schemas.py tests/integration/test_users_signup_removed.py`: **Success: no issues found in 5 source files**.
- `poetry run pytest tests/integration/test_users_signup_removed.py -vvv`: **6 passed**.
- `make test`: **15 passed** across the full Backend test suite.
- Static symbol scan across `src/Backend/src` (`SignupUserCreate|UserAlreadyExists|InvalidEmail|validate_email|check_email|/signup`): **0 matches**.

### Frontend (`src/Frontend`)
- Static symbol/key scan across `src/Frontend/src` (`ENDPOINT_SIGNUP|ENDPOINT_CHECK_EMAIL|success_signup|signup_user_error|create_account|['"\.]signup['"\.]`): **0 matches**.
- JSON syntax & locale leaf-key parity check (`en-US`, `pt-BR`, `es-ES`): **Passed** (`form.json`: 352 leaf keys with 100% parity; `toast.json`: 134 leaf keys with 100% parity).
- Run the Next.js lint/typecheck/build verification locally inside `src/Frontend` (interactive `pnpm` approval timed out during automated execution):
  ```bash
  cd /Users/fabriciols/Repos/aira/src/Frontend
  pnpm lint && pnpm exec tsc --noEmit && pnpm build
  ```
