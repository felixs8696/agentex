"""add_test_payload_to_action

Revision ID: c8b1f183c866
Revises: 445f4881318d
Create Date: 2024-10-02 16:31:11.299434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c8b1f183c866'
down_revision: Union[str, None] = '445f4881318d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('actions', sa.Column('test_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('actions', 'test_payload')
    # ### end Alembic commands ###
