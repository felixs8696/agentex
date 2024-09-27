from typing import Annotated

from fastapi import Depends

from agentex.external.llm.adapter_litellm import DLiteLLMGateway
from agentex.external.llm.entities import Message, UserMessage


class TaskService:

    def __init__(self, llm_gateway: DLiteLLMGateway):
        self.llm = llm_gateway
        self.model = "gpt-4o-mini"

    async def execute(self, prompt: str) -> Message:
        # Just call an LLM for now
        # TODO: Replace with real task execution
        return await self.llm.acompletion(
            model=self.model,
            messages=[
                UserMessage(content=prompt, role="user"),
            ]
        )


DTaskService = Annotated[TaskService, Depends(TaskService)]
