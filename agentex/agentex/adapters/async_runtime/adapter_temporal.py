from datetime import timedelta
from enum import Enum
from typing import Annotated, Callable, Union

from fastapi import Depends
from temporalio.client import WorkflowExecutionStatus
from temporalio.common import WorkflowIDReusePolicy, RetryPolicy as TemporalRetryPolicy
from temporalio.service import RPCError, RPCStatusCode

from agentex.adapters.async_runtime.port import AsyncRuntime, DuplicateWorkflowPolicy
from agentex.config.dependencies import DTemporalClient
from agentex.domain.entities.workflows import WorkflowState, RetryPolicy
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class TaskStatus(str, Enum):
    CANCELED = "CANCELED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RUNNING = "RUNNING"
    TERMINATED = "TERMINATED"
    TIMED_OUT = "TIMED_OUT"


TEMPORAL_STATUS_TO_UPLOAD_STATUS_AND_REASON = {
    # TODO: Support canceled status
    WorkflowExecutionStatus.CANCELED: WorkflowState(
        status=TaskStatus.CANCELED,
        reason="Task canceled by the user.",
        is_terminal=True,
    ),
    WorkflowExecutionStatus.COMPLETED: WorkflowState(
        status=TaskStatus.COMPLETED,
        reason="Task completed successfully.",
        is_terminal=True,
    ),
    WorkflowExecutionStatus.FAILED: WorkflowState(
        status=TaskStatus.FAILED,
        reason="Task encountered terminal failure. "
        "Please contact support if retrying does not resolve the issue.",
        is_terminal=True,
    ),
    WorkflowExecutionStatus.RUNNING: WorkflowState(
        status=TaskStatus.RUNNING,
        reason="Task is running.",
        is_terminal=False,
    ),
    WorkflowExecutionStatus.TERMINATED: WorkflowState(
        status=TaskStatus.CANCELED,
        reason="Task canceled by the user.",
        is_terminal=True,
    ),
    WorkflowExecutionStatus.TIMED_OUT: WorkflowState(
        status=TaskStatus.FAILED,
        reason="Task timed out. Please contact support if retrying does not resolve the issue",
        is_terminal=True,
    ),
    WorkflowExecutionStatus.CONTINUED_AS_NEW: WorkflowState(
        status=TaskStatus.RUNNING,
        reason="Task is running.",
        is_terminal=False,
    ),
}

DUPLICATE_POLICY_TO_ID_REUSE_POLICY = {
    DuplicateWorkflowPolicy.ALLOW_DUPLICATE: WorkflowIDReusePolicy.ALLOW_DUPLICATE,
    DuplicateWorkflowPolicy.ALLOW_DUPLICATE_FAILED_ONLY: WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
    DuplicateWorkflowPolicy.REJECT_DUPLICATE: WorkflowIDReusePolicy.REJECT_DUPLICATE,
    DuplicateWorkflowPolicy.TERMINATE_IF_RUNNING: WorkflowIDReusePolicy.TERMINATE_IF_RUNNING,
}


class TemporalGateway(AsyncRuntime):

    def __init__(self, temporal_client: DTemporalClient):
        self.client = temporal_client

    async def start_workflow(
        self,
        *args,
        duplicate_policy: DuplicateWorkflowPolicy = DuplicateWorkflowPolicy.ALLOW_DUPLICATE,
        retry_policy=RetryPolicy(maximum_attempts=1),
        task_timeout=timedelta(seconds=10),
        execution_timeout=timedelta(seconds=86400),
        **kwargs,
    ) -> str:
        temporal_retry_policy = TemporalRetryPolicy(
            **retry_policy.dict(exclude_unset=True)
        )
        workflow_handle = await self.client.start_workflow(
            retry_policy=temporal_retry_policy,
            task_timeout=task_timeout,
            execution_timeout=execution_timeout,
            id_reuse_policy=DUPLICATE_POLICY_TO_ID_REUSE_POLICY[duplicate_policy],
            *args,
            **kwargs,
        )
        return workflow_handle.id

    async def send_signal(
        self,
        workflow_id: str,
        signal: Union[str, Callable],
        payload: Union[dict, list, str, int, float, bool, BaseModel]
    ) -> None:
        handle = self.client.get_workflow_handle(workflow_id=workflow_id)
        await handle.signal(signal, payload)

    async def get_workflow_status(self, workflow_id: str) -> WorkflowState:
        try:
            handle = self.client.get_workflow_handle(workflow_id=workflow_id)
            description = await handle.describe()
            return TEMPORAL_STATUS_TO_UPLOAD_STATUS_AND_REASON[description.status]
        except RPCError as e:
            if e.status == RPCStatusCode.NOT_FOUND:
                return WorkflowState(
                    status="NOT_FOUND",
                    reason="Workflow not found",
                    is_terminal=True,
                )
            raise

    async def terminate_workflow(self, workflow_id: str) -> None:
        return await self.client.get_workflow_handle(workflow_id).terminate()

    async def cancel_workflow(self, workflow_id: str) -> None:
        return await self.client.get_workflow_handle(workflow_id).cancel()


DTemporalGateway = Annotated[TemporalGateway, Depends(TemporalGateway)]
