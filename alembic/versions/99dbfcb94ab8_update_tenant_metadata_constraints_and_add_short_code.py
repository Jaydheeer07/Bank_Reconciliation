"""update tenant metadata constraints and add short code

Revision ID: 99dbfcb94ab8
Revises: ff0405bea936
Create Date: 2025-01-22 11:49:02.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99dbfcb94ab8'
down_revision = 'ff0405bea936'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing unique constraints
    op.drop_constraint('tenant_metadata_tenant_id_key', 'tenant_metadata', type_='unique')
    op.drop_constraint('tenant_metadata_table_name_key', 'tenant_metadata', type_='unique')
    
    # Add tenant_short_code column
    op.add_column('tenant_metadata', sa.Column('tenant_short_code', sa.String(), nullable=True))
    
    # Add composite unique constraint for user_id and tenant_id
    op.create_unique_constraint('uq_user_tenant', 'tenant_metadata', ['user_id', 'tenant_id'])


def downgrade() -> None:
    # Drop composite unique constraint
    op.drop_constraint('uq_user_tenant', 'tenant_metadata', type_='unique')
    
    # Drop tenant_short_code column
    op.drop_column('tenant_metadata', 'tenant_short_code')
    
    # Restore original unique constraints
    op.create_unique_constraint('tenant_metadata_tenant_id_key', 'tenant_metadata', ['tenant_id'])
    op.create_unique_constraint('tenant_metadata_table_name_key', 'tenant_metadata', ['table_name'])
