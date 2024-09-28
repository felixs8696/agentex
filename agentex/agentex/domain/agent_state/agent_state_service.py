from typing import List, Dict, Any, Optional

from agentex.adapters.llm.entities import Message
from agentex.domain.agent_state.agent_state_repository import AgentStateRepository
from agentex.domain.agent_state.entities import AgentState


class AgentStateService:
    def __init__(self, repository: AgentStateRepository):
        self.repository = repository

    # -------------------------
    # Messages Operations
    # -------------------------

    async def messages_get_all(self, task_id: str) -> List[Message]:
        """Retrieve all messages in the agent's state."""
        state = await self.repository.load(task_id)
        return state.messages

    async def messages_get_by_index(self, task_id: str, index: int) -> Optional[Message]:
        """Retrieve a message by its index in the messages array."""
        state = await self.repository.load(task_id)
        if 0 <= index < len(state.messages):
            return state.messages[index]
        return None

    async def messages_batch_get_by_indices(self, task_id: str, indices: List[int]) -> List[Optional[Message]]:
        """Retrieve multiple messages by their indices."""
        state = await self.repository.load(task_id)
        return [state.messages[i] if 0 <= i < len(state.messages) else None for i in indices]

    async def messages_append(self, task_id: str, message: Message) -> None:
        """Append a message to the agent's messages array."""
        state = await self.repository.load(task_id)
        state.messages.append(message)
        await self.repository.save(task_id, state)

    async def messages_batch_append(self, task_id: str, messages: List[Message]) -> None:
        """Append multiple messages to the agent's messages array."""
        state = await self.repository.load(task_id)
        state.messages.extend(messages)
        await self.repository.save(task_id, state)

    async def messages_override(self, task_id: str, index: int, message: Message) -> None:
        """Override a message at the specified index in the messages array."""
        state = await self.repository.load(task_id)
        if 0 <= index < len(state.messages):
            state.messages[index] = message
            await self.repository.save(task_id, state)

    async def messages_batch_override(self, task_id: str, updates: Dict[int, str]) -> None:
        """Override multiple messages at specified indices."""
        state = await self.repository.load(task_id)
        for index, message in updates.items():
            if 0 <= index < len(state.messages):
                state.messages[index] = message
        await self.repository.save(task_id, state)

    async def messages_insert(self, task_id: str, index: int, message: Message) -> None:
        """Insert a message at the specified index in the messages array."""
        state = await self.repository.load(task_id)
        state.messages.insert(index, message)
        await self.repository.save(task_id, state)

    async def messages_batch_insert(self, task_id: str, inserts: Dict[int, Message]) -> None:
        """Insert multiple messages at specified indices."""
        state = await self.repository.load(task_id)
        for index, message in inserts.items():
            state.messages.insert(index, message)
        await self.repository.save(task_id, state)

    async def messages_delete_all(self, task_id: str) -> None:
        state = await self.repository.load(task_id)
        state.messages = []
        await self.repository.save(task_id, state)

    # -------------------------
    # Context Operations
    # -------------------------

    async def context_get_all(self, task_id: str) -> Dict[str, Any]:
        """Retrieve the entire context."""
        state = await self.repository.load(task_id)
        return state.context

    async def context_get_value(self, task_id: str, key: str) -> Optional[Any]:
        """Retrieve a value from the context by its key."""
        state = await self.repository.load(task_id)
        return state.context.get(key)

    async def context_batch_get_values(self, task_id: str, keys: List[str]) -> Dict[str, Optional[Any]]:
        """Retrieve multiple values from the context by their keys."""
        state = await self.repository.load(task_id)
        return {key: state.context.get(key) for key in keys}

    async def context_set_value(self, task_id: str, key: str, value: Any) -> None:
        """Set a value in the agent's context."""
        state = await self.repository.load(task_id)
        state.context[key] = value
        await self.repository.save(task_id, state)

    async def context_batch_set_value(self, task_id: str, updates: Dict[str, Any]) -> None:
        """Set multiple values in the agent's context."""
        state = await self.repository.load(task_id)
        for key, value in updates.items():
            state.context[key] = value
        await self.repository.save(task_id, state)

    async def context_delete_value(self, task_id: str, key: str) -> None:
        """Delete a key from the agent's context."""
        state = await self.repository.load(task_id)
        if key in state.context:
            del state.context[key]
        await self.repository.save(task_id, state)

    async def context_batch_delete_value(self, task_id: str, keys: List[str]) -> None:
        """Delete multiple keys from the agent's context."""
        state = await self.repository.load(task_id)
        for key in keys:
            if key in state.context:
                del state.context[key]
        await self.repository.save(task_id, state)

    async def context_delete_all(self, task_id: str) -> None:
        state = await self.repository.load(task_id)
        state.context = {}
        await self.repository.save(task_id, state)

    # -------------------------
    # General methods
    # -------------------------

    async def get_state(self, task_id: str) -> AgentState:
        """Retrieve the current agent state."""
        return await self.repository.load(task_id)

    async def delete_state(self, task_id: str) -> None:
        """Delete the agent state associated with the task ID."""
        await self.repository.delete(task_id)
