from typing import Optional

from agentex.domain.entities.agents import Agent, AgentStatus
from agentex.utils.model_utils import BaseModel


class BuildHostedActionsParams(BaseModel):
    name: str
    version: str
    zip_file_path: str


class CreateHostedActionsDeploymentParams(BaseModel):
    name: str
    image: str
    action_service_port: int
    replicas: int = 1


class CreateHostedActionsServiceParams(BaseModel):
    name: str
    action_service_port: int


class CallHostedActionsServiceParams(BaseModel):
    name: str
    port: int
    path: str
    method: str = "GET"
    payload: Optional[dict] = None


class UpdateAgentStatusParams(BaseModel):
    agent: Agent
    status: AgentStatus
    reason: Optional[str] = None
