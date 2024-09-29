from typing import Optional, List, Annotated

from fastapi import Depends

from agentex.domain.agents.agent_repository import DAgentRepository
from agentex.domain.entities.agents import Agent
from agentex.utils.ids import orm_id
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class AgentCRUDService:

    def __init__(
        self,
        agent_repository: DAgentRepository
    ):
        logger.info("Initializing AgentCRUDService")
        self.agent_repo = agent_repository

    async def create(self, name: str) -> Agent:
        return await self.agent_repo.create(item=Agent(id=orm_id(), name=name))

    async def get(self, id: Optional[str], name: Optional[str]) -> Agent:
        return await self.agent_repo.get(id=id, name=name)

    async def update(self, agent: Agent) -> Agent:
        return await self.agent_repo.update(item=agent)

    async def delete(self, id: Optional[str], name: Optional[str]) -> Agent:
        return await self.agent_repo.delete(id=id, name=name)

    async def list(self) -> List[Agent]:
        return await self.agent_repo.list()


DAgentCRUDService = Annotated[AgentCRUDService, Depends(AgentCRUDService)]
