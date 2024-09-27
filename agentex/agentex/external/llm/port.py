from abc import ABC, abstractmethod
from typing import Annotated, Optional
from fastapi import Depends

from agentex.external.llm.entities import Message


class LLMGateway(ABC):

    @abstractmethod
    def completion(self, *args, **kwargs) -> Message:
        pass

    @abstractmethod
    async def acompletion(self, *args, **kwargs) -> Message:
        pass


DLLMGateway = Annotated[Optional[LLMGateway], Depends(LLMGateway)]
