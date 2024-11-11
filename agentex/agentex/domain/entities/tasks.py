from typing import Optional

from pydantic import Field

from agentex.adapters.async_runtime.adapter_temporal import TaskStatus
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
    status: Optional[TaskStatus] = Field(
        None,
        title="The current status of the task",
    )
    status_reason: Optional[str] = Field(
        None,
        title="The reason for the current task status",
    )


class AgentTaskWorkflowParams(BaseModel):
    task: Task
    require_approval: Optional[bool] = False
