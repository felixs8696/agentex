from typing import Annotated, List, Optional

from fastapi import Depends

from agentex.adapters.crud_store.adapter_postgres import PostgresCRUDRepository, async_sql_exception_handler
from agentex.adapters.orm import AgentORM
from agentex.config.dependencies import DDatabaseAsyncReadWriteSessionMaker
from agentex.domain.entities.actions import Action
from agentex.domain.entities.agents import Agent
from agentex.domain.services.agents.action_repository import DActionRepository
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class AgentRepository(PostgresCRUDRepository[AgentORM, Agent]):
    def __init__(
        self,
        async_read_write_session_maker: DDatabaseAsyncReadWriteSessionMaker,
        action_repository: DActionRepository,
    ):
        super().__init__(async_read_write_session_maker, AgentORM, Agent)
        self.action_repository = action_repository

    async def associate_agents_with_actions(
        self,
        agent_ids: Optional[List[str]] = None,
        agent_names: Optional[List[str]] = None,
        agents: Optional[List[Agent]] = None,
        action_ids: Optional[List[str]] = None,
        action_names: Optional[List[str]] = None,
        actions: Optional[List[Action]] = None,
    ) -> List[Agent]:
        # Fetch existing agents and actions from the database
        if not agents:
            agents = await self.batch_get(ids=agent_ids, names=agent_names)
        if not actions:
            actions = await self.action_repository.batch_get(ids=action_ids, names=action_names)

        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            # Associate agents with actions
            for agent in agents:
                for action in actions:
                    agent.actions.append(action)

            # Save changes to the session
            await session.commit()

            return agents


DAgentRepository = Annotated[AgentRepository, Depends(AgentRepository)]
