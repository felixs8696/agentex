from typing import Annotated

from fastapi import Depends

from agentex.adapters.llm.adapter_litellm import DLiteLLMGateway
from agentex.api.schemas.tasks import GetTaskResponse
from agentex.domain.entities.tasks import Task
from agentex.domain.services.agent_tasks.task_service import DAgentTaskService
from agentex.domain.services.agents.agent_repository import DAgentRepository
from agentex.domain.services.agents.agent_state_repository import DAgentStateRepository
from agentex.domain.services.agents.task_respository import DTaskRepository
from agentex.utils.ids import orm_id
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class TasksUseCase:

    def __init__(
        self,
        llm_gateway: DLiteLLMGateway,
        task_service: DAgentTaskService,
        task_repository: DTaskRepository,
        agent_repository: DAgentRepository,
        agent_state_repository: DAgentStateRepository,
    ):
        self.llm = llm_gateway
        self.task_service = task_service
        self.task_repository = task_repository
        self.agent_repository = agent_repository
        self.agent_state_repository = agent_state_repository
        self.model = "gpt-4o-mini"

    async def create(self, agent_name: str, agent_version: str, prompt: str) -> Task:
        agent = await self.agent_repository.get_by_name_and_version(
            name=agent_name,
            version=agent_version,
        )
        task = await self.task_repository.create(
            Task(
                id=orm_id(),
                agent_id=agent.id,
                prompt=prompt,
            )
        )
        task_id = await self.task_service.submit_task(
            task=task,
            agent=agent,
        )
        assert task_id == task.id, f"Task ID mismatch: {task_id} != {task.id}"
        return task

    async def get(self, task_id: str) -> GetTaskResponse:
        task = await self.task_repository.get(id=task_id)
        task_state = await self.task_service.get_state(task_id=task_id)
        agent_state = await self.agent_state_repository.load(task_id=task_id)

        return GetTaskResponse(
            state=task_state,
            **task.to_dict(),
            **agent_state.to_dict(),
        )


DTaskUseCase = Annotated[TasksUseCase, Depends(TasksUseCase)]
