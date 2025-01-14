"""descUpdate Usuario table

Revision ID: db5e32300e15
Revises: ff5c8faa4530
Create Date: 2025-01-12 17:15:43.145657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db5e32300e15'
down_revision: Union[str, None] = 'ff5c8faa4530'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('usuarios', sa.Column('email', sa.String(), nullable=False))
    op.create_unique_constraint(None, 'usuarios', ['email'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'usuarios', type_='unique')
    op.drop_column('usuarios', 'email')
    # ### end Alembic commands ###
