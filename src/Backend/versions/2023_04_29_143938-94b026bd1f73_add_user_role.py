"""Add User role

Revision ID: 94b026bd1f73
Revises: 4c59ddc90b74
Create Date: 2023-04-29 14:39:38.166711+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94b026bd1f73'
down_revision = '4c59ddc90b74'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO roles (id, name, display_name, description, scopes, created_at, updated_at)
        VALUES (
            uuid_generate_v4(), 'user', '{"pt-BR": "Aluno", "en-US": "Student", "es-ES": "Alumno"}', '{"pt-BR": "Aluno", "en-US": "Student", "es-ES": "Alumno"}', '["user"]', NOW(), NOW()
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM roles
        WHERE name = 'user'
        """
    )