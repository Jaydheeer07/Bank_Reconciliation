"""add_refresh_tokens_and_blacklisted_tokens_tables

Revision ID: 213a2025fbc9
Revises: d8451148daa7
Create Date: 2024-12-18 07:10:18.690700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '213a2025fbc9'
down_revision: Union[str, None] = 'd8451148daa7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), default=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'])

    # Create blacklisted_tokens table
    op.create_table(
        'blacklisted_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('blacklisted_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index('ix_blacklisted_tokens_token', 'blacklisted_tokens', ['token'])


def downgrade() -> None:
    op.drop_index('ix_blacklisted_tokens_token')
    op.drop_table('blacklisted_tokens')
    op.drop_index('ix_refresh_tokens_token')
    op.drop_table('refresh_tokens')
