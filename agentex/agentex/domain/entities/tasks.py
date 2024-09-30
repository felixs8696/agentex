from pydantic import Field

from agentex.utils.model_utils import BaseModel


class Task(BaseModel):
    id: str = Field(
        ...,
        title="Unique Task ID",
    )
    agent_id: str = Field(
        ...,
        title="The ID of the agent that is responsible for this task",
    )
    prompt: str = Field(
        ...,
        title="The user's text prompt for the task",
    )
