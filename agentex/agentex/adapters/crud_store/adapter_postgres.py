from abc import ABC
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, List

from fastapi import Depends
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncSession

from agentex.config.dependencies import DDatabaseAsyncReadWriteSessionMaker
from agentex.domain.agents.exceptions import DuplicateItemError
from agentex.domain.entities.agents import Agent
from agentex.domain.exceptions import ServiceError

DUPLICATE_KEY_VAL_ERR = "duplicate key value"
CHECK_CONSTRAINT_ERR = "violates check constraint"


@asynccontextmanager
async def async_sql_exception_handler():
    try:
        yield
    except exc.IntegrityError as e:
        # Handle SQLAlchemy exceptions here
        if DUPLICATE_KEY_VAL_ERR in str(e):
            raise DuplicateItemError(
                message="Item already exists, cannot insert duplicate key", detail=str(e)
            )
        else:
            raise ServiceError(
                message="Invalid input resulted in constraint violation", detail=str(e)
            )
    except exc.NoResultFound as e:
        raise ItemDoesNotExist(message="No record found for given key", detail=str(e))
    except exc.NoForeignKeysError as e:
        raise ItemDoesNotExist(
            message="No foreign relationships found for given key", detail=str(e)
        )
    except Exception as e:
        # only raising the exception currently since a ServerError will result in a code = 500, breaking existing behavior
        raise e


class AgentRepository(ABC):
    def __init__(
        self,
        async_read_write_session_maker: DDatabaseAsyncReadWriteSessionMaker,
        # async_read_only_session_maker: DDatabaseAsyncReadOnlySessionMaker,
    ):
        self.async_rw_session_maker = async_read_write_session_maker
        # self.async_r_only_session_maker = async_read_only_session_maker

    @asynccontextmanager
    async def start_async_db_session(self, allow_writes=True) -> AsyncGenerator[AsyncSession, None]:
        if allow_writes:
            session_maker = self.async_rw_session_maker
        else:
            raise NotImplementedError("Read-only sessions are not yet supported.")
        async with session_maker() as session:
            async with session.begin():
                yield session

    async def get(self, id: str) -> Agent:
        with self.start_async_db_session() as session:


    async def create(self, agent: Agent) -> Agent:
        raise NotImplementedError

    async def update(self, agent: Agent) -> Agent:
        raise NotImplementedError

    async def delete(self, id: str) -> None:
        raise NotImplementedError

    async def list(self) -> List[Agent]:
        raise NotImplementedError


DAgentRepository = Annotated[AgentRepository, Depends(AgentRepository)]
