from typing import List, Dict, Any, Optional, Annotated

from fastapi import Depends

from agentex.adapters.llm.entities import Message
from agentex.domain.agent_state.agent_state_repository import AgentStateRepository, DAgentStateRepository
from agentex.domain.entities.agent_state import AgentState


class MessagesService:
    def __init__(self, repository: AgentStateRepository):
        self.repository = repository

    async def get_all(self, task_id: str) -> List[Message]:
        state = await self.repository.load(task_id)
        return state.messages

    async def get_by_index(self, task_id: str, index: int) -> Optional[Message]:
        state = await self.repository.load(task_id)
        if 0 <= index < len(state.messages):
            return state.messages[index]
        return None

    async def batch_get_by_indices(self, task_id: str, indices: List[int]) -> List[Optional[Message]]:
        state = await self.repository.load(task_id)
        return [state.messages[i] if 0 <= i < len(state.messages) else None for i in indices]

    async def append(self, task_id: str, message: Message) -> None:
        state = await self.repository.load(task_id)
        state.messages.append(message)
        await self.repository.save(task_id, state)

    async def batch_append(self, task_id: str, messages: List[Message]) -> None:
        state = await self.repository.load(task_id)
        state.messages.extend(messages)
        await self.repository.save(task_id, state)

    async def override(self, task_id: str, index: int, message: Message) -> None:
        state = await self.repository.load(task_id)
        if 0 <= index < len(state.messages):
            state.messages[index] = message
            await self.repository.save(task_id, state)

    async def batch_override(self, task_id: str, updates: Dict[int, str]) -> None:
        state = await self.repository.load(task_id)
        for index, message in updates.items():
            if 0 <= index < len(state.messages):
                state.messages[index] = message
        await self.repository.save(task_id, state)

    async def insert(self, task_id: str, index: int, message: Message) -> None:
        state = await self.repository.load(task_id)
        state.messages.insert(index, message)
        await self.repository.save(task_id, state)

    async def batch_insert(self, task_id: str, inserts: Dict[int, Message]) -> None:
        state = await self.repository.load(task_id)
        for index, message in inserts.items():
            state.messages.insert(index, message)
        await self.repository.save(task_id, state)

    async def delete_all(self, task_id: str) -> None:
        state = await self.repository.load(task_id)
        state.messages = []
        await self.repository.save(task_id, state)


class ContextService:
    def __init__(self, repository: AgentStateRepository):
        self.repository = repository

    async def get_all(self, task_id: str) -> Dict[str, Any]:
        state = await self.repository.load(task_id)
        return state.context

    async def get_value(self, task_id: str, key: str) -> Optional[Any]:
        state = await self.repository.load(task_id)
        return state.context.get(key)

    async def batch_get_values(self, task_id: str, keys: List[str]) -> Dict[str, Optional[Any]]:
        state = await self.repository.load(task_id)
        return {key: state.context.get(key) for key in keys}

    async def set_value(self, task_id: str, key: str, value: Any) -> None:
        state = await self.repository.load(task_id)
        state.context[key] = value
        await self.repository.save(task_id, state)

    async def batch_set_value(self, task_id: str, updates: Dict[str, Any]) -> None:
        state = await self.repository.load(task_id)
        for key, value in updates.items():
            state.context[key] = value
        await self.repository.save(task_id, state)

    async def delete_value(self, task_id: str, key: str) -> None:
        state = await self.repository.load(task_id)
        if key in state.context:
            del state.context[key]
        await self.repository.save(task_id, state)

    async def batch_delete_value(self, task_id: str, keys: List[str]) -> None:
        state = await self.repository.load(task_id)
        for key in keys:
            if key in state.context:
                del state.context[key]
        await self.repository.save(task_id, state)

    async def delete_all(self, task_id: str) -> None:
        state = await self.repository.load(task_id)
        state.context = {}
        await self.repository.save(task_id, state)


class AgentStateService:
    def __init__(self, repository: DAgentStateRepository):
        self.repository = repository
        self.messages = MessagesService(repository)
        self.context = ContextService(repository)

    async def set(self, task_id: str, state: AgentState) -> None:
        await self.repository.save(task_id, state)

    async def get(self, task_id: str) -> AgentState:
        return await self.repository.load(task_id)

    async def delete(self, task_id: str) -> None:
        await self.repository.delete(task_id)


DAgentStateService = Annotated[AgentStateService, Depends(AgentStateService)]
