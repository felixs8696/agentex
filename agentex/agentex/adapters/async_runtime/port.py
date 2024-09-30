from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any

from agentex.domain.entities.workflows import WorkflowState, RetryPolicy
from agentex.utils.logging import make_logger

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
    ) -> Any:
        pass

    @abstractmethod
    async def get_workflow_status(self, workflow_id: str) -> WorkflowState:
        pass

    @abstractmethod
    async def terminate_workflow(self, workflow_id: str) -> None:
        pass
