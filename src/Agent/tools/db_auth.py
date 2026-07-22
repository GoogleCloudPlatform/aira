import os
import asyncio
import asyncpg
from google.cloud.sql.connector import Connector
from dotenv import load_dotenv

# Load .env file from the Agent directory if present
load_dotenv()

async def get_user_context(email: str) -> dict | None:
    """Retrieves school manager authentication profile and allowed schools/groups.

    Args:
        email: The email address of the school manager to verify.

    Returns:
        A dictionary containing the user's role, name, and lists of allowed
        organization and group UUID strings. Returns None if user is not found.
    """
    # Retrieve DATABASE_URI from environment
    db_uri = os.getenv("DATABASE_URI") or os.getenv("_DATABASE_URI")
    if not db_uri:
        raise ValueError("DATABASE_URI environment variable is not set")
    
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
    print(f"[db_auth] Lookup email: '{email}'")
    print(f"[db_auth] Using instance_connection_name: {instance_connection_name}")
    
    conn = None
    connector = None
    
    try:
        if instance_connection_name:
            from sqlalchemy.engine import make_url
            
            # Parse db connection params from db_uri
            url = make_url(db_uri)
            db_user = url.username
            db_pass = url.password
            db_name = url.database
            
            print(f"[db_auth] Connecting to Cloud SQL instance: {instance_connection_name} as user {db_user}...")
            loop = asyncio.get_running_loop()
            connector = Connector(loop=loop)
            conn = await connector.connect_async(
                instance_connection_name,
                "asyncpg",
                user=db_user,
                password=db_pass,
                db=db_name
            )
        else:
            # asyncpg requires postgresql:// instead of postgresql+asyncpg://
            db_uri = db_uri.replace("postgresql+asyncpg://", "postgresql://")
            print(f"[db_auth] Connecting to direct DB URI...")
            conn = await asyncpg.connect(db_uri)
        print("[db_auth] Connection established successfully.")
    except Exception as connect_err:
        import traceback
        print(f"[db_auth] DATABASE CONNECTION FAILED: {connect_err}")
        traceback.print_exc()
        raise connect_err

    try:
        query = """
        SELECT 
            u.id::text AS user_id, 
            u.name AS user_name, 
            u.email_address, 
            r.name AS role_name,
            -- Subquery to get organization IDs
            COALESCE(
                (SELECT array_agg(uo.organization_id::text) FROM users_organizations uo WHERE uo.user_id = u.id),
                ARRAY[]::text[]
            ) AS allowed_organizations,
            -- Subquery to get group IDs
            COALESCE(
                (SELECT array_agg(ug.group_id::text) FROM users_groups ug WHERE ug.user_id = u.id),
                ARRAY[]::text[]
            ) AS allowed_groups
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.email_address = $1;
        """
        row = await conn.fetchrow(query, email.strip())
        if not row:
            return None
        
        return {
            "user_id": row["user_id"],
            "user_name": row["user_name"],
            "email_address": row["email_address"],
            "role_name": row["role_name"],
            "allowed_organizations": list(row["allowed_organizations"]) if row["allowed_organizations"] else [],
            "allowed_groups": list(row["allowed_groups"]) if row["allowed_groups"] else []
        }
    finally:
        if conn:
            await conn.close()
        if connector:
            await connector.close_async()
