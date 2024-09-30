import asyncio
import json
from datetime import timedelta
from typing import Dict, Any

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from agentex.adapters.llm.port import DLLMGateway
from agentex.domain.agents.agent_state_service import DAgentStateService
from agentex.domain.entities.agent_config import AgentConfig
from agentex.domain.entities.messages import ToolCall
from agentex.domain.entities.tasks import Task
from agentex.utils.model_utils import BaseModel


class DecideActionParams(BaseModel):
    task_id: str
    agent_config: AgentConfig


class TakeActionParams(BaseModel):
    task_id: str
    tool_name: str
    tool_args: Dict[str, Any]


class AgentActivities:

    def __init__(
        self,
        agent_state_service: DAgentStateService,
        llm_gateway: DLLMGateway,
    ):
        self.agent_state = agent_state_service
        self.llm = llm_gateway

    @activity.defn(name="decide_action")
    async def decide_action(self, params: DecideActionParams):
        task_id = params.task_id
        agent_config = params.agent_config

        state = await self.agent_state.get(task_id)
        response = await self.llm.acompletion(
            **agent_config.dict(),
            messages=state.messages,
        )
        decision_response = response.choices[0]
        await self.agent_state.messages.append(decision_response.message)
        return decision_response

    @activity.defn(name="take_action")
    async def take_action(self, params: TakeActionParams):
        task_id = params.task_id
        tool_name = params.tool_name
        tool_args = params.tool_args
        state = await self.agent_state.get(task_id)
        # Fetch tools from registry
        # Implement tool logic here
        dummy_tool = lambda x: {"result": f"Executed {tool_name} successfully"}
        tool_response = dummy_tool(tool_args)
        await self.agent_state.messages.append(ToolCall(
            tool_call_id=params.tool_call_id,
            role="tool",
            name=params.tool_name,
            content=tool_response,
        ))
        return tool_response


@workflow.defn
class AgentWorkflow:

    @workflow.run
    async def run(self, task: Task, agent_config: AgentConfig):
        content = None
        finish_reason = None
        while finish_reason not in ("stop", "length", "content_filter"):
            # Execute decision activity
            decision_response = await workflow.execute_activity(
                activity="decide_action",
                arg=DecideActionParams(
                    task_id=task.id,
                    agent_config=agent_config,
                ),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=5),
            )
            finish_reason = decision_response.finish_reason
            decision = decision_response.message
            tool_calls = decision.tool_calls

            if decision.content:
                content = decision.content
                break

            # Execute tool activities if requested
            take_action_activities = []
            if decision.tool_calls:
                for tool_call in tool_calls:
                    take_action_activity = asyncio.create_task(
                        workflow.execute_activity(
                            activity="take_action",
                            arg=TakeActionParams(
                                task_id=task.id,
                                tool_name=tool_call.function.name,
                                tool_args=json.loads(tool_call.function.arguments),
                            ),
                            start_to_close_timeout=timedelta(seconds=60),
                            retry_policy=RetryPolicy(maximum_attempts=5),
                        )
                    )
                    take_action_activities.append(take_action_activity)

            # Wait for all tool activities to complete
            await asyncio.gather(*take_action_activities)

        return {"status": "completed", "content": content}
