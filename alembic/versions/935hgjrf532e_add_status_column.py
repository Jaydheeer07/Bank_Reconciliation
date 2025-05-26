"""add status column to draft reconciliation

Revision ID: 935hgjrf532e
Revises: 935hgjrf532d
Create Date: 2025-02-03 10:48:37.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '935hgjrf532e'
down_revision = '935hgjrf532d'
branch_labels = None
depends_on = None


def upgrade():
    # Add status column
    op.add_column('draft_reconciliation_entries',
                  sa.Column('status', sa.String(), nullable=True))


def downgrade():
    # Remove the status column
    op.drop_column('draft_reconciliation_entries', 'status')
