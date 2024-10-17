import asyncio
import json
from datetime import timedelta
from typing import Dict, Any, Optional

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from agentex.adapters.llm.port import DLLMGateway
from agentex.domain.entities.agent_config import LLMConfig
from agentex.domain.entities.agents import Agent
from agentex.domain.entities.hosted_actions_service import HostedActionsService
from agentex.domain.entities.messages import UserMessage, LLMChoice, ToolMessage, SystemMessage
from agentex.domain.entities.tasks import Task
from agentex.domain.services.agents.agent_service import DAgentService
from agentex.domain.services.agents.agent_state_service import DAgentStateService
from agentex.domain.workflows.services.hosted_actions_service import start_hosted_actions_server, \
    delete_hosted_actions_server, mark_agent_as_active, mark_agent_as_idle
from agentex.domain.workflows.utils.activities import execute_workflow_activity
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class InitTaskStateParams(BaseModel):
    task: Task
    agent: Agent


class DecideActionParams(BaseModel):
    task: Task
    agent: Agent
    hosted_actions_service: HostedActionsService


class TakeActionParams(BaseModel):
    task: Task
    hosted_actions_service: HostedActionsService
    tool_call_id: str
    tool_name: str
    tool_args: Dict[str, Any]


class AgentTaskActivities:

    def __init__(
        self,
        agent_service: DAgentService,
        agent_state_service: DAgentStateService,
        llm_gateway: DLLMGateway,
    ):
        self.agent_service = agent_service
        self.agent_state = agent_state_service
        self.llm = llm_gateway

    @activity.defn(name="init_task_state")
    async def init_task_state(self, params: InitTaskStateParams) -> bool:
        task = params.task
        agent = params.agent
        await self.agent_state.messages.batch_append(
            task_id=task.id,
            messages=[
                SystemMessage(content=agent.instructions),
                UserMessage(content=task.prompt)
            ]
        )
        return True

    @activity.defn(name="decide_action")
    async def decide_action(self, params: DecideActionParams) -> LLMChoice:
        task = params.task
        hosted_actions_service = params.hosted_actions_service
        agent_spec = hosted_actions_service.agent_spec

        state = await self.agent_state.get(task.id)
        completion_args = LLMConfig(
            model=agent_spec.model,
            messages=state.messages,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": action.schema.name,
                        "description": action.schema.description,
                        "parameters": action.schema.parameters,
                    }
                }
                for action in agent_spec.actions
            ]
        )
        decision_response = await self.llm.acompletion(**completion_args.to_dict())
        await self.agent_state.messages.append(
            task_id=task.id,
            message=decision_response.message
        )
        return decision_response

    @activity.defn(name="take_action")
    async def take_action(self, params: TakeActionParams) -> Optional[Dict]:
        task = params.task
        hosted_actions_service = params.hosted_actions_service
        tool_call_id = params.tool_call_id
        tool_name = params.tool_name
        tool_args = params.tool_args

        tool_response = await self.agent_service.call_hosted_actions_service(
            name=hosted_actions_service.service_name,
            path=f"/{tool_name}",
            method="POST",
            payload=tool_args
        )
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
    agent: Agent


@workflow.defn
class AgentTaskWorkflow:

    @workflow.run
    async def run(self, params: AgentTaskWorkflowParams):
        task = params.task
        agent = params.agent

        # Give the agent the initial task
        success = await execute_workflow_activity(
            activity_name="init_task_state",
            arg=InitTaskStateParams(
                task=task,
                agent=agent,
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=5),
        )
        logger.info(f"Task state initialized: {success}")

        # Start up the action server
        hosted_actions_service = await start_hosted_actions_server(agent=agent)

        # Set the agent status to ACTIVE
        await mark_agent_as_active(agent=agent)

        content = None
        finish_reason = None
        while finish_reason not in ("stop", "length", "content_filter"):
            # Execute decision activity
            decision_response = await execute_workflow_activity(
                activity_name="decide_action",
                arg=DecideActionParams(
                    task=task,
                    agent=agent,
                    hosted_actions_service=hosted_actions_service,
                ),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=5),
                response_model=LLMChoice,
            )
            finish_reason = decision_response.finish_reason
            decision = decision_response.message
            tool_calls = decision.tool_calls
            content = decision.content

            # Execute tool activities if requested
            take_action_activities = []
            if decision.tool_calls:
                for tool_call in tool_calls:
                    take_action_activity = asyncio.create_task(
                        execute_workflow_activity(
                            activity_name="take_action",
                            arg=TakeActionParams(
                                task=task,
                                hosted_actions_service=hosted_actions_service,
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

        # Set the agent status to IDLE
        await mark_agent_as_idle(agent=agent)

        # When finished, delete the hosted action server. It will get recreated when the next task
        # is submitted
        # TODO: Don't outright delete this, schedule it for deletion, that way if the next task is requested
        #   in short succession, this doesn't get cleaned up.
        #   Also, allow for the server to be configured to be persistent if the user desired warm execution times.
        await delete_hosted_actions_server(
            service_name=hosted_actions_service.service_name,
            deployment_name=hosted_actions_service.deployment_name,
        )

        return {"status": "completed", "content": content}
