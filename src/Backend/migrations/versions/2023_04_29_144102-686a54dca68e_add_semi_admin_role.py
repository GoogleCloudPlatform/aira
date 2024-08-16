"""Add Semi-Admin role

Revision ID: 686a54dca68e
Revises: 94b026bd1f73
Create Date: 2023-04-29 14:41:02.669222+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "686a54dca68e"
down_revision = "94b026bd1f73"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO roles (id, name, display_name, description, scopes, created_at, updated_at)
        VALUES (
            uuid_generate_v4(), 'semi-admin', '{"pt-BR": "Professor", "en-US": "Teacher", "es-ES": "Profesor"}', '{"pt-BR": "Professor", "en-US": "Teacher", "es-ES": "Profesor"}', '["semi-admin"]', NOW(), NOW()
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM roles
        WHERE name = 'semi-admin'
        """
    )
