from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Union, Callable

from agentex.domain.entities.workflows import WorkflowState, RetryPolicy
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class AsyncRuntime(ABC):

    @abstractmethod
    async def start_workflow(
        self,
        *args,
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
