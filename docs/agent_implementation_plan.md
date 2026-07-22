# School Reading Proficiency Autonomous Agent - Implementation Plan

This document outlines the architecture, data security flows, and implementation steps for building a 100% autonomous educational agent using the **Google ADK Framework**. This agent enables school managers to analyze reading proficiency gaps dialogically.

---

## 1. Directory Structure

The agent codebase will reside in a new folder at `/src/Agent`, decoupled from the API backend but leveraging its virtual environment and database models.

```
/Users/fabriciols/Repos/aira/src/Agent/
├── .env                         # Agent-specific local configuration
├── agent.py                     # Agent definition (instantiates LlmAgent as root_agent)
├── run_playground.sh            # Script to run ADK Playground locally
├── requirements.txt             # Reference dependencies
└── tools/
    ├── __init__.py
    ├── db_auth.py               # Postgres tool (User metadata & auth context)
    ├── bq_query.py              # BigQuery tool (Grounding and metrics extraction)
    └── educational_analysis.py  # (Optional) Pedagogical guidelines and processing
```

---

## 2. Dependency Management & Environment Isolation (Selected)

Due to version conflicts between the backend's telemetry framework (`opentelemetry-instrumentation-sqlalchemy 0.41b0`) and the packages required by `google-adk` (`opentelemetry-sdk >=1.39`), **a dedicated, isolated Poetry environment will be initialized for the agent inside `/src/Agent`**.

### Environment Isolation Design:
*   **Decoupled Architecture**: `/src/Agent` will have its own independent `pyproject.toml` and lockfile.
*   **Version Independence**: This allows `google-adk` (version `2.5.0` or higher) to coexist safely with its required versions of `fastapi`, `httpx`, `opentelemetry-sdk`, and `pydantic v2` without altering or breaking the core `/src/Backend` dependencies.
*   **Database Interfacing**: To prevent duplication of complex SQLAlchemy schemas while maintaining environment isolation, the Postgres tool (`db_auth.py`) will perform direct SQL queries (or define a minimal, lightweight SQLAlchemy schema mapping only the required lookup fields for the `users`, `users_organizations`, and `users_groups` tables).

---

## 3. Database & Tool Architecture

### A. Postgres Authentication, Login Flow & Context Tool (`db_auth.py`)
To satisfy the security requirement of Least Privilege and protect school reading data, a strict interactive authentication process is enforced:

*   **Authentication Flow (Interactive Gate)**:
    *   **Greeting & Request**: Upon starting a session, the agent's very first turn (after a brief greeting) *must* request the user to provide their school manager email address.
    *   **Verification**: The agent immediately calls the `db_auth` tool with the provided email.
    *   **Strict Access Control**: 
        *   If the email does *not* exist in the Postgres database, the agent prints a polite access-denied message and prompts for the email again. The agent *must not* execute any other tools or answer any data-related queries until a valid email is authenticated.
        *   If found, the agent loads the profile, greets the user by name, stores the authorization context in memory, and allows queries.
*   **Context Retrieval Tool (`db_auth.py`)**:
    *   **Communication Channels**: The tool can query manager metadata using either:
        *   *Option A (Direct DB)*: Connecting directly to Postgres via SQLAlchemy/asyncpg using the `DATABASE_URI` environment variable (ideal for local testing).
        *   *Option B (REST API)*: Performing an HTTP REST call to AIRA's Backend API (e.g. `/users/me` or `/users` endpoints, if the backend is configured to support email-based queries or if active auth tokens are passed from the client) to fetch user profiles.
    *   Retrieves the manager's metadata:
        *   `role` (e.g., Regional School Manager, School Manager, Teacher).
        *   `allowed_organizations` (list of authorized `school_uuid` values).
        *   `allowed_groups` (list of authorized `class_uuid` values).
    *   Saves this context to the active session state/memory.

### B. BigQuery Analytical Tool (`bq_query.py`)
School managers need to ask questions like: *"What is the reading proficiency of 2nd graders in School X?"* or *"Which cities have the largest proficiency gaps?"*

*   **Functionality**:
    *   Generates a safe BigQuery SQL query to the `dataset_lia` analytical table.
    *   **Strict Security Parameterization**: To prevent SQL Injection or horizontal privilege escalation (viewing unauthorized schools), the tool will construct queries dynamically using `bigquery.ScalarQueryParameter` and `bigquery.ArrayQueryParameter`, explicitly adding constraints:
        `WHERE school_uuid IN UNNEST(@allowed_schools) AND class_uuid IN UNNEST(@allowed_classes)`
    *   Executes the query and returns aggregated statistics (accuracy, word counts, common error words).

### C. Pedagogical Instruction, Language & System Rules
The agent's system instructions and prompt rules will be configured with the following constraints:

