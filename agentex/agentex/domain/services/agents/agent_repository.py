from typing import Annotated

from fastapi import Depends
from sqlalchemy import select

from agentex.adapters.crud_store.adapter_postgres import PostgresCRUDRepository, async_sql_exception_handler
from agentex.adapters.crud_store.exceptions import ItemDoesNotExist
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
