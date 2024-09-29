from pydantic import Field

from agentex.utils.model_utils import BaseModel


class Task(BaseModel):
    id: str = Field(
        ...,
        title="Unique Task ID",
    )
    prompt: str = Field(
        ...,
        title="The user's text prompt for the task",
    )
