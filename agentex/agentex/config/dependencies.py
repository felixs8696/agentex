from typing import Annotated

from fastapi import Depends

from agentex.config.environment_variables import EnvironmentVariables


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class GlobalDependencies(metaclass=Singleton):

    def __init__(self):
        self.environment_variables: EnvironmentVariables = EnvironmentVariables.refresh()

    async def load(self):
        self.environment_variables = EnvironmentVariables.refresh()


async def startup_global_dependencies():
    global_dependencies = GlobalDependencies()
    await global_dependencies.load()


async def async_shutdown():
    pass


def shutdown():
    pass


def environment_variables():
    return GlobalDependencies().environment_variables


DEnvironmentVariables = Annotated[EnvironmentVariables, Depends(environment_variables)]


def resolve_environment_variable_dependency(environment_variable_key: str):
    return getattr(GlobalDependencies().environment_variables, environment_variable_key)


def DEnvironmentVariable(environment_variable_key: str):
    def resolve():
        return resolve_environment_variable_dependency(environment_variable_key)

    return Annotated[str, Depends(resolve)]
