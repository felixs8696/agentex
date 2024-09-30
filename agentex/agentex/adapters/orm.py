from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

BaseORM = declarative_base()


class AgentORM(BaseORM):
    __tablename__ = 'agents'
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)


class TaskORM(BaseORM):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey('agents.id'), nullable=False)
    prompt = Column(String, nullable=False)
