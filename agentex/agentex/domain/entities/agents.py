from enum import Enum
from typing import Optional, List

from pydantic import Field

from agentex.domain.entities.actions import Action
from agentex.utils.model_utils import BaseModel


class PackagingMethod(str, Enum):
    DOCKER = "docker"


class AgentStatus(str, Enum):
    PENDING = "Pending"
    BUILDING = "Building"
    READY = "Ready"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class Agent(BaseModel):
    id: str = Field(
        ...,
        description="The unique identifier of the agent."
    )
    packaging_method: PackagingMethod = Field(
        PackagingMethod.DOCKER,
        description="The method used to bundle the action code."
    )
    docker_image: Optional[str] = Field(
        None,
        description="The URI of the image associated with the action. Only set if the packaging method is `docker`."
    )
    name: str = Field(
        ...,
        description="The unique name of the agent."
    )
    description: str = Field(
        ...,
        description="The description of the action."
    )
    status: AgentStatus = Field(
        AgentStatus.UNKNOWN,
        description="The status of the action, indicating if it's building, ready, failed, etc."
    )
    status_reason: Optional[str] = Field(
        None,
        description="The reason for the status of the action."
    )
    build_job_name: Optional[str] = Field(
        None,
        description="The name of the build job that is building the action."
    )
    build_job_namespace: Optional[str] = Field(
        "default",
        description="The namespace that the build job is running in."
    )
    workflow_name: str = Field(
        ...,
        description="The name of the workflow that defines the agent."
    )
    workflow_queue_name: str = Field(
        ...,
        description="The name of the queue to send tasks to."
    )
