"""Adjust roles

Revision ID: 4d6b893ece60
Revises: 2fa71d14d1f1
Create Date: 2023-06-22 21:16:37.451500+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4d6b893ece60"
down_revision = "2fa71d14d1f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE roles
        SET name = 'professor', scopes='["dashboard.viewer"]'
        WHERE name = 'semi-admin'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE roles
        SET name = 'semi-admin', scopes='["semi-admin"]'
        WHERE name = 'professor'
        """
    )
