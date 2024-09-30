from pydantic import Field

from agentex.domain.entities.tasks import Task
from agentex.utils.model_utils import BaseModel


class CreateTaskRequest(BaseModel):
    agent: str = Field(
        ...,
        title="The unique name of the agent to use to run the task",
    )
    prompt: str = Field(
        ...,
        title="The user's text prompt for the task",
    )


class CreateTaskResponse(Task):
    pass
