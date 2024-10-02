from sqlalchemy import Column, String, ForeignKey, Table, Enum as SQLAlchemyEnum, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from agentex.domain.entities.actions import PackagingMethod
from agentex.utils.ids import orm_id

BaseORM = declarative_base()

agent_action_association = Table(
    'agent_action',
    BaseORM.metadata,
    Column('agent_id', String, ForeignKey('agents.id'), primary_key=True),
    Column('action_id', String, ForeignKey('actions.id'), primary_key=True)
)


class AgentORM(BaseORM):
    __tablename__ = 'agents'
    id = Column(String, primary_key=True, default=orm_id)  # Using UUIDs for IDs
    name = Column(String, unique=True, nullable=False, index=True)
    actions = relationship('ActionORM', secondary=agent_action_association, back_populates='agents')


class TaskORM(BaseORM):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True, default=orm_id)  # Using UUIDs for IDs
    agent_id = Column(String, ForeignKey('agents.id'), nullable=False)
    prompt = Column(String, nullable=False)
    agent = relationship("AgentORM")


class ActionORM(BaseORM):
    __tablename__ = 'actions'
    id = Column(String, primary_key=True, default=orm_id)  # Using UUIDs for IDs
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    version = Column(String, nullable=False, index=True)
    packaging_method = Column(SQLAlchemyEnum(PackagingMethod), nullable=False)
    parameters = Column(JSONB, nullable=False)  # JSON field for parameter schema
    test_payload = Column(JSONB, nullable=False)
    docker_image = Column(String, nullable=True)
    agents = relationship('AgentORM', secondary=agent_action_association, back_populates='actions')

    __table_args__ = (
        UniqueConstraint('version', name='uq_version'),  # Add unique constraint on version
    )
