from datetime import datetime, timezone

from sqlalchemy import DateTime, Column, String, ForeignKey, Enum as SQLAlchemyEnum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from agentex.adapters.async_runtime.adapter_temporal import TaskStatus
from agentex.domain.entities.agents import PackagingMethod, AgentStatus
from agentex.utils.ids import orm_id

BaseORM = declarative_base()


class AgentORM(BaseORM):
    __tablename__ = 'agents'
    id = Column(String, primary_key=True, default=orm_id)  # Using UUIDs for IDs
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    packaging_method = Column(SQLAlchemyEnum(PackagingMethod), nullable=False)
    docker_image = Column(String, nullable=True)
    status = Column(SQLAlchemyEnum(AgentStatus), nullable=False)
    status_reason = Column(Text, nullable=True)
    build_job_name = Column(String, nullable=True, index=True)
    build_job_namespace = Column(String, default="default", nullable=True)
    workflow_name = Column(String, nullable=False)
    workflow_queue_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))


class TaskORM(BaseORM):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True, default=orm_id)  # Using UUIDs for IDs
    agent_id = Column(String, ForeignKey('agents.id'), nullable=False)
    prompt = Column(String, nullable=False)
    agent = relationship("AgentORM")
    status = Column(SQLAlchemyEnum(TaskStatus), nullable=True)
    status_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
