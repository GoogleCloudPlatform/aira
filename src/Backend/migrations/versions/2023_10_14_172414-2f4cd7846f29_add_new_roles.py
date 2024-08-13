"""Add new roles

Revision ID: 2f4cd7846f29
Revises: bdae7a246545
Create Date: 2023-10-14 17:24:14.222496+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f4cd7846f29'
down_revision = 'bdae7a246545'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO roles (id, name, display_name, description, scopes, created_at, updated_at)
        VALUES (
            uuid_generate_v4(), 'school_manager', '{"pt-BR": "Gestor de Escola"}', '{}', '["dashboard.viewer"]', NOW(), NOW()
        )
        """
    )
    op.execute(
        """
        INSERT INTO roles (id, name, display_name, description, scopes, created_at, updated_at)
        VALUES (
            uuid_generate_v4(), 'county_manager', '{"pt-BR": "Gestor de Município"}', '{}', '["dashboard.viewer"]', NOW(), NOW()
        )
        """
    )
    op.execute(
        """
        INSERT INTO roles (id, name, display_name, description, scopes, created_at, updated_at)
        VALUES (
            uuid_generate_v4(), 'ed_regional_manager', '{"pt-BR": "Gestor da Regional de Educação"}', '{}', '["dashboard.viewer"]', NOW(), NOW()
        )
        """
    )
    op.execute(
        """
        INSERT INTO roles (id, name, display_name, description, scopes, created_at, updated_at)
        VALUES (
            uuid_generate_v4(), 'state_manager', '{"pt-BR": "Gestor Estadual"}', '{}', '["dashboard.viewer"]', NOW(), NOW()
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE 
            FROM roles 
            WHERE name in 
                ('school_manager', 'county_manager', 'ed_regional_manager', 'state_manager');
        """
    )
