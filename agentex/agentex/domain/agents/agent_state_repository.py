from typing import Optional, Annotated

from fastapi import Depends

from agentex.adapters.memory.port import DMemoryRepository
from agentex.domain.entities.agent_state import AgentState


class AgentStateRepository:
    def __init__(self, memory_repo: DMemoryRepository):
        self.memory_repo = memory_repo

    @staticmethod
    def _serialize(state: AgentState) -> str:
        """Serialize the AgentState object into a JSON string."""
        return state.to_json()

    @staticmethod
    def _deserialize(data: Optional[str]) -> AgentState:
        """Deserialize the JSON string back into an AgentState object."""
        if data is None:
            return AgentState()
        return AgentState.from_json(data)

    async def save(self, task_id: str, state: AgentState) -> None:
        """Save the AgentState to Redis."""
        serialized_state = self._serialize(state)
        await self.memory_repo.set(task_id, serialized_state)

    async def load(self, task_id: str) -> AgentState:
        """Load the AgentState from Redis."""
        data = await self.memory_repo.get(task_id)
        return self._deserialize(data)

    async def delete(self, task_id: str) -> None:
        """Delete the AgentState from Redis."""
        await self.memory_repo.delete(task_id)


DAgentStateRepository = Annotated[AgentStateRepository, Depends(AgentStateRepository)]
