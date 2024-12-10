"""Add login attempt tracking columns

Revision ID: cd96a66303a5
Revises: fd752f470000
Create Date: 2024-12-02 13:38:18.719377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd96a66303a5'
down_revision: Union[str, None] = 'fd752f470000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('last_failed_login', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'last_failed_login')
    op.drop_column('users', 'failed_login_attempts')
    # ### end Alembic commands ###
