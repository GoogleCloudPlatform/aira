"""Add multiple choice

Revision ID: f5757084df5d
Revises: f110ee740ac4
Create Date: 2024-12-02 15:31:17.944597+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5757084df5d'
down_revision = 'f110ee740ac4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE questiontype_tmp AS ENUM('WORDS', 'COMPLEX_WORDS', 'PHRASES', 'MULTIPLE_CHOICE')")
    op.execute("""
        ALTER TABLE questions 
        ALTER COLUMN type TYPE questiontype_tmp 
        USING type::text::questiontype_tmp
    """)
    op.execute("DROP TYPE questiontype")
    op.execute("ALTER TYPE questiontype_tmp RENAME TO questiontype")


def downgrade() -> None:
    op.execute("UPDATE questions SET type = 'WORDS' WHERE type = 'MULTIPLE_CHOICE'")
    op.execute("CREATE TYPE questiontype_tmp AS ENUM('WORDS', 'COMPLEX_WORDS', 'PHRASES')")
    op.execute("""
        ALTER TABLE questions 
        ALTER COLUMN type TYPE questiontype_tmp 
        USING type::text::questiontype_tmp
    """)
    op.execute("DROP TYPE questiontype")
    op.execute("ALTER TYPE questiontype_tmp RENAME TO questiontype")
