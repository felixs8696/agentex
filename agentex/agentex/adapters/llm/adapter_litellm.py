from typing import Annotated, Optional

import litellm as llm
from fastapi import Depends

from agentex.adapters.llm.port import LLMGateway
from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.messages import Message, LLMChoice


class LiteLLMGateway(LLMGateway):
    def __init__(self, environment_variables: DEnvironmentVariables):
        self.environment_variables = environment_variables

    def completion(self, *args, **kwargs) -> LLMChoice:
        choice = llm.completion(*args, **kwargs).choices[0]
        if kwargs.get('response_format'):
            choice.message.parsed = kwargs['response_format'].from_json(choice.message.content)
        return LLMChoice.from_orm(choice)

    async def acompletion(self, *args, **kwargs) -> LLMChoice:
        response = await llm.acompletion(*args, **kwargs)
        choice = response.choices[0]
        if kwargs.get('response_format'):
            choice.message.parsed = kwargs['response_format'].from_json(choice.message.content)
        try:
            return LLMChoice.from_orm(choice)
        except Exception as e:
            raise Exception(f"Error parsing response: {e}, Choice: {choice}")


DLiteLLMGateway = Annotated[Optional[LiteLLMGateway], Depends(LiteLLMGateway)]
