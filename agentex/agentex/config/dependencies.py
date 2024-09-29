import asyncio
from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine, create_async_engine

from agentex.config.environment_variables import EnvironmentVariables, Environment
from agentex.utils.database import async_db_engine_creator


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class GlobalDependencies(metaclass=Singleton):

    def __init__(self):
        self.environment_variables: EnvironmentVariables = EnvironmentVariables.refresh()
        self.database_async_read_write_engine: Optional[AsyncEngine] = None
        # self.database_async_read_only_engine: Optional[AsyncEngine] = None

    async def load(self):
        self.environment_variables = EnvironmentVariables.refresh()

        echo_db_engine = self.environment_variables.ENV == Environment.DEV
        async_db_pool_size = 10

        # https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine
        self.database_async_read_write_engine = create_async_engine(
            "postgresql+asyncpg://",
            async_creator=async_db_engine_creator(
                self.environment_variables.DATABASE_URL,
            ),
            echo=echo_db_engine,
            pool_size=async_db_pool_size,
            pool_pre_ping=True,
        )

        # self.database_async_read_only_engine = create_async_engine(
        #     "postgresql+asyncpg://",
        #     async_creator=async_db_engine_creator(
        #         self.environment_variables.READ_ONLY_DATABASE_URL,
        #     ),
        #     echo=echo_db_engine,
        #     pool_size=async_db_pool_size,
        #     pool_pre_ping=True,
        # )


async def startup_global_dependencies():
    global_dependencies = GlobalDependencies()
    await global_dependencies.load()


def shutdown():
    pass


async def async_shutdown():
    global_dependencies = GlobalDependencies()
    run_concurrently = []
    # if global_dependencies.database_async_read_only_engine:
    #     run_concurrently.append(global_dependencies.database_async_read_only_engine.dispose())
    if global_dependencies.database_async_read_write_engine:
        run_concurrently.append(global_dependencies.database_async_read_write_engine.dispose())
    await asyncio.gather(*run_concurrently)


def environment_variables():
    return GlobalDependencies().environment_variables


DEnvironmentVariables = Annotated[EnvironmentVariables, Depends(environment_variables)]


def resolve_environment_variable_dependency(environment_variable_key: str):
    return getattr(GlobalDependencies().environment_variables, environment_variable_key)


def DEnvironmentVariable(environment_variable_key: str):
    def resolve():
        return resolve_environment_variable_dependency(environment_variable_key)

    return Annotated[str, Depends(resolve)]


def database_async_read_write_engine() -> AsyncEngine:
    return GlobalDependencies().database_async_read_write_engine


# def database_async_read_only_engine() -> AsyncEngine:
#     return GlobalDependencies().database_async_read_only_engine


DDatabaseAsyncReadWriteEngine = Annotated[AsyncEngine, Depends(database_async_read_write_engine)]


# DDatabaseAsyncReadOnlyEngine = Annotated[AsyncEngine, Depends(database_async_read_only_engine)]


def database_async_read_write_session_maker(
    db_async_read_write_engine: DDatabaseAsyncReadWriteEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        autoflush=False, bind=db_async_read_write_engine, expire_on_commit=False
    )


# def database_async_read_only_session_maker(
#     db_async_read_only_engine: DDatabaseAsyncReadOnlyEngine,
# ) -> async_sessionmaker[AsyncSession]:
#     return async_sessionmaker(
#         autoflush=False, bind=db_async_read_only_engine, expire_on_commit=False
#     )


DDatabaseAsyncReadWriteSessionMaker = Annotated[
    async_sessionmaker[AsyncSession], Depends(database_async_read_write_session_maker)
]
# DDatabaseAsyncReadOnlySessionMaker = Annotated[
#     async_sessionmaker[AsyncSession], Depends(database_async_read_only_session_maker)
# ]
