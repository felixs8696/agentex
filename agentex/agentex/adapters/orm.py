from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

BaseORM = declarative_base()


class AgentORM(BaseORM):
    __tablename__ = 'agents'
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
