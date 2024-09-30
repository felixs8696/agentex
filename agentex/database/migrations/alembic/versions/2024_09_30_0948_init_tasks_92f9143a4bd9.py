"""init_tasks

Revision ID: 92f9143a4bd9
Revises: 63452efd5718
Create Date: 2024-09-30 09:48:48.377003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92f9143a4bd9'
down_revision: Union[str, None] = '63452efd5718'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tasks',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('agent_id', sa.String(), nullable=False),
    sa.Column('prompt', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tasks')
    # ### end Alembic commands ###