from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List

from pydantic import Field

from agentex.utils.model_utils import BaseModel


class JobStatus(str, Enum):
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    RUNNING = "Running"
    PENDING = "Pending"
    UNKNOWN = "Unknown"


class JobCondition(BaseModel):
    last_probe_time: datetime = Field(
        ...,
        description="Last time the condition was checked for status.",
    )
    last_transition_time: datetime = Field(
        ...,
        description="Last time the condition transitioned from one status to another.",
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
        description="Type of job condition, Complete or Failed.	",
    )


class Job(BaseModel):
    name: str = Field(
        ...,
        description="Name of the job, must be unique.",
    )
    namespace: Optional[str] = Field(
        default="default",
        description="Namespace that the job is running in.",
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None,
        description="Metadata for the job.",
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="CreationTimestamp is a timestamp representing the server time when this object was created. "
                    "It is not guaranteed to be set in happens-before order across separate operations. Clients may "
                    "not set this value. It is represented in RFC3339 form and is in UTC. Populated by the system. "
                    "Read-only. Null for lists. ",
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Start time of the job.",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Completion time of the job.",
    )
    status: JobStatus
    conditions: List[JobCondition] = Field(
        default_factory=list,
        description="List of states that the job has transitioned through.",
    )
