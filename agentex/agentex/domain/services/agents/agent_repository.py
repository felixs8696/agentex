from typing import Annotated

from fastapi import Depends

from agentex.adapters.crud_store.adapter_postgres import PostgresCRUDRepository
from agentex.adapters.orm import AgentORM
from agentex.config.dependencies import DDatabaseAsyncReadWriteSessionMaker
from agentex.domain.entities.agents import Agent
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class AgentRepository(PostgresCRUDRepository[AgentORM, Agent]):
    def __init__(
        self,
        async_read_write_session_maker: DDatabaseAsyncReadWriteSessionMaker,
    ):
        super().__init__(async_read_write_session_maker, AgentORM, Agent)


DAgentRepository = Annotated[AgentRepository, Depends(AgentRepository)]
