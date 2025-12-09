"""update_questiontheme_enum_to_uppercase

Revision ID: ee851f2b393c
Revises: a6308cf92433
Create Date: 2025-12-09 22:51:41.777415+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee851f2b393c'
down_revision = 'a6308cf92433'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update the questiontheme enum from lowercase to uppercase values
    # Drop the column that uses the enum
    op.drop_column('questions', 'theme')
    
    # Drop the old enum type
    op.execute("DROP TYPE IF EXISTS questiontheme")
    
    # Create the new enum type with uppercase values
    op.execute("""
        CREATE TYPE questiontheme AS ENUM (
            'MONICA_AGUA_BOA',
            'O_MENINO_MALUQUINHO',
            'O_PEQUENO_PRINCIPE'
        )
    """)
    
    # Re-add the column with the new enum type
    op.execute("""
        ALTER TABLE questions 
        ADD COLUMN theme questiontheme
    """)


def downgrade() -> None:
    # Reverse the migration by restoring lowercase enum values
    
    # Drop the column
    op.drop_column('questions', 'theme')
    
    # Drop the uppercase enum type
    op.execute("DROP TYPE IF EXISTS questiontheme")
    
    # Recreate the enum type with lowercase values
    op.execute("""
        CREATE TYPE questiontheme AS ENUM (
            'monica_agua_boa',
            'o_menino_maluquinho',
            'o_pequeno_principe'
        )
    """)
    
    # Re-add the column with the old enum type
    op.execute("""
        ALTER TABLE questions 
        ADD COLUMN theme questiontheme
    """)

