from typing import Annotated

from fastapi import Depends

from agentex.adapters.crud_store.adapter_postgres import PostgresCRUDRepository
from agentex.adapters.orm import TaskORM
from agentex.config.dependencies import DDatabaseAsyncReadWriteSessionMaker
from agentex.domain.entities.tasks import Task
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class TaskRepository(PostgresCRUDRepository[TaskORM, Task]):
    def __init__(self, async_read_write_session_maker: DDatabaseAsyncReadWriteSessionMaker):
        super().__init__(async_read_write_session_maker, TaskORM, Task)


DTaskRepository = Annotated[TaskRepository, Depends(TaskRepository)]
