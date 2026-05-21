"""migrate_groups_to_relational

Revision ID: 3ffbcd242dd2
Revises: 55b87d683498
Create Date: 2026-05-21 13:47:55.293446+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3ffbcd242dd2'
down_revision = '55b87d683498'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('groups', sa.Column('series_id', sa.UUID(), nullable=True))
    op.add_column('groups', sa.Column('shift_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_groups_series_id'), 'groups', ['series_id'], unique=False)
    op.create_index(op.f('ix_groups_shift_id'), 'groups', ['shift_id'], unique=False)
    op.create_foreign_key(None, 'groups', 'work_shifts', ['shift_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'groups', 'series', ['series_id'], ['id'], ondelete='CASCADE')

    # Data Migration (Map Enums to relational UUIDs with fallback)
    op.execute("""
        UPDATE groups g
        SET series_id = s.id
        FROM series s
        WHERE s.name = g.grade::text 
           OR (g.grade::text = 'FIRST_FUND' AND s.name = '1º Ano')
           OR (g.grade::text = 'SECOND_FUND' AND s.name = '2º Ano')
           OR (g.grade::text = 'THIRD_FUND' AND s.name = '3º Ano')
           OR (g.grade::text = 'FOURTH_FUND' AND s.name = '4º Ano')
           OR (g.grade::text = 'FIFTH_FUND' AND s.name = '5º Ano')
           OR (g.grade::text = 'SIXTH_FUND' AND s.name = '6º Ano')
           OR (g.grade::text = 'SEVENTH_FUND' AND s.name = '7º Ano')
           OR (g.grade::text = 'EIGHTH_FUND' AND s.name = '8º Ano')
           OR (g.grade::text = 'NINETH_FUND' AND s.name = '9º Ano')
           OR (g.grade::text = 'FIRST_HS' AND s.name = '1ª Série')
           OR (g.grade::text = 'SECOND_HS' AND s.name = '2ª Série')
           OR (g.grade::text = 'THIRD_HS' AND s.name = '3ª Série')
    """)
    op.execute("""
        UPDATE groups g
        SET shift_id = w.id
        FROM work_shifts w
        WHERE w.code = g.shift::text
           OR w.code = UPPER(g.shift::text)
    """)

    # Enforce NOT NULL constraint
    op.alter_column('groups', 'series_id', nullable=False)
    op.alter_column('groups', 'shift_id', nullable=False)

    op.drop_column('groups', 'shift')
    op.drop_column('groups', 'grade')
    # ### end Alembic commands ###


def downgrade() -> None:
    op.add_column('groups', sa.Column('grade', postgresql.ENUM('FIRST_FUND', 'SECOND_FUND', 'THIRD_FUND', 'FOURTH_FUND', 'FIFTH_FUND', 'SIXTH_FUND', 'SEVENTH_FUND', 'EIGHTH_FUND', 'NINETH_FUND', 'FIRST_HS', 'SECOND_HS', 'THIRD_HS', name='grades'), autoincrement=False, nullable=True))
    op.add_column('groups', sa.Column('shift', postgresql.ENUM('MORNING', 'AFTERNOON', 'EVENING', 'ALLDAY', name='shifts'), autoincrement=False, nullable=True))
    
    # Populate old columns from relational data
    op.execute("""
        UPDATE groups
        SET grade = series.name::grades
        FROM series
        WHERE series.id = groups.series_id
    """)
    op.execute("""
        UPDATE groups
        SET shift = work_shifts.name::shifts
        FROM work_shifts
        WHERE work_shifts.id = groups.shift_id
    """)

    # Enforce NOT NULL
    op.alter_column('groups', 'grade', nullable=False)
    op.alter_column('groups', 'shift', nullable=False)

    op.drop_constraint(None, 'groups', type_='foreignkey')
    op.drop_constraint(None, 'groups', type_='foreignkey')
    op.drop_index(op.f('ix_groups_shift_id'), table_name='groups')
    op.drop_index(op.f('ix_groups_series_id'), table_name='groups')
    op.drop_column('groups', 'shift_id')
    op.drop_column('groups', 'series_id')
    # ### end Alembic commands ###
