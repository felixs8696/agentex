from datetime import timedelta

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.agents import Agent, AgentStatus
from agentex.domain.services.agents.agent_service import DAgentService
from agentex.domain.workflows.services.hosted_actions_service import build_and_push_agent, \
    start_hosted_actions_server, validate_hosted_actions_server_with_test_payloads, delete_hosted_actions_server
from agentex.domain.workflows.utils.activities import execute_workflow_activity
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class CreateAgentWorkflowParams(BaseModel):
    agent: Agent
    agent_tar_path: str


class CreateAgentActivities:

    def __init__(
        self,
        agent_service: DAgentService,
        environment_variables: DEnvironmentVariables,
    ):
        self.agent_service = agent_service
        self.build_contexts_path = environment_variables.BUILD_CONTEXTS_PATH

    @activity.defn(name="update_agent")
    async def update_agent(
        self,
        agent: Agent,
    ) -> Agent:
        return await self.agent_service.update_agent(agent=agent)


@workflow.defn
class CreateAgentWorkflow:

    @workflow.run
    async def run(self, params: CreateAgentWorkflowParams):
        agent = params.agent
        agent_name = params.agent.name
        agent_version = params.agent.version

        agent_tar_path = params.agent_tar_path

        agent.status = AgentStatus.BUILDING
        agent.status_reason = "Agent is building its actions."
        agent = await _update_agent(agent)

        # try:
        # Build the agent image and push it to the registry
        image_url, job = await build_and_push_agent(
            agent_name=agent_name,
            agent_version=agent_version,
            agent_tar_path=agent_tar_path,
        )

        agent.docker_image = image_url
        agent.build_job_name = job.name
        agent.build_job_namespace = job.namespace
        agent = await _update_agent(agent)

        # Create the agent deployment and service to fetch the agent spec
        hosted_actions_service = await start_hosted_actions_server(agent=agent)
        agent_spec = hosted_actions_service.agent_spec

        agent.instructions = agent_spec.instructions
        agent.model = agent_spec.model
        agent.actions = agent_spec.actions
        agent.status = AgentStatus.IDLE
        agent.status_reason = "Agent built and ready to receive tasks."
        agent = await _update_agent(agent)

        await validate_hosted_actions_server_with_test_payloads(
            service_name=hosted_actions_service.service_name,
            actions=agent.actions,
        )

        workflow.logger.info("Agent actions validated with test payloads.")

        await delete_hosted_actions_server(
            service_name=hosted_actions_service.service_name,
            deployment_name=hosted_actions_service.deployment_name,
        )

        workflow.logger.info("Agent actions service cleaned up.")

        workflow.logger.info(f"Agent fully built and ready to receive tasks: {agent}")

        return agent
        # except Exception as error:
        #     logger.error(f"Error creating agent: {error}")
        #
        #     # Set the agent status to failed
        #     await execute_workflow_activity(
        #         activity_name="update_agent_status",
        #         arg=UpdateAgentStatusParams(
        #             agent=agent,
        #             status=AgentStatus.FAILED,
        #             reason=str(error),
        #         ),
        #         start_to_close_timeout=timedelta(seconds=10),
        #         retry_policy=RetryPolicy(maximum_attempts=3),
        #     )
        #
        #     raise error


async def _update_agent(agent: Agent) -> Agent:
    agent = await execute_workflow_activity(
        activity_name="update_agent",
        arg=agent,
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=3),
        response_model=Agent,
    )
    workflow.logger.info(f"Agent updated: {agent}")
    return agent
