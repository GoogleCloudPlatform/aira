"""Add order to question

Revision ID: 5068b03bf199
Revises: ce130db65df2
Create Date: 2024-04-03 19:04:55.248297+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5068b03bf199'
down_revision = 'ce130db65df2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("COMMIT;")
    op.add_column('questions', sa.Column('order', sa.SmallInteger(), nullable=True))
    op.execute(
        """
        UPDATE questions 
            SET "order" = (
                CASE 
                    WHEN "type" = 'WORDS' then 1 
                    WHEN "type" = 'COMPLEX_WORDS' then 2 
                    WHEN "type" = 'PHRASES' then 3 
                END
            )
        """
    )
    op.alter_column("questions", "order", nullable=False)


def downgrade() -> None:
    op.drop_column('questions', 'order')
