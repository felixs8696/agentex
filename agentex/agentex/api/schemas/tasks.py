from pydantic import Field

from agentex.utils.model_utils import BaseModel


class TaskRequest(BaseModel):
    agent: str = Field(
        ...,
        title="The unique name of the agent to use to run the task",
    )
    prompt: str = Field(
        ...,
        title="The user's text prompt for the task",
    )


class TaskResponse(BaseModel):
    content: str = Field(
        ...,
        title="The response content from the agent",
    )
