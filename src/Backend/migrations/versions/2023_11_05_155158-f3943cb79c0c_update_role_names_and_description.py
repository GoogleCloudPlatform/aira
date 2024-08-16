"""Update role names and description

Revision ID: f3943cb79c0c
Revises: e1bdd39016fb
Create Date: 2023-11-05 15:51:58.571219+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3943cb79c0c'
down_revision = 'e1bdd39016fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE roles
            SET display_name = display_name::jsonb || '{"en-US": "School Manager", "es-ES": "Director de Escuela"}'::jsonb,
                description = display_name::jsonb || '{"en-US": "School Manager", "es-ES": "Director de Escuela"}'::jsonb
            WHERE name = 'school_manager';
        """
    )
    op.execute(
        """
        UPDATE roles
            SET display_name = display_name::jsonb || '{"en-US": "County Manager", "es-ES": "Gerente municipal"}'::jsonb,
                description = display_name::jsonb || '{"en-US": "County Manager", "es-ES": "Gerente municipal"}'::jsonb
            WHERE name = 'county_manager';
        """
    )
    op.execute(
        """
        UPDATE roles
            SET display_name = display_name::jsonb || '{"en-US": "Regional Education Manager", "es-ES": "Gerente Regional de Educacíon"}'::jsonb,
                description = display_name::jsonb || '{"en-US": "Regional Education Manager", "es-ES": "Gerente Regional de Educacíon"}'::jsonb
            WHERE name = 'ed_regional_manager';
        """
    )
    op.execute(
        """
        UPDATE roles
            SET display_name = display_name::jsonb || '{"en-US": "State Manager", "es-ES": "Gerente Estatal"}'::jsonb,
                description = display_name::jsonb || '{"en-US": "State Manager", "es-ES": "Gerente Estatal"}'::jsonb

            WHERE name = 'state_manager';
        """
    )



def downgrade() -> None:
    pass
