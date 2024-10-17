from pydantic import Field

from agentex.domain.entities.agent_state import AgentState
from agentex.domain.entities.tasks import Task
from agentex.domain.entities.workflows import WorkflowState
from agentex.utils.model_utils import BaseModel


class CreateTaskRequest(BaseModel):
    agent_name: str = Field(
        ...,
        title="The unique name of the agent to use to run the task",
    )
    agent_version: str = Field(
        ...,
        title="The version of the agent to use to run the task.",
    )
    prompt: str = Field(
        ...,
        title="The user's text prompt for the task",
    )


class CreateTaskResponse(Task):
    pass


class GetTaskResponse(Task, AgentState):
    state: WorkflowState = Field(
        ...,
        title="The current state of the task",
    )