*   **Hardcoded Instruction Language**: All system instructions, prompt templates, and agent rules *must* be written in **English**.
*   **Supported Conversation Languages**:
    *   **Default Language**: The agent defaults to conversing in **English**.
    *   **Language Switching**: The user can ask to switch the conversation language. The only supported languages are: **English**, **Portuguese (pt-br)**, and **Spanish**.
    *   **Block Unallowed Languages**: If a user attempts to speak in any other language or requests to switch to an unsupported language, the agent *must* politely decline and explain that only English, Portuguese, and Spanish are supported.
*   **Reading Proficiency Tiers**:
    *   **Pre-Reader 1 (Pré-leitor 1)**: Base pre-reading tier. No syllable or spelling recognition (usually similarity percentage < 5%).
    *   **Pre-Reader 2 (Pré-leitor 2)**: Emergent pre-reading tier. Student spells out words letter-by-letter (similarity >= 5%).
    *   **Pre-Reader 3 (Pré-leitor 3)**: Syllabic pre-reading tier. Student reads syllable-by-syllable (similarity >= 10%).
    *   **Pre-Reader 4 (Pré-leitor 4)**: Emergent word recognition. Student reads words incorrectly or reads some words correctly (but fewer than 11 words).
    *   **Beginner Reader (Leitor Iniciante)**: Word recognition tier. Student reads at least 11 words correctly in word-level exams.
    *   **Fluent Reader (Leitor Fluente)**: Fluent reading tier. High accuracy and automaticity.
*   **Analysis Guidelines**: Instructs the LLM to identify specific phonetic and reading progression gaps (e.g., spelling behaviors, syllable-level halting, sound-symbol correspondence struggles) by analyzing mismatches in the `question_words` and `response_words` arrays.
*   **Actionable Remediation**: Instructions on suggesting targeted interventions matching the student's rating tier (e.g., phonetic decoding exercises for Pre-Reader 2/3, word-recognition automaticity games for Pre-Reader 4/Beginner Readers) based on query findings.

### D. Agent Memory & Session Persistence
The agent must keep track of user context, conversation state, and history across turns:
*   **Local Development Memory**: In the local testing and playground environment, the ADK `sqlite` session and memory service will be enabled. It persists the conversation log and session state variables to a local SQLite database (`.adk/sessions.db`).
*   **Production Deployment Memory**: In the cloud/production deployment, session data will be backed by a relational database session provider (`DatabaseSessionService`) pointing to the Postgres instance, ensuring horizontal scaling and high availability of session state.

---

## 4. Environment Variables (`.env`)

The local configuration file `/src/Agent/.env` will define:

```env
# Google GenAI Settings
GEMINI_API_KEY="your-api-key"
MODEL_VERSION="gemini-3.5-flash"

# Database Configuration
DATABASE_URI="postgresql+asyncpg://fabriciols@localhost:5432/aira"

# BigQuery Configuration
GCP_PROJECT_ID="aira-demo-eaed8"
BQ_DATASET="dataset_lia"
BQ_TABLE_NAME="student_results"
GCP_CREDENTIALS_PATH="../Backend/aira-sa-local-access-key.json"
```

---

## 5. ADK Playground Configuration

To test the agent locally using the Web UI provided by Google ADK:
We will write a shell script `/src/Agent/run_playground.sh`:

```bash
#!/bin/bash
# Load local environment variables
export $(grep -v '^#' .env | xargs)

# Launch ADK Web UI using Agent's own Poetry environment
poetry run google-adk web .
```

---

## 6. Implementation Steps

1.  **Create Agent Directory**: Create `/src/Agent` and `/src/Agent/tools`.
2.  **Initialize Isolated Poetry Project**: In `/src/Agent`, initialize a new Poetry environment (`poetry init`) and add packages: `poetry add google-adk asyncpg sqlalchemy google-cloud-bigquery`.
3.  **Postgres Context Tool**: Write `tools/db_auth.py` with standalone async Postgres connection capability to query and authenticate users.
4.  **BigQuery Analytical Tool**: Write `tools/bq_query.py` utilizing the BigQuery client.
5.  **Agent Assembly**: Write `agent.py` setting up `root_agent` with English system instructions, greeting, authentication gate, allowed languages, tools, and configurations.
6.  **Environment Setup**: Create `src/Agent/.env` based on existing local setups.
7.  **Playground Launch Script**: Create and grant executable permissions to `src/Agent/run_playground.sh`.

---

## Verification Plan

### Automated Security Check

- **Security Scanner**: Run a scan on all newly created files to identify common vulnerabilities (e.g., XSS, SQL injection). If findings are detected, auto-apply the fix and document the results.
- **Security Audit**: Audit the new code for design-level security issues (input validation, secrets handling, auth checks). Document findings and remediations in the `walkthrough.md` artifact using the `generate_security_audit_report` skill.

### Manual Verification
- Launch the ADK Playground using `run_playground.sh` and access it via browser.
- Perform test runs simulating a "School Manager" user role.
- Verify that queries to BigQuery successfully fetch results only for the manager's authorized schools, confirming that the security boundary holds.
