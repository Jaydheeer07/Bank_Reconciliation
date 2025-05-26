"""add xero tokens table

Revision ID: 410fffe15bfa
Revises: 935hgjrf532e
Create Date: 2024-02-07 13:57:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '410fffe15bfa'
down_revision: Union[str, None] = '935hgjrf532e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'xero_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_data', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_xero_tokens_id'), 'xero_tokens', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_xero_tokens_id'), table_name='xero_tokens')
    op.drop_table('xero_tokens')
