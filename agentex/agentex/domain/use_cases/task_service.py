from typing import Annotated

from fastapi import Depends

from agentex.adapters.llm.adapter_litellm import DLiteLLMGateway
from agentex.adapters.llm.entities import Message, UserMessage
from agentex.domain.entities.tasks import Task
from agentex.utils.ids import orm_id


class TaskService:

    def __init__(self, llm_gateway: DLiteLLMGateway):
        self.llm = llm_gateway
        self.model = "gpt-4o-mini"

    async def execute(self, prompt: str) -> Message:
        task = Task(
            id=orm_id(),
            prompt=prompt,
        )
        # Just call an LLM for now
        # TODO: Replace with real task execution
        return await self.llm.acompletion(
            model=self.model,
            messages=[
                UserMessage(content=task.prompt, role="user"),
            ]
        )


DTaskService = Annotated[TaskService, Depends(TaskService)]
