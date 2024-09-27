from typing import Annotated, Optional

import litellm as llm
from agentex.external.llm.entities import Message
from fastapi import Depends

from agentex.external.llm.port import LLMGateway


class LiteLLMGateway(LLMGateway):

    def completion(self, *args, **kwargs) -> Message:
        message = llm.completion(*args, **kwargs).choices[0].message
        if kwargs.get('response_format'):
            message.parsed = kwargs['response_format'].from_json(message.content)
        return message

    async def acompletion(self, *args, **kwargs) -> Message:
        response = await llm.acompletion(*args, **kwargs)
        message = response.choices[0].message
        if kwargs.get('response_format'):
            message.parsed = kwargs['response_format'].from_json(message.content)
        return message


DLiteLLMGateway = Annotated[Optional[LiteLLMGateway], Depends(LiteLLMGateway)]
