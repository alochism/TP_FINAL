"""create audit_logs

Revision ID: 5c1a9e2f7d40
Revises: 3b8d1c4e9a72
Create Date: 2026-11-20 16:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5c1a9e2f7d40'
down_revision: Union[str, Sequence[str], None] = '3b8d1c4e9a72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('actions', sa.JSON(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('reply', sa.Text(), nullable=False),
        sa.Column('llm_error', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')
