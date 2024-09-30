import pytest
from agentex.domain.entities.messages import SystemMessage, UserMessage, AssistantMessage
from agentex.domain.agent_state.agent_state_repository import AgentStateRepository
from agentex.domain.entities.agent_state import AgentState
from agentex.domain.agent_state.agent_state_service import AgentStateService


@pytest.mark.asyncio
class TestAgentStateService:
    @pytest.fixture(scope="function")
    def agent_state_service(self, mock_memory_repo):
        """Fixture to initialize the AgentStateService with a mocked memory repository."""
        repository = AgentStateRepository(mock_memory_repo)
        return AgentStateService(repository)

    @pytest.fixture(scope="function")
    def sample_agent_state(self):
        """Fixture to return a sample AgentState object."""
        return AgentState(
            messages=[
                SystemMessage(role="system", content="instructions"),
                UserMessage(role="user", content="user message"),
                AssistantMessage(role="assistant", content="assistant message")
            ],
            context={"key": "value"}
        )

    async def test_messages_get_all(self, agent_state_service, sample_agent_state):
        task_id = "task_1"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        messages = await agent_state_service.messages.get_all(task_id)
        assert len(messages) == 3
        assert messages[0].content == "instructions"

    async def test_messages_get_by_index(self, agent_state_service, sample_agent_state):
        task_id = "task_2"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        message = await agent_state_service.messages.get_by_index(task_id, 1)
        assert message.content == "user message"

        # Test out-of-bounds index
        message = await agent_state_service.messages.get_by_index(task_id, 5)
        assert message is None

    async def test_messages_batch_get_by_indices(self, agent_state_service, sample_agent_state):
        task_id = "task_3"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        messages = await agent_state_service.messages.batch_get_by_indices(task_id, [0, 2, 5])
        assert messages[0].content == "instructions"
        assert messages[1].content == "assistant message"
        assert messages[2] is None  # Out of bounds

    async def test_messages_append(self, agent_state_service, sample_agent_state):
        task_id = "task_4"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        new_message = UserMessage(role="user", content="new user message")
        await agent_state_service.messages.append(task_id, new_message)

        updated_state = await agent_state_service.repository.load(task_id)
        assert len(updated_state.messages) == 4
        assert updated_state.messages[-1].content == "new user message"

    async def test_messages_batch_append(self, agent_state_service, sample_agent_state):
        task_id = "task_5"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        new_messages = [
            UserMessage(role="user", content="message 1"),
            AssistantMessage(role="assistant", content="message 2"),
        ]
        await agent_state_service.messages.batch_append(task_id, new_messages)

        updated_state = await agent_state_service.repository.load(task_id)
        assert len(updated_state.messages) == 5
        assert updated_state.messages[-1].content == "message 2"

    async def test_messages_override(self, agent_state_service, sample_agent_state):
        task_id = "task_6"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        new_message = UserMessage(role="user", content="overridden message")
        await agent_state_service.messages.override(task_id, 1, new_message)

        updated_state = await agent_state_service.repository.load(task_id)
        assert updated_state.messages[1].content == "overridden message"

        # Test out-of-bounds index
        await agent_state_service.messages.override(task_id, 5, new_message)  # Should not raise an error

    async def test_messages_batch_override(self, agent_state_service, sample_agent_state):
        task_id = "task_7"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        updates = {
            0: UserMessage(role="user", content="first overridden message"),
            2: AssistantMessage(role="assistant", content="second overridden message"),
        }
        await agent_state_service.messages.batch_override(task_id, updates)

        updated_state = await agent_state_service.repository.load(task_id)
        assert updated_state.messages[0].content == "first overridden message"
        assert updated_state.messages[2].content == "second overridden message"

    async def test_messages_insert(self, agent_state_service, sample_agent_state):
        task_id = "task_8"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        new_message = UserMessage(role="user", content="inserted message")
        await agent_state_service.messages.insert(task_id, 1, new_message)

        updated_state = await agent_state_service.repository.load(task_id)
        assert updated_state.messages[1].content == "inserted message"
        assert updated_state.messages[2].content == "user message"

    async def test_messages_batch_insert(self, agent_state_service, sample_agent_state):
        task_id = "task_9"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        inserts = {
            0: UserMessage(role="user", content="first inserted message"),
            2: AssistantMessage(role="assistant", content="second inserted message"),
        }
        await agent_state_service.messages.batch_insert(task_id, inserts)

        updated_state = await agent_state_service.repository.load(task_id)
        assert updated_state.messages[0].content == "first inserted message"
        assert updated_state.messages[2].content == "second inserted message"

    async def test_messages_delete_all(self, agent_state_service, sample_agent_state):
        task_id = "task_10"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        await agent_state_service.messages.delete_all(task_id)

        updated_state = await agent_state_service.repository.load(task_id)
        assert updated_state.messages == []

    async def test_context_get_all(self, agent_state_service, sample_agent_state):
        task_id = "task_11"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        context = await agent_state_service.context.get_all(task_id)
        assert context == sample_agent_state.context

    async def test_context_get_value(self, agent_state_service, sample_agent_state):
        task_id = "task_12"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        value = await agent_state_service.context.get_value(task_id, "key")
        assert value == "value"

        # Test missing key
        value = await agent_state_service.context.get_value(task_id, "missing_key")
        assert value is None

    async def test_context_batch_get_values(self, agent_state_service, sample_agent_state):
        task_id = "task_13"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        keys = ["key", "missing_key"]
        values = await agent_state_service.context.batch_get_values(task_id, keys)
        assert values["key"] == "value"
        assert values["missing_key"] is None

    async def test_context_set_value(self, agent_state_service, sample_agent_state):
        task_id = "task_14"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        await agent_state_service.context.set_value(task_id, "new_key", "new_value")

        updated_state = await agent_state_service.repository.load(task_id)
        assert updated_state.context["new_key"] == "new_value"

    async def test_context_batch_set_value(self, agent_state_service, sample_agent_state):
        task_id = "task_15"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        updates = {"new_key": "new_value", "another_key": "another_value"}
        await agent_state_service.context.batch_set_value(task_id, updates)

        updated_state = await agent_state_service.repository.load(task_id)
        assert updated_state.context["new_key"] == "new_value"
        assert updated_state.context["another_key"] == "another_value"

    async def test_context_delete_value(self, agent_state_service, sample_agent_state):
        task_id = "task_16"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        await agent_state_service.context.delete_value(task_id, "key")

        updated_state = await agent_state_service.repository.load(task_id)
        assert "key" not in updated_state.context

    async def test_context_batch_delete_value(self, agent_state_service, sample_agent_state):
        task_id = "task_17"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        await agent_state_service.context.batch_delete_value(task_id, ["key", "missing_key"])

        updated_state = await agent_state_service.repository.load(task_id)
        assert "key" not in updated_state.context

    async def test_state_set(self, agent_state_service, sample_agent_state):
        task_id = "task_18"
        await agent_state_service.set(task_id, sample_agent_state)

        state = await agent_state_service.repository.load(task_id)
        assert state.messages == sample_agent_state.messages
        assert state.context == sample_agent_state.context

    async def test_state_get(self, agent_state_service, sample_agent_state):
        task_id = "task_19"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        state = await agent_state_service.get(task_id)

        assert state.messages == sample_agent_state.messages
        assert state.context == sample_agent_state.context

    async def test_state_delete(self, agent_state_service, sample_agent_state):
        task_id = "task_20"
        await agent_state_service.repository.save(task_id, sample_agent_state)
        await agent_state_service.delete(task_id)

        state = await agent_state_service.repository.load(task_id)
        assert state.messages == []
        assert state.context == {}
