from typing import Annotated, Optional

from fastapi import Depends

from agentex.adapters.async_runtime.adapter_temporal import DTemporalGateway
from agentex.domain.entities.agents import Agent
from agentex.domain.entities.tasks import Task
from agentex.domain.entities.workflows import WorkflowState
from agentex.domain.workflows.constants import AGENT_TASK_TASK_QUEUE
from agentex.domain.workflows.run_agent_task_workflow import AgentTaskWorkflow, AgentTaskWorkflowParams, \
    HumanInstruction


class AgentTaskService:
    """
    Submits Agent agent_tasks to the async runtime for execution.
    """

    def __init__(
        self,
        async_runtime: DTemporalGateway,
    ):
        self.async_runtime = async_runtime
        self.task_queue = AGENT_TASK_TASK_QUEUE

    async def submit_task(self, task: Task, agent: Agent, require_approval: Optional[bool] = False) -> str:
        """
        Submit a task to the async runtime for execution.

        returns the workflow ID of the temporal workflow
        """
        return await self.async_runtime.start_workflow(
            AgentTaskWorkflow.run,
            AgentTaskWorkflowParams(
                task=task,
                agent=agent,
                require_approval=require_approval,
            ),
            id=task.id,
            task_queue=self.task_queue,
        )

    async def get_state(self, task_id: str) -> WorkflowState:
        """
        Get the task state from the async runtime.
        """
        return await self.async_runtime.get_workflow_status(
            workflow_id=task_id,
        )

    async def instruct(self, task_id: str, prompt: str) -> None:
        return await self.async_runtime.send_signal(
            workflow_id=task_id,
            signal=AgentTaskWorkflow.instruct,
            payload=HumanInstruction(
                task_id=task_id,
                prompt=prompt,
            )
        )

    async def approve(self, task_id: str) -> None:
        return await self.async_runtime.send_signal(
            workflow_id=task_id,
            signal=AgentTaskWorkflow.approve,
            payload=None
        )

    async def cancel(self, task_id: str) -> None:
        return await self.async_runtime.cancel_workflow(
            workflow_id=task_id,
        )

    async def terminate(self, task_id: str) -> None:
        return await self.async_runtime.terminate_workflow(
            workflow_id=task_id,
        )


DAgentTaskService = Annotated[AgentTaskService, Depends(AgentTaskService)]
