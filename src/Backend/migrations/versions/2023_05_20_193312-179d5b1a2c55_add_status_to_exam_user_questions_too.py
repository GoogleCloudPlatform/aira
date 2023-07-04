"""Add status to exam/user/questions too

Revision ID: 179d5b1a2c55
Revises: 25e2e05c5fc5
Create Date: 2023-05-20 19:33:12.722353+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '179d5b1a2c55'
down_revision = '25e2e05c5fc5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exams_users_questions', sa.Column('status', postgresql.ENUM('NOT_STARTED', 'IN_PROGRESS', 'FINISHED', name='examstatus'), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('exams_users_questions', 'status')
    # ### end Alembic commands ###