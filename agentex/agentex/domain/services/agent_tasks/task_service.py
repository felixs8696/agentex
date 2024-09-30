from typing import Annotated

from fastapi import Depends

from agentex.adapters.async_runtime.adapter_temporal import DTemporalGateway
from agentex.domain.entities.agent_config import AgentConfig
from agentex.domain.entities.tasks import Task
from agentex.domain.workflows.agent_task_workflow import AgentTaskWorkflow, AgentTaskWorkflowParams
from agentex.domain.workflows.constants import AGENT_TASK_TASK_QUEUE


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

    def submit_task(self, task: Task, agent_config: AgentConfig) -> str:
        """
        Submit a task to the async runtime for execution.

        returns the workflow ID of the temporal workflow
        """
        return self.async_runtime.start_workflow(
            AgentTaskWorkflow.run,
            AgentTaskWorkflowParams(
                task=task,
                agent_config=agent_config,
            ),
            id=task.id,
            task_queue=self.task_queue,
        )


DAgentTaskService = Annotated[AgentTaskService, Depends(AgentTaskService)]
