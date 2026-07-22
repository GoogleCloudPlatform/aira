import os
import asyncpg
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
    
    # asyncpg requires postgresql:// instead of postgresql+asyncpg://
    db_uri = db_uri.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_uri)
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
        await conn.close()
