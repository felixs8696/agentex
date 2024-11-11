from abc import ABC, abstractmethod
from datetime import timedelta
from enum import Enum
from typing import Union, Callable

from agentex.domain.entities.workflows import WorkflowState, RetryPolicy
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class DuplicateWorkflowPolicy(str, Enum):
    ALLOW_DUPLICATE = "ALLOW_DUPLICATE"
    ALLOW_DUPLICATE_FAILED_ONLY = "ALLOW_DUPLICATE_FAILED_ONLY"
    REJECT_DUPLICATE = "REJECT_DUPLICATE"
    TERMINATE_IF_RUNNING = "TERMINATE_IF_RUNNING"


class AsyncRuntime(ABC):

    @abstractmethod
    async def start_workflow(
        self,
        *args,
        duplicate_policy: DuplicateWorkflowPolicy,
        retry_policy: RetryPolicy,
        task_timeout: timedelta,
        execution_timeout: timedelta,
        **kwargs,
    ) -> str:
        pass

    @abstractmethod
    async def send_signal(
        self,
        workflow_id: str,
        signal: Union[str, Callable],
        payload: Union[dict, list, str, int, float, bool, BaseModel]
    ) -> None:
        pass

    @abstractmethod
    async def get_workflow_status(self, workflow_id: str) -> WorkflowState:
        pass

    @abstractmethod
    async def terminate_workflow(self, workflow_id: str) -> None:
        pass
