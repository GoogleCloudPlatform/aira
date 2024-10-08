"""Add customer ids and region to organization

Revision ID: a8fb190bf415
Revises: 431170d168be
Create Date: 2023-06-05 21:01:45.335454+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8fb190bf415'
down_revision = '431170d168be'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('groups', sa.Column('customer_id', sa.String(length=100), nullable=True))
    op.add_column('organizations', sa.Column('customer_id', sa.String(length=100), nullable=True))
    op.add_column('organizations', sa.Column('region', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('organizations', 'region')
    op.drop_column('organizations', 'customer_id')
    op.drop_column('groups', 'customer_id')
    # ### end Alembic commands ###
