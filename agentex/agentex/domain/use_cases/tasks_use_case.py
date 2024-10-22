from typing import Annotated, Optional, List

from fastapi import Depends

from agentex.adapters.llm.adapter_litellm import DLiteLLMGateway
from agentex.api.schemas.tasks import TaskModel, ModifyTaskRequest
from agentex.domain.entities.instructions import TaskModificationType
from agentex.domain.entities.tasks import Task
from agentex.domain.exceptions import ClientError
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

    async def create(self, agent_name: str, agent_version: str, prompt: str,
                     require_approval: Optional[bool] = False) -> Task:
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
            require_approval=require_approval,
        )
        assert task_id == task.id, f"Task ID mismatch: {task_id} != {task.id}"
        return task

    async def get(self, task_id: str) -> TaskModel:
        task = await self.task_repository.get(id=task_id)
        task_state = await self.task_service.get_state(task_id=task_id)
        agent_state = await self.agent_state_repository.load(task_id=task_id)

        task.status = task_state.status
        task.status_reason = task_state.reason

        if task_state.is_terminal:
            await self.update(task)

        return TaskModel(
            **task.to_dict(),
            **agent_state.to_dict(),
        )

    async def modify(self, task_id: str, modification_request: ModifyTaskRequest) -> None:
        if modification_request.type == TaskModificationType.CANCEL:
            return await self.task_service.cancel(task_id=task_id)
        elif modification_request.type == TaskModificationType.APPROVE:
            return await self.task_service.approve(task_id=task_id)
        elif modification_request.type == TaskModificationType.INSTRUCT:
            return await self.task_service.instruct(
                task_id=task_id,
                prompt=modification_request.prompt,
            )
        else:
            raise ClientError(f"Invalid modification request: {modification_request}")

    async def update(self, task: Task) -> Task:
        return await self.task_repository.update(item=task)

    async def delete(self, id: Optional[str], name: Optional[str]) -> Task:
        return await self.task_repository.delete(id=id, name=name)

    async def list(self) -> List[Task]:
        return await self.task_repository.list()


DTaskUseCase = Annotated[TasksUseCase, Depends(TasksUseCase)]
