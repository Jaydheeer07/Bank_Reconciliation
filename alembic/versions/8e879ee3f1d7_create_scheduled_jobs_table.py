"""create scheduled jobs table

Revision ID: 8e879ee3f1d7
Revises: d6f2814aaf75
Create Date: 2025-02-21 05:54:18.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e879ee3f1d7'
down_revision = 'd6f2814aaf75'  # Point to current head
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'scheduled_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('brain_id', sa.String(36), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Add indexes
    op.create_index('ix_scheduled_jobs_user_id', 'scheduled_jobs', ['user_id'])
    op.create_index('ix_scheduled_jobs_tenant_id', 'scheduled_jobs', ['tenant_id'])
    op.create_index('ix_scheduled_jobs_job_type', 'scheduled_jobs', ['job_type'])
    op.create_index('ix_scheduled_jobs_is_active', 'scheduled_jobs', ['is_active'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_scheduled_jobs_is_active', table_name='scheduled_jobs')
    op.drop_index('ix_scheduled_jobs_job_type', table_name='scheduled_jobs')
    op.drop_index('ix_scheduled_jobs_tenant_id', table_name='scheduled_jobs')
    op.drop_index('ix_scheduled_jobs_user_id', table_name='scheduled_jobs')
    
    # Then drop the table
    op.drop_table('scheduled_jobs')
