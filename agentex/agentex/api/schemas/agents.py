from pydantic import Field

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


class CreateAgentResponse(BaseModel):
    id: str = Field(
        ...,
        description="The unique identifier of the agent."
    )
    name: str = Field(
        ...,
        description="The unique name of the agent."
    )
