"""create knowledge base files table

Revision ID: a8f0b99f1234
Revises: 0a5e4f92a319
Create Date: 2026-07-22 16:33:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8f0b99f1234'
down_revision = '0a5e4f92a319'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('knowledge_base_files',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.String(length=512), nullable=False),
    sa.Column('bucket_name', sa.String(length=255), nullable=False),
    sa.Column('content_type', sa.String(length=100), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('transcription', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('indexing_status', sa.String(length=50), nullable=False),
    sa.Column('vector_status', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('knowledge_base_files')
