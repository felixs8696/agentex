from agentex.adapters.crud_store.adapter_postgres import PostgresCRUDRepository
from agentex.adapters.orm import AgentORM
from agentex.domain.entities.agents import Agent

AgentRepository = PostgresCRUDRepository[AgentORM, Agent]
