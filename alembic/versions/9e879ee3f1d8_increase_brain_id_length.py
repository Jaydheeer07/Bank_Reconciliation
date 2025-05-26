"""increase brain_id length

Revision ID: 9e879ee3f1d8
Revises: 8e879ee3f1d7
Create Date: 2025-02-21 06:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e879ee3f1d8'
down_revision = '8e879ee3f1d7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alter brain_id column to be varchar(100)
    op.alter_column('scheduled_jobs', 'brain_id',
                    existing_type=sa.String(36),
                    type_=sa.String(100),
                    existing_nullable=False)


def downgrade() -> None:
    # Revert brain_id column back to varchar(36)
    op.alter_column('scheduled_jobs', 'brain_id',
                    existing_type=sa.String(100),
                    type_=sa.String(36),
                    existing_nullable=False)
