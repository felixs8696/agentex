import pytest

from agentex.adapters.llm.entities import SystemMessage, UserMessage, AssistantMessage
from agentex.domain.agent_state.agent_state_repository import AgentStateRepository
from agentex.domain.agent_state.entities import AgentState


@pytest.mark.asyncio
class TestAgentStateRepository:

    @pytest.fixture(scope="function")
    def agent_state_repository(self, mock_memory_repo):
        """Fixture to initialize the AgentStateRepository with a mocked memory repository."""
        return AgentStateRepository(mock_memory_repo)

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

    async def test_save_load_agent_state(
        self,
        agent_state_repository: AgentStateRepository,
        sample_agent_state: AgentState,
    ):
        """Test saving, loading, and deleting the agent state."""
        task_id = "task_123"

        # Save
        await agent_state_repository.save(task_id, sample_agent_state)

        # Load
        fetched_state = await agent_state_repository.load(task_id)

        # Assert
        assert fetched_state.messages == sample_agent_state.messages
        assert fetched_state.context == sample_agent_state.context
        assert isinstance(fetched_state.messages[0], SystemMessage)
        assert isinstance(fetched_state.messages[1], UserMessage)
        assert isinstance(fetched_state.messages[2], AssistantMessage)

        # Delete
        await agent_state_repository.delete(task_id)

        # Assert
        loaded_state = await agent_state_repository.load(task_id)

        assert loaded_state.messages == []
        assert loaded_state.context == {}

    async def test_load_empty_state(
        self,
        agent_state_repository: AgentStateRepository,
    ):
        """Test loading when no state exists (None returned)."""
        task_id = "task_456"

        # Act
        loaded_state = await agent_state_repository.load(task_id)

        # Assert
        assert loaded_state.messages == []
        assert loaded_state.context == {}
