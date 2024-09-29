from abc import ABC, abstractmethod
from typing import Annotated, List

from fastapi import Depends

from agentex.domain.entities.agents import Agent


class AgentRepository(ABC):

    @abstractmethod
    async def get(self, id: str) -> Agent:
        raise NotImplementedError

    @abstractmethod
    async def create(self, agent: Agent) -> Agent:
        raise NotImplementedError

    @abstractmethod
    async def update(self, agent: Agent) -> Agent:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> List[Agent]:
        raise NotImplementedError


DAgentRepository = Annotated[AgentRepository, Depends(AgentRepository)]
