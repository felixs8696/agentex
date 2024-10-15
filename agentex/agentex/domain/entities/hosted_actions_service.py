from agentex.domain.entities.agent_spec import AgentSpec
from agentex.utils.model_utils import BaseModel


class HostedActionsService(BaseModel):
    service_name: str
    service_namespace: str
    service_port: int
    deployment_name: str
    deployment_namespace: str
    agent_spec: AgentSpec
