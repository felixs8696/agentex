from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, List, TypeVar, Optional, Generic, Type

from fastapi import Depends
from sqlalchemy import exc, select, update, delete
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
                message=f"Invalid input resulted in constraint violation: {e}", detail=str(e)
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
            # await session.refresh(orm)
            return self.entity.from_orm(orm)

    async def batch_create(self, items: List[T]) -> List[T]:
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            # Prepare a list of ORM instances from items
            orm_instances = [self.orm(**item.to_dict()) for item in items]
            session.add_all(orm_instances)
            await session.commit()

            # # Refresh each instance to retrieve any auto-generated fields (like IDs)
            # for orm_instance in orm_instances:
            #     await session.refresh(orm_instance)

            return [self.entity.from_orm(orm_instance) for orm_instance in orm_instances]

    async def get(self, id: Optional[str] = None, name: Optional[str] = None) -> T:
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            result = await self._get(session, id, name)
            return self.entity.from_orm(result)

    async def batch_get(self, ids: Optional[List[str]] = None, names: Optional[List[str]] = None) -> List[T]:
        async with self.start_async_db_session(False) as session, async_sql_exception_handler():
            results = await self._batch_get(session, ids, names)
            return [self.entity.from_orm(result) for result in results]

    async def update(self, item: T) -> T:
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            orm = self.orm(**item.to_dict())
            modified_orm = await session.merge(orm)
            await session.commit()
            return self.entity.from_orm(modified_orm)

    async def batch_update(self, items: List[T]) -> List[T]:
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            # Convert each item to a dictionary, which includes the primary key and updated fields
            update_data = [item.to_dict() for item in items]

            # Perform the bulk update by primary key
            await session.execute(
                update(self.orm),  # The update ORM construct for the mapped entity
                update_data  # A list of dictionaries, each containing the PK and updated fields
            )
            # Commit the changes
            await session.commit()

            # Return the updated items as ORM objects
            return [self.entity.from_orm(item) for item in items]

    async def delete(self, id: Optional[str] = None, name: Optional[str] = None) -> None:
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            # Ensure at least one of id or name is provided
            if not id and not name:
                raise ClientError("You must provide either id or name for deletion.")

            # Build the delete query
            if id:
                stmt = delete(self.orm).where(self.orm.id == id)
            elif name:
                stmt = delete(self.orm).where(self.orm.name == name)

            # Execute the delete statement
            await session.execute(stmt)
            await session.commit()

    async def batch_delete(self, ids: Optional[List[str]] = None, names: Optional[List[str]] = None) -> None:
        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            # Ensure at least one of ids or names is provided
            if not ids and not names:
                raise ClientError("You must provide either ids or names for deletion.")

            # Construct the delete query based on available criteria
            if ids:
                stmt = delete(self.orm).where(self.orm.id.in_(ids))
            elif names:
                stmt = delete(self.orm).where(self.orm.name.in_(names))

            # Execute the delete operation
            await session.execute(stmt)
            await session.commit()

    async def list(self) -> List[T]:
        async with self.start_async_db_session(False) as session, async_sql_exception_handler():
            results = await session.execute(select(self.orm)).scalars()
            return [self.entity.from_orm(result) for result in results]

    async def _get(self, session: AsyncSession, id: Optional[str] = None, name: Optional[str] = None) -> M:
        if id is not None:
            result = await session.scalar(select(self.orm).filter(self.orm.id == id))
        elif name is not None:
            result = await session.scalar(select(self.orm).filter(self.orm.name == name))
        else:
            raise ClientError("Either id or name must be provided.")
        if result is None:
            if id is not None:
                error_message = f"Item with id '{id}' does not exist."
            else:
                error_message = f"Item with name '{name}' does not exist."
            raise ItemDoesNotExist(error_message)
        return result

    async def _batch_get(
        self, session: AsyncSession, ids: Optional[List[str]] = None, names: Optional[List[str]] = None
    ) -> M:
        if ids is not None:
            results = await session.execute(select(self.orm).filter(self.orm.id.in_(ids)))
        elif names is not None:
            results = await session.execute(select(self.orm).filter(self.orm.name.in_(names)))
        else:
            raise ClientError("Either ids or names must be provided.")
        if results is None:
            if ids is not None:
                error_message = f"Item with id '{ids}' does not exist."
            else:
                error_message = f"Item with name '{names}' does not exist."
            raise ItemDoesNotExist(error_message)
        return results


DPostgresCRUDRepository = Annotated[PostgresCRUDRepository, Depends(PostgresCRUDRepository)]
