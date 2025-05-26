"""add_user_id_to_xero_tokens

Revision ID: 9e13867c2042
Revises: 66d7a6f73c22
Create Date: 2025-02-11 10:54:38.812075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e13867c2042'
down_revision: Union[str, None] = '66d7a6f73c22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id column (nullable)
    op.add_column('xero_tokens', sa.Column('user_id', sa.UUID(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_xero_tokens_user_id',
        'xero_tokens',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Set user_id to non-nullable
    op.alter_column('xero_tokens', 'user_id',
                    existing_type=sa.UUID(),
                    nullable=False)


def downgrade() -> None:
    op.drop_constraint('fk_xero_tokens_user_id', 'xero_tokens', type_='foreignkey')
    op.drop_column('xero_tokens', 'user_id')
