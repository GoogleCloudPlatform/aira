"""Add Admin role

Revision ID: 4c59ddc90b74
Revises: 8518ccf74f6b
Create Date: 2023-04-29 14:39:35.375451+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4c59ddc90b74"
down_revision = "8518ccf74f6b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO roles (id, name, display_name, description, scopes, created_at, updated_at)
        VALUES (
            uuid_generate_v4(), 'admin', '{"pt-BR": "Administrador", "en-US": "Administrator", "es-ES": "Administrador"}', '{"pt-BR": "Administrador", "en-US": "Administrator", "es-ES": "Administrador"}', '["admin"]', NOW(), NOW()
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM roles
        WHERE name = 'admin'
        """
    )
