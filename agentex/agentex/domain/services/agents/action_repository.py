from typing import Annotated

from fastapi import Depends

from agentex.adapters.crud_store.adapter_postgres import PostgresCRUDRepository
from agentex.adapters.orm import ActionORM
from agentex.config.dependencies import DDatabaseAsyncReadWriteSessionMaker
from agentex.domain.entities.actions import Action
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class ActionRepository(PostgresCRUDRepository[ActionORM, Action]):
    def __init__(self, async_read_write_session_maker: DDatabaseAsyncReadWriteSessionMaker):
        super().__init__(async_read_write_session_maker, ActionORM, Action)


DActionRepository = Annotated[ActionRepository, Depends(ActionRepository)]
