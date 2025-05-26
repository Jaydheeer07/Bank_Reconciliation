"""add_tenant_id_to_statements

Revision ID: 119b9dd99c10
Revises: ae879ee3f1d9
Create Date: 2025-03-04 09:57:41.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '119b9dd99c10'
down_revision = 'ae879ee3f1d9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First check if statements table exists, if not create it
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if not inspector.has_table('statements'):
        op.create_table('statements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('brain_id', sa.String(length=255), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('client_name', sa.String(length=255), nullable=True),
            sa.Column('account_name', sa.String(length=255), nullable=True),
            sa.Column('account_number', sa.String(length=255), nullable=True),
            sa.Column('transaction_date', sa.Date(), nullable=True),
            sa.Column('particulars', sa.String(length=255), nullable=True),
            sa.Column('code', sa.String(length=255), nullable=True),
            sa.Column('reference', sa.String(length=255), nullable=True),
            sa.Column('amount', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Now add the tenant_id column
    op.add_column('statements', sa.Column('tenant_id', sa.String(length=255), nullable=True))
    # Add index for better query performance
    op.create_index(op.f('ix_statements_tenant_id'), 'statements', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_statements_tenant_id'), table_name='statements')
    op.drop_column('statements', 'tenant_id')
