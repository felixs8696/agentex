from pydantic import Field

from agentex.utils.model_utils import BaseModel


class CreateAgentRequest(BaseModel):
    name: str = Field(
        ...,
        title="The unique name of the agent",
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
