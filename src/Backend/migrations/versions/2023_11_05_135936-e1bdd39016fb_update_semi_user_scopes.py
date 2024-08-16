"""Update semi-user scopes

Revision ID: e1bdd39016fb
Revises: 11294e7878d6
Create Date: 2023-11-05 13:59:36.146017+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1bdd39016fb'
down_revision = '11294e7878d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE roles
            SET scopes = "scopes" || '["user.impersonate", "user.list", "group.list", "exam.list"]'
            WHERE name = 'professor';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE roles
            SET scopes = '["dashboard.viewer"]'
            WHERE name = 'professor';
        """
    )
    