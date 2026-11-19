import logging
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext
from google.cloud import bigquery

# Try importing dependencies from relative/absolute paths
try:
    from .bq_query import _resolve_bq_table_path, get_bq_client
    from .db_auth import authenticate_tool_context, get_db_connection
except ImportError:
    from tools.bq_query import _resolve_bq_table_path, get_bq_client
    from tools.db_auth import authenticate_tool_context, get_db_connection

load_dotenv()

logger = logging.getLogger(__name__)


async def query_pedagogical_recommendations(
    pedagogical_approach: str,
    class_name: Optional[str] = None,
    school_name: Optional[str] = None,
    student_uuid: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, Any]:
    """Retrieves students in need of intervention and matching pedagogical materials.

    Verifies the caller's cryptographic AIRA session token and live database
    authorization boundaries before querying student analytics or knowledge-base records.

    Args:
        pedagogical_approach: The pedagogical approach or strategy picked by the model
            (e.g. 'Consciência fonêmica', 'Síntese silábica').
        class_name: Optional name of the class to filter students.
        school_name: Optional name of the school to filter students.
        student_uuid: Optional UUID of a specific student to query.
    """
    if not tool_context:
        return {"success": False, "error": "Access Denied: Missing execution context."}

    user_context = await authenticate_tool_context(tool_context)
    if not user_context:
        return {
            "success": False,
            "error": "Access Denied: Valid authentication credentials are required.",
        }

    is_admin = bool(user_context["is_admin"])
    allowed_orgs = user_context["allowed_organizations"]
    allowed_groups = user_context["allowed_groups"]

    # 1. Fetch Students in Need of Intervention from BigQuery
    full_table_path = _resolve_bq_table_path()
    if not full_table_path:
        logger.error("Invalid or missing BigQuery configuration; failing closed.")
        return {
            "success": False,
            "error": "Unable to retrieve pedagogical recommendations right now.",
        }

    conditions = []
    query_params = []

    # Enforce Least Privilege Security Boundary using live verified DB scopes
    if not is_admin:
        if allowed_orgs:
            conditions.append("school_uuid IN UNNEST(@allowed_orgs_param)")
            query_params.append(
                bigquery.ArrayQueryParameter("allowed_orgs_param", "STRING", allowed_orgs)
            )
        else:
            return {
                "success": True,
                "students": [],
                "materials": [],
                "message": "No organizations authorized for this user.",
            }

        if allowed_groups:
            conditions.append("class_uuid IN UNNEST(@allowed_groups_param)")
            query_params.append(
                bigquery.ArrayQueryParameter(
                    "allowed_groups_param", "STRING", allowed_groups
                )
            )

    # Add filters
    if school_name:
        conditions.append("TRIM(LOWER(school_name)) = TRIM(LOWER(@school_name_param))")
        query_params.append(
            bigquery.ScalarQueryParameter("school_name_param", "STRING", school_name)
        )
    if class_name:
        conditions.append("TRIM(LOWER(class_name)) = TRIM(LOWER(@class_name_param))")
        query_params.append(
            bigquery.ScalarQueryParameter("class_name_param", "STRING", class_name)
        )
    if student_uuid:
        conditions.append("student_uuid = @student_uuid_param")
        query_params.append(
            bigquery.ScalarQueryParameter("student_uuid_param", "STRING", student_uuid)
        )

    # We target Pre-Readers and students with low scores
    conditions.append(
        "(user_rating IN ('Pré-leitor 1', 'Pré-leitor 2', 'Pré-leitor 3', 'Pré-leitor 4') "
        "OR response_amount_hits < (question_amount_words * 0.45))"
    )

    where_clause = "WHERE " + " AND ".join(conditions)

    bq_query = f"""
    SELECT
        school_uuid, school_name,
        class_uuid, class_name, class_grade,
        student_uuid, student_name,
        user_rating, response_amount_hits, question_amount_words,
        ARRAY_TO_STRING(question_words, ' ') as question_text,
        ARRAY_TO_STRING(response_words, ' ') as response_text
    FROM `{full_table_path}`
    {where_clause}
    LIMIT 50;
    """

    students = []
    try:
        bq_client = get_bq_client()
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = bq_client.query(bq_query, job_config=job_config)
        results = query_job.result()
        for row in results:
            students.append(dict(row.items()))
    except Exception:
        logger.warning("BigQuery lookup for pedagogical recommendations failed.")
        return {
            "success": False,
            "error": "Unable to retrieve student proficiency data right now.",
        }

    # If no students need intervention, we can return early
    if not students:
        return {
            "success": True,
            "students": [],
            "materials": [],
            "message": "No students in need of intervention found within your scope.",
        }

    # 2. Database Metadata and Transcription Search (PostgreSQL)
    materials = []
    db_conn = None
    db_connector = None
    try:
        db_conn, db_connector = await get_db_connection()

        # Search using ILIKE for files containing the selected pedagogical approach
        search_query = """
        SELECT id::text as file_id, filename, description, transcription
        FROM knowledge_base_files
        WHERE status = 'completed'
          AND (
              filename ILIKE $1
              OR description ILIKE $1
              OR transcription ILIKE $1
          )
        LIMIT 4;
        """
        search_param = f"%{pedagogical_approach}%"
        rows = await db_conn.fetch(search_query, search_param)
        for row in rows:
            materials.append(dict(row))

        # Fallback: if search returned no results, fetch up to 3 completed guides directly via SQL
        if not materials:
            fallback_query = """
            SELECT id::text as file_id, filename, description, transcription
            FROM knowledge_base_files
            WHERE status = 'completed'
            LIMIT 3;
            """
            rows = await db_conn.fetch(fallback_query)
            for row in rows:
                materials.append(dict(row))
    except Exception:
        logger.warning("Knowledge base lookup failed for pedagogical recommendations.")
        return {
            "success": True,
            "students": students,
            "materials": [],
            "message": "Pedagogical materials database is temporarily unavailable.",
        }
    finally:
        if db_conn:
            await db_conn.close()
        if db_connector:
            await db_connector.close_async()

    return {
        "success": True,
        "students": students,
        "vector_chunks": [],
        "materials": materials,
        "pedagogical_approach": pedagogical_approach,
    }
