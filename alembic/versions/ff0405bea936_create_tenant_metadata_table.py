"""create tenant metadata table

Revision ID: ff0405bea936
Revises: 4a9b2025fbc9
Create Date: 2025-01-21 09:10:04.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ff0405bea936'
down_revision = '4a9b2025fbc9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tenant_metadata table
    op.create_table(
        'tenant_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('tenant_name', sa.String(), nullable=False),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id'),
        sa.UniqueConstraint('table_name')
    )
    
    # Create an index on tenant_id for faster lookups
    op.create_index(op.f('ix_tenant_metadata_tenant_id'), 'tenant_metadata', ['tenant_id'], unique=True)
    
    # Create an index on user_id for faster joins
    op.create_index(op.f('ix_tenant_metadata_user_id'), 'tenant_metadata', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f('ix_tenant_metadata_user_id'), table_name='tenant_metadata')
    op.drop_index(op.f('ix_tenant_metadata_tenant_id'), table_name='tenant_metadata')
    
    # Drop the table
    op.drop_table('tenant_metadata')
