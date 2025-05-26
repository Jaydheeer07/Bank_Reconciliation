"""Create draft_reconciliation_entries table

Revision ID: 935hgjrf532c
Revises: 99dbfcb94ab8
Create Date: 2025-01-27 13:27:54.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '935hgjrf532c'
down_revision: Union[str, None] = '99dbfcb94ab8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('draft_reconciliation_entries',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('statement_client_name', sa.String(), nullable=True),
        sa.Column('account_name', sa.String(), nullable=True),
        sa.Column('transaction_date', sa.DateTime(), nullable=True),
        sa.Column('payee', sa.String(), nullable=True),
        sa.Column('particulars', sa.String(), nullable=True),
        sa.Column('statement_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('file_name', sa.String(), nullable=True),
        sa.Column('invoice_client_name', sa.String(), nullable=True),
        sa.Column('details', sa.String(), nullable=True),
        sa.Column('invoice_date', sa.DateTime(), nullable=True),
        sa.Column('invoice_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('draft_reconciliation_entries')