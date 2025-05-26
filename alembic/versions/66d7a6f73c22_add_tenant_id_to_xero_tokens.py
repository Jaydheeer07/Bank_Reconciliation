"""add tenant_id to xero_tokens

Revision ID: 66d7a6f73c22
Revises: 410fffe15bfa
Create Date: 2024-02-10 09:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66d7a6f73c22'
down_revision: Union[str, None] = '410fffe15bfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('xero_tokens', sa.Column('tenant_id', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('xero_tokens', 'tenant_id')
