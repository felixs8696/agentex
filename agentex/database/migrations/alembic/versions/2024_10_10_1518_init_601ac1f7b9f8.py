"""init

Revision ID: 601ac1f7b9f8
Revises: 
Create Date: 2024-10-10 15:18:35.443527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '601ac1f7b9f8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('actions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('version', sa.String(), nullable=False),
    sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('test_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'version', name='uq_action_name_version')
    )
    op.create_index(op.f('ix_actions_name'), 'actions', ['name'], unique=False)
    op.create_index(op.f('ix_actions_version'), 'actions', ['version'], unique=False)
    op.create_table('agents',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('version', sa.String(), nullable=False),
    sa.Column('model', sa.String(), nullable=True),
    sa.Column('instructions', sa.Text(), nullable=True),
    sa.Column('action_service_port', sa.Integer(), nullable=False),
    sa.Column('packaging_method', sa.Enum('DOCKER', name='packagingmethod'), nullable=False),
    sa.Column('docker_image', sa.String(), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'BUILDING', 'IDLE', 'ACTIVE', 'READY', 'FAILED', 'UNKNOWN', name='agentstatus'), nullable=False),
    sa.Column('status_reason', sa.Text(), nullable=True),
    sa.Column('build_job_name', sa.String(), nullable=True),
    sa.Column('build_job_namespace', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'version', name='uq_agent_name_version')
    )
    op.create_index(op.f('ix_agents_build_job_name'), 'agents', ['build_job_name'], unique=False)
    op.create_index(op.f('ix_agents_name'), 'agents', ['name'], unique=False)
    op.create_index(op.f('ix_agents_version'), 'agents', ['version'], unique=False)
    op.create_table('agent_action',
    sa.Column('agent_id', sa.String(), nullable=False),
    sa.Column('action_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['action_id'], ['actions.id'], ),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
    sa.PrimaryKeyConstraint('agent_id', 'action_id')
    )
    op.create_table('tasks',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('agent_id', sa.String(), nullable=False),
    sa.Column('prompt', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tasks')
    op.drop_table('agent_action')
    op.drop_index(op.f('ix_agents_version'), table_name='agents')
    op.drop_index(op.f('ix_agents_name'), table_name='agents')
    op.drop_index(op.f('ix_agents_build_job_name'), table_name='agents')
    op.drop_table('agents')
    op.drop_index(op.f('ix_actions_version'), table_name='actions')
    op.drop_index(op.f('ix_actions_name'), table_name='actions')
    op.drop_table('actions')
    # ### end Alembic commands ###