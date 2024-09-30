from datetime import timedelta
from typing import Any

from agentex.adapters.async_runtime.port import AsyncRuntime
from agentex.config.dependencies import DTemporalClient
from agentex.domain.entities.workflows import WorkflowState, RetryPolicy
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class TemporalGateway(AsyncRuntime):

    def __init__(self, temporal_client: DTemporalClient):
        self.client = temporal_client

    async def start_workflow(
        self,
        *args,
        retry_policy=RetryPolicy(maximum_attempts=3),
        task_timeout=timedelta(seconds=10),
        execution_timeout=timedelta(seconds=86400),
        **kwargs,
    ) -> Any:
        return await self.client.start_workflow(
            retry_policy=retry_policy,
            task_timeout=task_timeout,
            execution_timeout=execution_timeout,
            *args,
            **kwargs,
        )

    async def get_workflow_status(self, workflow_id: str) -> WorkflowState:
        handle = self.client.get_workflow_handle(workflow_id=workflow_id)
        description = await handle.describe()
        return WorkflowState(
            status=description.state,
            is_terminal=description.is_done,
            reason=description.close_status
        )

    async def terminate_workflow(self, workflow_id: str) -> None:
        return await self.client.get_workflow_handle(workflow_id).terminate()
