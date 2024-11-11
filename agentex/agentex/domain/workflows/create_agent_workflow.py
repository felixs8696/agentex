from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from agentex.domain.entities.agents import Agent, AgentStatus
from agentex.domain.workflows.activities.activity_names import AgentActivity
from agentex.domain.workflows.activities.build_agent import build_and_push_agent, start_agent_server
from agentex.domain.workflows.utils.activities import execute_workflow_activity
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class BuildAgentWorkflowParams(BaseModel):
    agent: Agent
    agent_tar_path: str


@workflow.defn
class BuildAgentWorkflow:

    @workflow.run
    async def run(self, params: BuildAgentWorkflowParams):
        agent = params.agent
        agent_name = params.agent.name

        agent_tar_path = params.agent_tar_path

        agent.status = AgentStatus.BUILDING
        agent.status_reason = "Agent is building its actions."
        agent = await _update_agent(agent)

        # try:
        # Build the agent image and push it to the registry
        image_url, job = await build_and_push_agent(
            agent_name=agent_name,
            agent_tar_path=agent_tar_path,
        )

        agent.docker_image = image_url
        agent.build_job_name = job.name
        agent.build_job_namespace = job.namespace
        agent = await _update_agent(agent)

        # Create the agent deployment and service to fetch the agent spec
        await start_agent_server(agent=agent)

        agent.status = AgentStatus.READY
        agent.status_reason = "Agent built and ready to receive tasks."
        agent = await _update_agent(agent)

        workflow.logger.info(f"Agent fully built and ready to receive tasks: {agent}")

        return agent


async def _update_agent(agent: Agent) -> Agent:
    agent = await execute_workflow_activity(
        activity_name=AgentActivity.UPDATE_AGENT,
        arg=agent,
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=3),
        response_model=Agent,
    )
    workflow.logger.info(f"Agent updated: {agent}")
    return agent
