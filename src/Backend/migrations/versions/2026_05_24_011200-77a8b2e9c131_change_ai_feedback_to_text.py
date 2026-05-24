"""change ai feedback to text

Revision ID: 77a8b2e9c131
Revises: 3ffbcd242dd2
Create Date: 2026-05-24 01:12:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77a8b2e9c131'
down_revision = '3ffbcd242dd2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('exams_users', 'ai_exam_feedback', type_=sa.Text(), existing_type=sa.String(length=1000), existing_nullable=True)
    op.alter_column('exams_users_questions', 'ai_feedback', type_=sa.Text(), existing_type=sa.String(length=1000), existing_nullable=True)


def downgrade() -> None:
    op.alter_column('exams_users', 'ai_exam_feedback', type_=sa.String(length=1000), existing_type=sa.Text(), existing_nullable=True)
    op.alter_column('exams_users_questions', 'ai_feedback', type_=sa.String(length=1000), existing_type=sa.Text(), existing_nullable=True)
