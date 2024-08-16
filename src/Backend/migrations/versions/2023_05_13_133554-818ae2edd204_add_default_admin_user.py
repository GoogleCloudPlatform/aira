"""add default admin user

Revision ID: 818ae2edd204
Revises: 23190f5d61ae
Create Date: 2023-05-13 13:35:54.531789+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "818ae2edd204"
down_revision = "23190f5d61ae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO 
            users (id, external_id, customer_id, type, group_id, role_id, name, email_address, password, last_login, created_at, updated_at) 
        SELECT uuid_generate_v4(), null, null, 'PASSWORD', null, roles.id, 'Admin', 'admin@example.com', '$2b$12$T8qK2VOaETPE1tZ0YhQnOez/bi3/KIHhqRPto2qC6tteG/5dZBW7i', null, now(), now() from roles where name = 'admin';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM users
        WHERE users.email_address = 'admin@example.com';
        """
    )
