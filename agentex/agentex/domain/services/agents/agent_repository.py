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

    async def get_by_name_and_version(self, name: str, version: str):
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            result = await session.scalar(
                select(self.orm).filter(self.orm.name == name, self.orm.version == version)
            )

            if result is None:
                error_message = f"Agent with name '{name}' and version '{version}' does not exist."
                raise ItemDoesNotExist(error_message)

            return self.entity.from_orm(result)

    async def get_latest_version_by_name(self, name: str):
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            result = await session.scalar(
                select(self.orm)
                .filter(self.orm.name == name)
                .order_by(self.orm.version.desc())
                .limit(1)
            )

            if result is None:
                error_message = f"Agent with name '{name}' does not exist."
                raise ItemDoesNotExist(error_message)

            return self.entity.from_orm(result)


DAgentRepository = Annotated[AgentRepository, Depends(AgentRepository)]
