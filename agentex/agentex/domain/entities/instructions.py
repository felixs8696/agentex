from enum import Enum
from typing import Literal, Optional

from pydantic import Field

from agentex.utils.model_utils import BaseModel


class TaskModificationType(str, Enum):
    INSTRUCT = "instruct"
    APPROVE = "approve"
    CANCEL = "cancel"


class CancelTaskRequest(BaseModel):
    type: Literal[TaskModificationType.CANCEL] = Field(
        TaskModificationType.CANCEL,
        title="The type of instruction to send to the task",
    )


class ApproveTaskRequest(BaseModel):
    type: Literal[TaskModificationType.APPROVE] = Field(
        TaskModificationType.APPROVE,
        title="The type of instruction to send to the task",
    )


class InstructTaskRequest(BaseModel):
    type: Literal[TaskModificationType.INSTRUCT] = Field(
        TaskModificationType.INSTRUCT,
        title="The type of instruction to send to the task",
    )
    prompt: str = Field(
        ...,
        title="The user's text prompt for the task",
    )
