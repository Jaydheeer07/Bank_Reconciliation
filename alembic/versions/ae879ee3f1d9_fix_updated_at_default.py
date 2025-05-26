"""fix updated_at default

Revision ID: ae879ee3f1d9
Revises: 9e879ee3f1d8
Create Date: 2025-02-21 06:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = 'ae879ee3f1d9'
down_revision = '9e879ee3f1d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Set default value for updated_at column
    op.alter_column('scheduled_jobs', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.text('CURRENT_TIMESTAMP'),
                    existing_nullable=False)


def downgrade() -> None:
    # Remove default value from updated_at column
    op.alter_column('scheduled_jobs', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=False)
