# School Reading Proficiency Agent - Implementation Walkthrough

We have successfully built the **autonomous educational agent** under the directory `/src/Agent` inside the workspace. The implementation is based on the Google ADK Framework, using an isolated Python environment to avoid versioning conflicts with backend tracing libraries.

---

## 1. Directory Structure Created

```
/Users/fabriciols/Repos/aira/src/Agent/
├── .env                         # Agent GenAI and database configurations
├── agent.py                     # Agent definition & root_agent exporter
├── poetry.lock                  # Poetry lockfile
├── pyproject.toml               # Dependency declarations (google-adk, asyncpg, sqlalchemy, bigquery)
├── run_playground.sh            # Playground local testing launch script
└── tools/
    ├── __init__.py              # Exposes compiled tools
    ├── bq_query.py              # BigQuery dynamic query runner (Least Privilege)
    └── db_auth.py               # Postgres manager authentication checker
```

---

## 2. Core Features Implemented

### A. Strict Authentication & Interactive Login Gate
To protect reading proficiency results, the agent implements an interactive gate at the start of a session:
1. **Interactive Greeting**: When the session begins, the agent greets the user and immediately asks for their email address.
2. **Database Lookup**: The agent triggers `tools/db_auth.py`, which establishes an async connection to the Postgres database to check if the email belongs to a registered user.
3. **Restricted Access**: If the user is not found, the agent politely rejects any query request, does not trigger BigQuery tools, and prompts for the email again.
4. **Authorized Scope**: If found, it stores their metadata (`role_name`, `allowed_organizations`, `allowed_groups`) inside the ADK session state memory.

### B. Security-Sanitized BigQuery Queries
School managers can query student scores and reading tiers using natural language:
*   The `tools/bq_query.py` client reads filters from the LLM (like school city, class name, exam name, date ranges).
*   It automatically pulls the user's `allowed_organizations` and `allowed_groups` lists from the session state.
*   It programmatically appends `school_uuid IN UNNEST(@allowed_orgs_param)` to the SQL query to guarantee that managers can **only** read results they have permission to see.

### C. Language & System Constraints
*   **Hardcoded Instructions**: All system prompt templates, reading level explanations, and tool schemas are written in **English**.
*   **Interaction Languages**: The conversation default is **English**, but it natively supports switching to **Portuguese (pt-br)** or **Spanish** if requested by the user. Any other languages are rejected.

### D. Reading Level Alignment
Pedagogical suggestions are grounded using the AIRA system's standard reading tiers:
*   `Pre-Reader 1 (Pré-leitor 1)`: Base level (similarity < 5%)
*   `Pre-Reader 2 (Pré-leitor 2)`: Spells out words (similarity >= 5%)
*   `Pre-Reader 3 (Pré-leitor 3)`: Reads syllable-by-syllable (similarity >= 10%)
*   `Pre-Reader 4 (Pré-leitor 4)`: Reads words incorrectly or few words
*   `Beginner Reader (Leitor Iniciante)`: Reads 11+ words correctly
*   `Fluent Reader (Leitor Fluente)`: High accuracy and comprehension

### E. Session Memory & Persistence
*   **Local testing**: Sessions are persisted in a local SQLite database (`.adk/sessions.db`).
*   **Production**: Session state is backed by the ADK `DatabaseSessionService` pointing to the PostgreSQL instance.

---

## 3. How to Start the Local Testing Playground

1.  Navigate to the agent directory:
    ```bash
    cd /Users/fabriciols/Repos/aira/src/Agent
    ```
2.  Launch the playground script:
    ```bash
    ./run_playground.sh
    ```
3.  Open the returned URL (typically `http://127.0.0.1:8000`) in your browser to interact with the agent dialogically.
