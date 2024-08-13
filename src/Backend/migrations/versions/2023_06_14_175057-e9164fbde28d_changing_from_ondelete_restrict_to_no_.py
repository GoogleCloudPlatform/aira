"""Changing from ondelete restrict to no action

Revision ID: e9164fbde28d
Revises: 181afb8d0e87
Create Date: 2023-06-14 17:50:57.396498+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9164fbde28d'
down_revision = '181afb8d0e87'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('exams_users_questions_group_id_fkey', 'exams_users_questions', type_='foreignkey')
    op.drop_constraint('exams_users_questions_organization_id_fkey', 'exams_users_questions', type_='foreignkey')
    op.drop_constraint('exams_users_questions_user_id_fkey', 'exams_users_questions', type_='foreignkey')
    op.drop_constraint('exams_users_questions_question_id_fkey', 'exams_users_questions', type_='foreignkey')
    op.drop_constraint('exams_users_questions_exam_id_fkey', 'exams_users_questions', type_='foreignkey')
    op.create_foreign_key(None, 'exams_users_questions', 'questions', ['question_id'], ['id'], ondelete='NO ACTION')
    op.create_foreign_key(None, 'exams_users_questions', 'organizations', ['organization_id'], ['id'], ondelete='NO ACTION')
    op.create_foreign_key(None, 'exams_users_questions', 'exams', ['exam_id'], ['id'], ondelete='NO ACTION')
    op.create_foreign_key(None, 'exams_users_questions', 'groups', ['group_id'], ['id'], ondelete='NO ACTION')
    op.create_foreign_key(None, 'exams_users_questions', 'users', ['user_id'], ['id'], ondelete='NO ACTION')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'exams_users_questions', type_='foreignkey')
    op.drop_constraint(None, 'exams_users_questions', type_='foreignkey')
    op.drop_constraint(None, 'exams_users_questions', type_='foreignkey')
    op.drop_constraint(None, 'exams_users_questions', type_='foreignkey')
    op.drop_constraint(None, 'exams_users_questions', type_='foreignkey')
    op.create_foreign_key('exams_users_questions_exam_id_fkey', 'exams_users_questions', 'exams', ['exam_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('exams_users_questions_question_id_fkey', 'exams_users_questions', 'questions', ['question_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('exams_users_questions_user_id_fkey', 'exams_users_questions', 'users', ['user_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('exams_users_questions_organization_id_fkey', 'exams_users_questions', 'organizations', ['organization_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('exams_users_questions_group_id_fkey', 'exams_users_questions', 'groups', ['group_id'], ['id'], ondelete='RESTRICT')
    # ### end Alembic commands ###
