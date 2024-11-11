from typing import Union, Annotated, Optional

from pydantic import Field

from agentex.domain.entities.agent_state import AgentState
from agentex.domain.entities.instructions import CancelTaskRequest, ApproveTaskRequest, \
    InstructTaskRequest
from agentex.domain.entities.tasks import Task
from agentex.utils.model_utils import BaseModel


class CreateTaskRequest(BaseModel):
    agent_name: str = Field(
        ...,
        title="The unique name of the agent to use to run the task",
    )
    prompt: str = Field(
        ...,
        title="The user's text prompt for the task",
    )
    require_approval: Optional[bool] = Field(
        False,
        title="Whether the task requires human approval in order to complete. "
              "If false, the task is left running until the human sends a finish",
    )


class TaskModel(Task, AgentState):
    pass


ModifyTaskRequest = Annotated[
    Union[ApproveTaskRequest, CancelTaskRequest, InstructTaskRequest],
    Field(discriminator="type")
]
