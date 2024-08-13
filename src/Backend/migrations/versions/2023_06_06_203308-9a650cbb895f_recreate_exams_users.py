"""Recreate exams_users

Revision ID: 9a650cbb895f
Revises: ab7b8383843d
Create Date: 2023-06-06 20:33:08.533203+00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9a650cbb895f"
down_revision = "ab7b8383843d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "exams_users",
        sa.Column("exam_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "NOT_STARTED",
                "IN_PROGRESS",
                "FINISHED",
                name="examstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["exam_id"],
            ["exams.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("exam_id", "user_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("exams_users")
    # ### end Alembic commands ###
