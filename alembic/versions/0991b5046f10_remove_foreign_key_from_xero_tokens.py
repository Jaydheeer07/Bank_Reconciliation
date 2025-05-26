"""remove_foreign_key_from_xero_tokens

Revision ID: 0991b5046f10
Revises: 9e13867c2042
Create Date: 2025-02-12 02:42:27.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0991b5046f10'
down_revision: Union[str, None] = '9e13867c2042'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove the foreign key constraint
    op.drop_constraint('fk_xero_tokens_user_id', 'xero_tokens', type_='foreignkey')


def downgrade() -> None:
    # Re-add the foreign key constraint if needed to rollback
    op.create_foreign_key(
        'fk_xero_tokens_user_id',
        'xero_tokens',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )
