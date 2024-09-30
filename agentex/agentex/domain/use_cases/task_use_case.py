from typing import Annotated

from fastapi import Depends

from agentex.adapters.llm.adapter_litellm import DLiteLLMGateway
from agentex.api.schemas.tasks import GetTaskResponse
from agentex.domain.entities.agent_config import AgentConfig, LLMConfig
from agentex.domain.entities.messages import Message, UserMessage
from agentex.domain.entities.tasks import Task
from agentex.domain.services.agent_tasks.task_service import DAgentTaskService
from agentex.domain.services.agents.agent_repository import DAgentRepository
from agentex.domain.services.agents.agent_state_repository import DAgentStateRepository
from agentex.domain.services.agents.task_respository import DTaskRepository
from agentex.utils.ids import orm_id
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class TaskUseCase:

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

    async def create(self, agent_name: str, prompt: str) -> Task:
        agent = await self.agent_repository.get(
            name=agent_name,
        )
        task = await self.task_repository.create(
            Task(
                id=orm_id(),
                agent_id=agent.id,
                prompt=prompt,
            )
        )
        logger.info(f"AGENT: {agent}")
        dummy_agent_config = AgentConfig(
            agent=agent,
            llm_config=LLMConfig(
                model=self.model,
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "dummy_tool",
                            "description": """
Call this just to check that you can call a tool from the agent.
You must call this tool, but just do it once.
                        """,
                            "parameters": {},
                        }
                    }
                ],
                tool_choice="auto",
            )
        )
        task_id = await self.task_service.submit_task(
            task=task,
            agent_config=dummy_agent_config,
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


DTaskUseCase = Annotated[TaskUseCase, Depends(TaskUseCase)]
