"""add tenant_shortcode to draft reconciliation

Revision ID: 935hgjrf532d
Revises: 935hgjrf532c
Create Date: 2025-01-30 09:02:10.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '935hgjrf532d'
down_revision = '935hgjrf532c'
branch_labels = None
depends_on = None


def upgrade():
    # Add tenant_shortcode column
    op.add_column('draft_reconciliation_entries',
                  sa.Column('tenant_shortcode', sa.String(), nullable=False,
                           server_default='default'))  # Providing a default value for existing rows
    
    # After all existing rows have been migrated, we can remove the server_default
    op.alter_column('draft_reconciliation_entries', 'tenant_shortcode',
                    existing_type=sa.String(),
                    server_default=None)


def downgrade():
    # Remove the tenant_shortcode column
    op.drop_column('draft_reconciliation_entries', 'tenant_shortcode')
