import asyncio
from datetime import timedelta
from typing import List, Optional, Tuple

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.actions import Action
from agentex.domain.entities.agent_spec import AgentSpec
from agentex.domain.entities.agents import Agent, AgentStatus
from agentex.domain.entities.deployment import Deployment, DeploymentStatus
from agentex.domain.entities.job import Job, JobStatus
from agentex.domain.entities.service import Service
from agentex.domain.exceptions import ServiceError
from agentex.domain.services.agents.agent_service import DAgentService
from agentex.domain.workflows.services.hosted_actions_service import build_and_push_agent, \
    create_hosted_actions_deployment, create_hosted_actions_service, poll_service_for_agent_spec, \
    start_hosted_actions_server
from agentex.utils.ids import orm_id, short_id
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class CreateAgentWorkflowParams(BaseModel):
    agent: Agent
    agent_tar_path: str


class UpdateAgentWithBuildInfoParams(BaseModel):
    agent: Agent
    job: Job


class BuildAgentParams(BaseModel):
    name: str
    version: str
    zip_file_path: str


class UpdateAgentStatusParams(BaseModel):
    agent: Agent
    status: AgentStatus
    reason: Optional[str] = None


class CreateAgentActions(BaseModel):
    agent: Agent
    actions: List[Action]


class CreateAgentActionDeploymentParams(BaseModel):
    name: str
    image: str
    action_service_port: int
    replicas: int = 1


class CreateAgentActionServiceParams(BaseModel):
    name: str
    action_service_port: int


class CallAgentActionServiceParams(BaseModel):
    name: str
    port: int
    method: str = "GET"
    payload: Optional[dict] = None


class CreateAgentActivities:

    def __init__(
        self,
        agent_service: DAgentService,
        environment_variables: DEnvironmentVariables,
    ):
        self.agent_service = agent_service
        self.build_contexts_path = environment_variables.BUILD_CONTEXTS_PATH

    @activity.defn(name="create_actions")
    async def create_actions(
        self,
        params: CreateAgentActions,
    ) -> Tuple[Agent, List[Action]]:
        agent = params.agent
        actions = params.actions

        return await self.agent_service.create_actions(
            agent=agent,
            actions=actions,
        )

    @activity.defn(name="update_agent")
    async def update_agent(
        self,
        agent: Agent,
    ) -> Agent:
        return await self.agent_service.update_agent(agent=agent)

    @activity.defn(name="update_agent_status")
    async def update_agent_status(
        self,
        params: UpdateAgentStatusParams,
    ) -> Agent:
        agent = params.agent

        agent.status = params.status
        agent.status_reason = params.reason
        return await self.agent_service.update_agent(
            agent=agent,
        )


@workflow.defn
class CreateAgentWorkflow:

    @workflow.run
    async def run(self, params: CreateAgentWorkflowParams):
        agent = params.agent
        agent_id = params.agent.id
        agent_name = params.agent.name
        agent_description = params.agent.description
        agent_version = params.agent.version
        action_service_port = params.agent.action_service_port

        agent_tar_path = params.agent_tar_path

        # try:
        # Build the agent image and push it to the registry
        image_url, job = await build_and_push_agent(
            agent_name=agent_name,
            agent_version=agent_version,
            agent_tar_path=agent_tar_path,
        )

        # Create the agent deployment and service to fetch the agent spec
        hosted_actions_service = await start_hosted_actions_server(agent=agent)
        agent_spec = hosted_actions_service.agent_spec

        # Create the agent and actions
        agent = Agent(
            id=agent_id,
            docker_image=image_url,
            name=agent_name,
            description=agent_description,
            version=agent_version,
            model=agent_spec.model,
            instructions=agent_spec.instructions,
            action_service_port=action_service_port,
            status=AgentStatus.IDLE,
            status_reason="Agent built, but idle until it receives a task.",
            build_job_name=job.name,
            build_job_namespace=job.namespace,
        )

        agent = await workflow.execute_activity(
            activity="update_agent",
            arg=agent,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        workflow.logger.info(f"Agent updated: {agent}")

        actions = [
            Action(
                id=orm_id(),
                name=action_spec.name,
                description=action_spec.description,
                parameters=action_spec.parameters,
                test_payload=action_spec.test_payload,
                version=action_spec.version,
            )
            for action_spec in agent_spec.actions
        ]

        # Create actions now that the build was successful
        actions = await workflow.execute_activity(
            activity="create_actions",
            arg=CreateAgentActions(
                agent=agent,
                actions=actions,
            ),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        workflow.logger.info(f"Actions created: {actions}")

        return agent
        # except Exception as error:
        #     logger.error(f"Error creating agent: {error}")
        #
        #     # Set the agent status to failed
        #     await workflow.execute_activity(
        #         activity="update_agent_status",
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
