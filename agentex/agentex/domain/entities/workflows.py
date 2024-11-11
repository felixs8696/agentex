from datetime import timedelta
from typing import Optional

from pydantic import Field

from agentex.utils.model_utils import BaseModel


class WorkflowState(BaseModel):
    status: str
    is_terminal: bool
    reason: Optional[str] = None


class RetryPolicy(BaseModel):
    initial_interval: timedelta = Field(
        timedelta(seconds=1),
        description="Backoff interval for the first retry. Default 1s.",
    )
    backoff_coefficient: float = Field(
        2.0,
        description="Coefficient to multiply previous backoff interval by to get new interval. Default 2.0.",
    )
    maximum_interval: Optional[timedelta] = Field(
        None,
        description="Maximum backoff interval between retries. Default 100x :py:attr:`initial_interval`.",
    )
    maximum_attempts: int = Field(
        0,
        description="Maximum number of attempts. If 0, the default, there is no maximum.",
    )


