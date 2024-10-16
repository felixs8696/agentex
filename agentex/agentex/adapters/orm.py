from datetime import datetime, UTC, timezone

from sqlalchemy import DateTime, Column, String, ForeignKey, Table, Enum as SQLAlchemyEnum, Text, UniqueConstraint, \
    Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from agentex.domain.entities.agents import PackagingMethod, AgentStatus
from agentex.utils.ids import orm_id

BaseORM = declarative_base()


class AgentORM(BaseORM):
    __tablename__ = 'agents'
    id = Column(String, primary_key=True, default=orm_id)  # Using UUIDs for IDs
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    version = Column(String, nullable=False, index=True)
    model = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)
    action_service_port = Column(Integer, nullable=False)
    packaging_method = Column(SQLAlchemyEnum(PackagingMethod), nullable=False)
    actions = Column(JSONB, nullable=True)
    docker_image = Column(String, nullable=True)
    status = Column(SQLAlchemyEnum(AgentStatus), nullable=False)
    status_reason = Column(Text, nullable=True)
    build_job_name = Column(String, nullable=True, index=True)
    build_job_namespace = Column(String, default="default", nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_agent_name_version'),  # Unique constraint on name and version
    )


class TaskORM(BaseORM):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True, default=orm_id)  # Using UUIDs for IDs
    agent_id = Column(String, ForeignKey('agents.id'), nullable=False)
    prompt = Column(String, nullable=False)
    agent = relationship("AgentORM")
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
