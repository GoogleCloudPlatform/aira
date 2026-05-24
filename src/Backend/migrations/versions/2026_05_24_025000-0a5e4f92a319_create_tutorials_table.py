"""create tutorials table

Revision ID: 0a5e4f92a319
Revises: 77a8b2e9c131
Create Date: 2026-05-24 02:50:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a5e4f92a319'
down_revision = '77a8b2e9c131'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('tutorials',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('audience', sa.String(length=50), nullable=False),
    sa.Column('source_type', sa.String(length=50), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=True),
    sa.Column('file_path', sa.String(length=512), nullable=True),
    sa.Column('bucket_name', sa.String(length=255), nullable=True),
    sa.Column('url', sa.String(length=1024), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('tutorials')
