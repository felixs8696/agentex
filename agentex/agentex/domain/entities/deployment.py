from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List

from pydantic import Field

from agentex.utils.model_utils import BaseModel


class DeploymentStatus(str, Enum):
    READY = "Ready"
    UNAVAILABLE = "Unavailable"
    UNKNOWN = "Unknown"


class DeploymentCondition(BaseModel):
    last_transition_time: datetime = Field(
        ...,
        description="Last time the condition transitioned from one status to another.",
    )
    last_update_time: datetime = Field(
        ...,
        description="The last time this condition was updated.	",
    )
    message: str = Field(
        ...,
        description="Human readable message indicating details about last transition.",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for the condition's last transition.",
    )
    status: str = Field(
        ...,
        description="Status of the condition, one of True, False, Unknown.",
    )
    type: str = Field(
        ...,
        description="Type of deployment condition, Complete or Failed.	",
    )


class Deployment(BaseModel):
    name: str = Field(
        ...,
        description="Name of the deployment, must be unique.",
    )
    namespace: Optional[str] = Field(
        default="default",
        description="Namespace that the deployment is running in.",
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None,
        description="Metadata for the deployment.",
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="CreationTimestamp is a timestamp representing the server time when this object was created. "
                    "It is not guaranteed to be set in happens-before order across separate operations. Clients may "
                    "not set this value. It is represented in RFC3339 form and is in UTC. Populated by the system. "
                    "Read-only. Null for lists. ",
    )
    status: DeploymentStatus
    conditions: List[DeploymentCondition] = Field(
        default_factory=list,
        description="List of states that the deployment has transitioned through.",
    )
