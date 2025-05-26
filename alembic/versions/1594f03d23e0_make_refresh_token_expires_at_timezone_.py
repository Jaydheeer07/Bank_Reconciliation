"""make refresh token expires_at timezone aware

Revision ID: 1594f03d23e0
Revises: 9e13867c2042
Create Date: 2025-02-12 00:06:11.215124

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1594f03d23e0"
down_revision: Union[str, None] = "9e13867c2042"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Modify the expires_at column to be timezone-aware
    op.alter_column(
        "refresh_tokens",
        "expires_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    # Revert the expires_at column to be naive (timezone-unaware)
    op.alter_column(
        "refresh_tokens",
        "expires_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        nullable=False,
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
    )
