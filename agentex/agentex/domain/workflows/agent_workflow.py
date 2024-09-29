from temporalio import workflow, activity

from agentex.adapters.llm.port import DLLMGateway
from agentex.adapters.kv_store.port import DMemoryRepository
from agentex.domain.agent_state.agent_state_repository import AgentStateRepository
from agentex.domain.agent_state.agent_state_service import AgentStateService, DAgentStateService
from agentex.domain.entities.agent_config import AgentConfig
from agentex.domain.entities.agent_state import AgentState
from agentex.domain.entities.tasks import Task


class AgentActivities:

    def __init__(
        self,
        agent_state_service: DAgentStateService,
        llm_gateway: DLLMGateway,
    ):
        self.agent_state = agent_state_service
        self.llm = llm_gateway

    @activity.defn
    async def decide_next_action(self, task_id: str, agent_config: AgentConfig):
        state = await self.agent_state.get(task_id)
        return await self.llm.acompletion(
            **agent_config.dict(),
            messages=state.messages,
        )

    @activity.defn
    async def take_action(self, task_id: str, tool_name: str, tool_args: str):
        state = await self.agent_state.get(task_id)
        # Fetch tools from registry
        # Implement tool logic here
        return {"result": f"Executed {tool_name} successfully"}


@workflow.defn
class AgentWorkflow:

    @workflow.run
    async def run(self, task: Task):
        agent_service = AgentStateService(AgentStateRepository(DMemoryRepository()))
        # Initialize agent state
        state = AgentState()  # Replace with actual initialization
        await agent_service.set(task_id, state)

        while True:
            # Execute decision activity
            decision = await workflow.execute_activity(make_decision_activity, task_id, prompt, timeout=60)
            if decision["complete"]:
                break

            # Execute tool activities if requested
            if "tools" in decision:
                for tool in decision["tools"]:
                    await workflow.execute_activity(tool_activity, task_id, tool)

        return {"status": "completed"}


@activity.defn
async def make_decision_activity(task_id: str, prompt: str):
    agent_service = AgentStateService(AgentStateRepository(DMemoryRepository()))
    # Simulate LLM call to make a decision
    state = await agent_service.get_state(task_id)
    # ... implement LLM logic here
    return {"complete": False, "tools": ["tool_1", "tool_2"]}  # Example return


@activity.defn
async def tool_activity(task_id: str, tool_name: str):
    agent_service = AgentStateService(AgentStateRepository(DMemoryRepository()))
    # Implement tool logic here
    return {"result": f"Executed {tool_name} successfully"}
