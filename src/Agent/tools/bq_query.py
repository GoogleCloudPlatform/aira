import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from google.cloud import bigquery
from google.oauth2 import service_account
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv

load_dotenv()

def get_bq_client() -> bigquery.Client:
    """Initializes and returns a BigQuery Client using local credentials."""
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("_PROJECT_ID")
    creds_path = os.getenv("GCP_CREDENTIALS_PATH") or os.getenv("_GCP_STORAGE_CREDENTIALS")
    
    # Resolve relative credentials path
    if creds_path and not os.path.isabs(creds_path):
        # Resolve relative to backend if needed
        possible_paths = [
            creds_path,
            os.path.join("../Backend", creds_path),
            os.path.join("../../src/Backend", creds_path),
            os.path.abspath(creds_path)
        ]
        for path in possible_paths:
            if os.path.exists(path):
                creds_path = path
                break

    credentials = None
    if creds_path and os.path.exists(creds_path):
        credentials = service_account.Credentials.from_service_account_file(creds_path)
    
    return bigquery.Client(project=project_id, credentials=credentials)

async def query_reading_proficiency(
    school_name: Optional[str] = None,
    school_city: Optional[str] = None,
    school_state: Optional[str] = None,
    school_region: Optional[str] = None,
    class_name: Optional[str] = None,
    class_grade: Optional[str] = None,
    exam_name: Optional[str] = None,
    exam_start_date: Optional[str] = None,
    exam_end_date: Optional[str] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Queries reading proficiency results in BigQuery for students, filtered by school, city, grade, or exam.
    
    This tool dynamically queries the analytical BigQuery table to fetch students' reading outcomes,
    word counts, correct word counts (hits), and ratings. It automatically respects the user's
    security scopes (only accessing authorized schools and classes).

    Args:
        school_name: Filter by name of the school.
        school_city: Filter by city.
        school_state: Filter by state (2 letters code).
        school_region: Filter by school region.
        class_name: Filter by classroom name.
        class_grade: Filter by classroom grade (e.g. '2º Ano', '3º Ano').
        exam_name: Filter by exam name.
        exam_start_date: Filter by exam start date (YYYY-MM-DD format).
        exam_end_date: Filter by exam end date (YYYY-MM-DD format).

    Returns:
        A dictionary containing the query result rows under "records", or a success/error message.
    """
    if not tool_context:
        return {"success": False, "error": "System execution error: tool_context is missing"}
    
    print(f"[bq_query] query_reading_proficiency called with school_name='{school_name}', class_name='{class_name}', exam_name='{exam_name}', role='{tool_context.state.get('role_name')}'")
    
    # Retrieve security scopes from session state
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

    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("_PROJECT_ID")
    dataset = os.getenv("BQ_DATASET") or os.getenv("_BQ_DATASET", "dataset_lia")
    table_name = os.getenv("BQ_TABLE_NAME") or os.getenv("_BQ_TABLE_NAME", "student_results")
    full_table_path = f"{project_id}.{dataset}.{table_name}"

    # Build SQL constraints programmatically
    conditions = []
    query_params = []

    # Enforce Least Privilege Security Boundary
    if role_name != "admin":
        # Filter by allowed organizations (schools)
        if allowed_orgs:
            conditions.append("school_uuid IN UNNEST(@allowed_orgs_param)")
            query_params.append(bigquery.ArrayQueryParameter("allowed_orgs_param", "STRING", allowed_orgs))
        else:
            # If not admin and has no allowed organizations, they have access to nothing
            return {"success": True, "records": [], "message": "No organizations authorized for this user."}

        # Filter by allowed groups if specified
        if allowed_groups:
            conditions.append("class_uuid IN UNNEST(@allowed_groups_param)")
            query_params.append(bigquery.ArrayQueryParameter("allowed_groups_param", "STRING", allowed_groups))

    # Add dynamic user filters
    if school_name:
        conditions.append("TRIM(LOWER(school_name)) = TRIM(LOWER(@school_name_param))")
        query_params.append(bigquery.ScalarQueryParameter("school_name_param", "STRING", school_name))
    if school_city:
        conditions.append("TRIM(LOWER(school_city)) = TRIM(LOWER(@school_city_param))")
        query_params.append(bigquery.ScalarQueryParameter("school_city_param", "STRING", school_city))
    if school_state:
        conditions.append("TRIM(LOWER(school_state)) = TRIM(LOWER(@school_state_param))")
        query_params.append(bigquery.ScalarQueryParameter("school_state_param", "STRING", school_state))
    if school_region:
        conditions.append("TRIM(LOWER(school_region)) = TRIM(LOWER(@school_region_param))")
        query_params.append(bigquery.ScalarQueryParameter("school_region_param", "STRING", school_region))
    if class_name:
        conditions.append("TRIM(LOWER(class_name)) = TRIM(LOWER(@class_name_param))")
        query_params.append(bigquery.ScalarQueryParameter("class_name_param", "STRING", class_name))
    if class_grade:
        conditions.append("TRIM(LOWER(class_grade)) = TRIM(LOWER(@class_grade_param))")
        query_params.append(bigquery.ScalarQueryParameter("class_grade_param", "STRING", class_grade))
    if exam_name:
        conditions.append("TRIM(LOWER(exam_name)) = TRIM(LOWER(@exam_name_param))")
        query_params.append(bigquery.ScalarQueryParameter("exam_name_param", "STRING", exam_name))
        
    if exam_start_date:
        try:
            start_dt = datetime.strptime(exam_start_date.strip(), "%Y-%m-%d")
            conditions.append("exam_start_date >= @exam_start_date_param")
            query_params.append(bigquery.ScalarQueryParameter("exam_start_date_param", "TIMESTAMP", start_dt))
        except ValueError:
            return {"success": False, "error": f"Invalid start date format: {exam_start_date}. Use YYYY-MM-DD."}
            
    if exam_end_date:
        try:
            end_dt = datetime.strptime(exam_end_date.strip(), "%Y-%m-%d")
            conditions.append("exam_end_date <= @exam_end_date_param")
            query_params.append(bigquery.ScalarQueryParameter("exam_end_date_param", "TIMESTAMP", end_dt))
        except ValueError:
            return {"success": False, "error": f"Invalid end date format: {exam_end_date}. Use YYYY-MM-DD."}

    # Construct complete query
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
    SELECT 
        school_uuid, school_name, school_city, school_state, school_region,
        class_uuid, class_name, class_grade,
        student_uuid, student_name,
        exam_uuid, exam_name, exam_grade, exam_start_date, exam_end_date,
        question_uuid, question_amount_words,
        response_amount_hits, user_rating,
        -- Aggregate words statistics
        ARRAY_TO_STRING(question_words, ' ') as question_text,
        ARRAY_TO_STRING(response_words, ' ') as response_text
    FROM `{full_table_path}`
    {where_clause}
    LIMIT 200;
    """

    print(f"[bq_query] Running query:\n{query}")
    try:
        client = get_bq_client()
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        records = []
        for row in results:
            # Convert row to dictionary
            record = dict(row.items())
            # Convert timestamps to string format for JSON compatibility
            if record.get("exam_start_date"):
                record["exam_start_date"] = record["exam_start_date"].isoformat()
            if record.get("exam_end_date"):
                record["exam_end_date"] = record["exam_end_date"].isoformat()
            records.append(record)

        print(f"[bq_query] Query succeeded. Returned {len(records)} records.")
        return {
            "success": True,
            "records": records,
            "count": len(records)
        }
    except Exception as e:
        print(f"[bq_query] FAILED: {str(e)}")
        return {"success": False, "error": f"Failed to execute BigQuery query: {str(e)}"}
