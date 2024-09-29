from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, List, TypeVar, Optional, Generic, Type

from fastapi import Depends
from sqlalchemy import exc, select
from sqlalchemy.ext.asyncio import AsyncSession

from agentex.adapters.crud_store.exceptions import DuplicateItemError, ItemDoesNotExist
from agentex.adapters.crud_store.port import CRUDRepository
from agentex.adapters.orm import BaseORM
from agentex.config.dependencies import DDatabaseAsyncReadWriteSessionMaker
from agentex.domain.exceptions import ServiceError, ClientError
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)

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
                message="Item already exists. Please check all unique constraints and try again.",
                detail=str(e)
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


T = TypeVar("T", bound=BaseModel)
M = TypeVar("M", bound=BaseORM)


class PostgresCRUDRepository(CRUDRepository[T], Generic[M, T]):
    def __init__(
        self,
        async_read_write_session_maker: DDatabaseAsyncReadWriteSessionMaker,
        orm: Type[M],
        entity: Type[T],
    ):
        self.async_rw_session_maker = async_read_write_session_maker
        self.orm = orm
        self.entity = entity

    @asynccontextmanager
    async def start_async_db_session(self, allow_writes: Optional[bool] = True) -> AsyncGenerator[AsyncSession, None]:
        if allow_writes:
            session_maker = self.async_rw_session_maker
        else:
            raise NotImplementedError("Read-only sessions are not yet supported.")
        async with session_maker() as session:
            async with session.begin():
                yield session

    async def create(self, item: T) -> T:
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            orm = self.orm(**item.to_dict())
            session.add(orm)
            await session.commit()
            return self.entity.from_orm(orm)

    async def get(self, id: Optional[str], name: Optional[str]) -> T:
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            if id is not None:
                result = session.scalar(select(T).filter(T.id == id))
            elif name is not None:
                result = session.scalar(select(T).filter(T.name == name))
            else:
                raise ClientError("Either id or name must be provided.")
            if result is None:
                raise ItemDoesNotExist(f'Item with id "{id}" does not exist.')
            return self.entity.from_orm(result)

    async def update(self, item: T) -> T:
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            orm = self.orm(**item.to_dict())
            session.merge(orm)
            await session.commit()
            return self.entity.from_orm(orm)

    async def delete(self, id: Optional[str], name: Optional[str]) -> T:
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            if id is not None:
                result = session.scalar(select(T).filter(T.id == id))
            elif name is not None:
                result = session.scalar(select(T).filter(T.name == name))
            else:
                raise ClientError("Either id or name must be provided.")
            if result is None:
                raise ItemDoesNotExist(f'Item with id "{id}" does not exist.')
            session.delete(result)
            await session.commit()
            return self.entity.from_orm(result)

    async def list(self) -> List[T]:
        async with self.start_async_db_session(False) as session, async_sql_exception_handler():
            results = session.execute(select(T)).scalars()
            return [self.entity.from_orm(result) for result in results]


DPostgresCRUDRepository = Annotated[PostgresCRUDRepository, Depends(PostgresCRUDRepository)]
