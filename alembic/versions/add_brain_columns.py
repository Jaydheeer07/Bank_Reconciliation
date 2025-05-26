"""add brain columns to users table

Revision ID: 4a9b2025fbc9
Revises: 213a2025fbc9
Create Date: 2025-01-09 10:24:36.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4a9b2025fbc9'
down_revision: Union[str, None] = '213a2025fbc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('brain_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('brain_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'brain_name')
    op.drop_column('users', 'brain_id')
