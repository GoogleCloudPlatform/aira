"""Delete exam user table

Revision ID: ab7b8383843d
Revises: fcf319cac6bd
Create Date: 2023-06-06 20:31:58.815331+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ab7b8383843d"
down_revision = "fcf319cac6bd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("exams_users")


def downgrade() -> None:
    pass
