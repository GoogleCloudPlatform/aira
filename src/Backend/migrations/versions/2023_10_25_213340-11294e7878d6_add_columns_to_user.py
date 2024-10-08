"""Add columns to user

Revision ID: 11294e7878d6
Revises: 2f4cd7846f29
Create Date: 2023-10-25 21:33:40.791833+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11294e7878d6'
down_revision = '2f4cd7846f29'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('organizations', 'county',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.add_column('users', sa.Column('state', sa.String(length=2), nullable=True))
    op.add_column('users', sa.Column('region', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('county', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'county')
    op.drop_column('users', 'region')
    op.drop_column('users', 'state')
    op.alter_column('organizations', 'county',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    # ### end Alembic commands ###
