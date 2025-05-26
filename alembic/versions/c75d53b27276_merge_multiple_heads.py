"""merge_multiple_heads

Revision ID: c75d53b27276
Revises: 0991b5046f10, 1594f03d23e0
Create Date: 2025-02-12 02:43:46.812276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c75d53b27276'
down_revision: Union[str, None] = ('0991b5046f10', '1594f03d23e0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
