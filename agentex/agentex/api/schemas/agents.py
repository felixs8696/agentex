from typing import Optional, List

from pydantic import Field

from agentex.domain.entities.actions import Action
from agentex.domain.entities.agents import AgentStatus
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class CreateAgentRequest(BaseModel):
    name: str = Field(
        ...,
        description="The unique name of the agent."
    )
    description: str = Field(
        ...,
        description="A brief description of the agent."
    )
    version: str = Field(
        ...,
        description="The version of the agent."
    )
    action_service_port: int = Field(
        ...,
        description="The port on which the service will run inside the container. This is the port that the "
                    "command is pointing at in your Dockerfile. It should be specified in the action manifest."
    )


class AgentModel(BaseModel):
    id: str = Field(
        ...,
        description="The unique identifier of the agent."
    )
    name: str = Field(
        ...,
        description="The unique name of the agent."
    )
    description: str = Field(
        ...,
        description="The description of the action."
    )
    version: str = Field(
        ...,
        description="The version of the action."
    )
    model: Optional[str] = Field(
        None,
        description="The LLM model powering the agent."
    )
    instructions: Optional[str] = Field(
        None,
        description="The instructions for the agent."
    )
    actions: Optional[List[Action]] = Field(
        default=None,
        description="The actions that the agent can perform."
    )
    status: AgentStatus = Field(
        AgentStatus.UNKNOWN,
        description="The status of the action, indicating if it's building, ready, failed, etc."
    )
    status_reason: Optional[str] = Field(
        None,
        description="The reason for the status of the action."
    )
