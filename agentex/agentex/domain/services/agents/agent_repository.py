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
        if agents:
            agent_ids = [agent.id for agent in agents]

        if actions:
            action_ids = [action.id for action in actions]

        async with self.start_async_db_session(True) as session, async_sql_exception_handler():
            # Associate agents with actions
            agent_orms = await self._batch_get(session, agent_ids, agent_names)
            action_orms = await self.action_repository._batch_get(session, action_ids, action_names)

            for agent_orm in agent_orms:
                for action_orm in action_orms:
                    agent_orm.actions.append(action_orm)

            # Save changes to the session
            await session.commit()

            return agents


DAgentRepository = Annotated[AgentRepository, Depends(AgentRepository)]
