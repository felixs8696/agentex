from typing import Annotated

from fastapi import Depends

from agentex.adapters.llm.adapter_litellm import DLiteLLMGateway
from agentex.domain.entities.agent_config import AgentConfig, LLMConfig
from agentex.domain.entities.messages import Message, UserMessage
from agentex.domain.entities.tasks import Task
from agentex.domain.services.agent_tasks.task_service import DAgentTaskService
from agentex.domain.services.agents.agent_repository import DAgentRepository
from agentex.utils.ids import orm_id
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class TaskUseCase:

    def __init__(
        self,
        llm_gateway: DLiteLLMGateway,
        task_service: DAgentTaskService,
        agent_repository: DAgentRepository,
    ):
        self.llm = llm_gateway
        self.task_service = task_service
        self.agent_repository = agent_repository
        self.model = "gpt-4o-mini"

    async def execute(self, agent_name: str, prompt: str) -> Task:
        agent = await self.agent_repository.get(
            name=agent_name,
        )
        task = Task(
            id=orm_id(),
            prompt=prompt,
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


DTaskUseCase = Annotated[TaskUseCase, Depends(TaskUseCase)]
