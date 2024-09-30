import asyncio
import json
from datetime import timedelta
from typing import Dict, Any

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from agentex.adapters.llm.port import DLLMGateway
from agentex.domain.entities.agent_config import AgentConfig
from agentex.domain.entities.messages import UserMessage, LLMChoice, ToolMessage
from agentex.domain.entities.tasks import Task
from agentex.domain.services.agents.agent_state_service import DAgentStateService
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class InitTaskStateParams(BaseModel):
    task: Task
    agent_config: AgentConfig


class DecideActionParams(BaseModel):
    task: Task
    agent_config: AgentConfig


class TakeActionParams(BaseModel):
    task: Task
    tool_call_id: str
    tool_name: str
    tool_args: Dict[str, Any]


class AgentTaskActivities:

    def __init__(
        self,
        agent_state_service: DAgentStateService,
        llm_gateway: DLLMGateway,
    ):
        self.agent_state = agent_state_service
        self.llm = llm_gateway

    @activity.defn(name="init_task_state")
    async def init_task_state(self, params: InitTaskStateParams) -> bool:
        task = params.task
        await self.agent_state.messages.batch_append(
            task_id=task.id,
            messages=[
                UserMessage(content=task.prompt)
            ]
        )
        return True

    @activity.defn(name="decide_action")
    async def decide_action(self, params: DecideActionParams) -> LLMChoice:
        task = params.task
        agent_config = params.agent_config

        state = await self.agent_state.get(task.id)
        completion_args = {
            **agent_config.llm_config.to_dict(
                exclude_unset=True,
                exclude_none=True,
            ),
            "messages": state.messages,  # override existing messages
        }
        decision_response = await self.llm.acompletion(**completion_args)
        await self.agent_state.messages.append(
            task_id=task.id,
            message=decision_response.message
        )
        return decision_response

    @activity.defn(name="take_action")
    async def take_action(self, params: TakeActionParams):
        task = params.task
        tool_name = params.tool_name
        tool_args = params.tool_args
        tool_call_id = params.tool_call_id
        state = await self.agent_state.get(task.id)
        # Fetch tools from registry
        # Implement tool logic here
        get_weather = lambda x: {"results": "The weather is cloudy, windy, and rainy. Typhoon Krathon is imminent. Take cover."}
        dummy_tool = lambda x: {"result": f"{tool_name} was executed, but is undefined."}
        if tool_name == 'get_current_weather':
            tool = get_weather
        else:
            tool = dummy_tool
        tool_response = tool(tool_args)
        try:
            tool_call_message = ToolMessage(
                content=json.dumps(tool_response),
                tool_call_id=tool_call_id,
                name=tool_name,
            )
        except Exception as e:
            raise Exception(f"Error creating tool call message: {e}, Params: {params}")
        await self.agent_state.messages.append(
            task_id=task.id,
            message=tool_call_message
        )
        return tool_response


class AgentTaskWorkflowParams(BaseModel):
    task: Task
    agent_config: AgentConfig


@workflow.defn
class AgentTaskWorkflow:

    @workflow.run
    async def run(self, params: AgentTaskWorkflowParams):
        task = params.task
        agent_config = params.agent_config

        success = await workflow.execute_activity(
            activity="init_task_state",
            arg=InitTaskStateParams(
                task=task,
                agent_config=agent_config,
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=5),
        )
        logger.info(f"Task state initialized: {success}")

        content = None
        finish_reason = None
        while finish_reason not in ("stop", "length", "content_filter"):
            # Execute decision activity
            decision_response_dict = await workflow.execute_activity(
                activity="decide_action",
                arg=DecideActionParams(
                    task=task,
                    agent_config=agent_config,
                ),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=5),
            )
            decision_response = LLMChoice.from_dict(decision_response_dict)
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
                                task=task,
                                tool_call_id=tool_call.id,
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
