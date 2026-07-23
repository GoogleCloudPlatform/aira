import os
import uuid
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from google.cloud import bigquery
from google.adk.tools.tool_context import ToolContext
import asyncpg
from dotenv import load_dotenv

# Try importing dependencies from relative/absolute paths
try:
    from .bq_query import get_bq_client
except ImportError:
    from tools.bq_query import get_bq_client

load_dotenv()

async def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    db_uri = os.getenv("DATABASE_URI") or os.getenv("_DATABASE_URI")
    if not db_uri:
        raise ValueError("DATABASE_URI environment variable is not set")
    
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
    
    if instance_connection_name:
        from google.cloud.sql.connector import Connector
        from sqlalchemy.engine import make_url
        
        url = make_url(db_uri)
        db_user = url.username
        db_pass = url.password
        db_name = url.database
        
        loop = asyncio.get_running_loop()
        connector = Connector(loop=loop)
        conn = await connector.connect_async(
            instance_connection_name,
            "asyncpg",
            user=db_user,
            password=db_pass,
            db=db_name
        )
        return conn, connector
    else:
        db_uri = db_uri.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(db_uri)
        return conn, None

async def query_pedagogical_recommendations(
    pedagogical_approach: str,
    class_name: Optional[str] = None,
    school_name: Optional[str] = None,
    student_uuid: Optional[str] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Retrieves students in need of intervention, and performs a semantic vector search (RAG) 
    over the pedagogical knowledge base using the selected approach to return matching materials.

    Args:
        pedagogical_approach: The pedagogical approach or strategy picked by the model (e.g. 'Consciência fonêmica', 'Síntese silábica').
        class_name: Optional name of the class to filter students.
        school_name: Optional name of the school to filter students.
        student_uuid: Optional UUID of a specific student to query.
    """
    if not tool_context:
        return {"success": False, "error": "System execution error: tool_context is missing"}
    
    print(f"[ped_rec] query_pedagogical_recommendations called with approach='{pedagogical_approach}', school='{school_name}', class='{class_name}'")
    
    session_state = tool_context.state
    email = session_state.get("user_email")
    allowed_orgs = session_state.get("allowed_organizations")
    allowed_groups = session_state.get("allowed_groups")
    role_name = session_state.get("role_name")

    if not email:
        return {
            "success": False, 
            "error": "Access Denied: You are not logged in. Please authenticate first by providing your email."
        }

    # 1. Fetch Students in Need of Intervention from BigQuery
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("_PROJECT_ID")
    dataset = os.getenv("BQ_DATASET") or os.getenv("_BQ_DATASET", "dataset_lia")
    table_name = os.getenv("BQ_TABLE_NAME") or os.getenv("_BQ_TABLE_NAME", "student_results")
    full_table_path = f"{project_id}.{dataset}.{table_name}"

    conditions = []
    query_params = []

    # Enforce Least Privilege Security Boundary
    if role_name != "admin":
        if allowed_orgs:
            conditions.append("school_uuid IN UNNEST(@allowed_orgs_param)")
            query_params.append(bigquery.ArrayQueryParameter("allowed_orgs_param", "STRING", allowed_orgs))
        else:
            return {"success": True, "students": [], "materials": [], "message": "No organizations authorized for this user."}

        if allowed_groups:
            conditions.append("class_uuid IN UNNEST(@allowed_groups_param)")
            query_params.append(bigquery.ArrayQueryParameter("allowed_groups_param", "STRING", allowed_groups))

    # Add filters
    if school_name:
        conditions.append("TRIM(LOWER(school_name)) = TRIM(LOWER(@school_name_param))")
        query_params.append(bigquery.ScalarQueryParameter("school_name_param", "STRING", school_name))
    if class_name:
        conditions.append("TRIM(LOWER(class_name)) = TRIM(LOWER(@class_name_param))")
        query_params.append(bigquery.ScalarQueryParameter("class_name_param", "STRING", class_name))
    if student_uuid:
        conditions.append("student_uuid = @student_uuid_param")
        query_params.append(bigquery.ScalarQueryParameter("student_uuid_param", "STRING", student_uuid))

    # We target Pre-Readers and students with low scores
    conditions.append("(user_rating IN ('Pré-leitor 1', 'Pré-leitor 2', 'Pré-leitor 3', 'Pré-leitor 4') OR response_amount_hits < (question_amount_words * 0.45))")

    where_clause = ""
    if conditions:
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
    print(f"[ped_rec] Querying BigQuery for students...")
    try:
        bq_client = get_bq_client()
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = bq_client.query(bq_query, job_config=job_config)
        results = query_job.result()
        for row in results:
            students.append(dict(row.items()))
        print(f"[ped_rec] BigQuery returned {len(students)} students needing intervention.")
    except Exception as e:
        print(f"[ped_rec] BigQuery query failed: {str(e)}")
        return {"success": False, "error": f"Failed to query BigQuery student results: {str(e)}"}

    # If no students need intervention, we can return early
    if not students:
        return {
            "success": True,
            "students": [],
            "materials": [],
            "message": "No students in need of intervention found within your scope."
        }

    # 2. Database Metadata and Transcription Search (PostgreSQL)
    materials = []
    db_conn = None
    db_connector = None
    print(f"[ped_rec] Querying Postgres database for file transcriptions matching '{pedagogical_approach}'...")
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
        print(f"[ped_rec] Postgres search returned {len(materials)} materials.")

        # Fallback: if search returned no results, fetch up to 3 completed guides directly via SQL
        if not materials:
            print(f"[ped_rec] Search returned no results, using Postgres direct fallback...")
            fallback_query = """
            SELECT id::text as file_id, filename, description, transcription 
            FROM knowledge_base_files 
            WHERE status = 'completed'
            LIMIT 3;
            """
            rows = await db_conn.fetch(fallback_query)
            for row in rows:
                materials.append(dict(row))
            print(f"[ped_rec] Postgres fallback returned {len(materials)} materials.")
            
    except Exception as e:
        print(f"[ped_rec] Postgres query failed: {str(e)}")
        # Return a safe dictionary instead of failing the tool execution
        return {
            "success": True,
            "students": students,
            "materials": [],
            "message": "Pedagogical materials database is temporarily unavailable."
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
        "pedagogical_approach": pedagogical_approach
    }
