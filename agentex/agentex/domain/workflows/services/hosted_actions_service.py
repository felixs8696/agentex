import asyncio
from datetime import timedelta
from typing import Tuple

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.agent_spec import AgentSpec
from agentex.domain.entities.agents import Agent
from agentex.domain.entities.deployment import Deployment, DeploymentStatus
from agentex.domain.entities.hosted_actions_service import HostedActionsService
from agentex.domain.entities.job import Job, JobStatus
from agentex.domain.entities.service import Service
from agentex.domain.exceptions import ServiceError
from agentex.domain.services.agents.agent_service import DAgentService
from agentex.domain.workflows.create_agent_workflow import BuildAgentParams
from agentex.domain.workflows.services.hosted_actions.workflow_entities import CreateHostedActionsDeploymentParams, \
    CreateHostedActionsServiceParams, CallHostedActionsServiceParams, UpdateAgentStatusParams, BuildHostedActionsParams
from agentex.utils.ids import short_id
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class HostedActionsServiceActivities:

    def __init__(
        self,
        agent_service: DAgentService,
        environment_variables: DEnvironmentVariables,
    ):
        self.agent_service = agent_service
        self.build_contexts_path = environment_variables.BUILD_CONTEXTS_PATH

    @activity.defn(name="build_hosted_actions_service")
    async def build_hosted_actions_service(
        self,
        params: BuildAgentParams,
    ) -> Tuple[str, Job]:
        image = params.name
        tag = params.version

        return await self.agent_service.build_hosted_actions_service(
            image=image,
            tag=tag,
            zip_file_path=params.zip_file_path
        )

    @activity.defn(name="get_build_job")
    async def get_build_job(
        self,
        name: str
    ) -> Job:
        return await self.agent_service.get_build_job(name=name)

    @activity.defn(name="delete_build_job")
    async def delete_build_job(
        self,
        name: str,
    ) -> None:
        await self.agent_service.delete_build_job(name=name)

    @activity.defn(name="create_hosted_actions_deployment")
    async def create_hosted_actions_deployment(
        self,
        params: CreateHostedActionsDeploymentParams,
    ) -> Deployment:
        name = params.name
        image = params.image
        action_service_port = params.action_service_port
        replicas = params.replicas

        return await self.agent_service.create_hosted_actions_deployment(
            name=name,
            image=image,
            action_service_port=action_service_port,
            replicas=replicas,
        )

    @activity.defn(name="create_hosted_actions_service")
    async def create_hosted_actions_service(
        self,
        params: CreateHostedActionsServiceParams,
    ) -> Service:
        name = params.name
        action_service_port = params.action_service_port

        return await self.agent_service.create_hosted_actions_service(
            name=name,
            action_service_port=action_service_port,
        )

    @activity.defn(name="get_hosted_actions_deployment")
    async def get_hosted_actions_deployment(
        self,
        name: str,
    ) -> Deployment:
        return await self.agent_service.get_hosted_actions_deployment(name=name)

    @activity.defn(name="get_hosted_actions_service")
    async def get_hosted_actions_service(
        self,
        name: str,
    ) -> Service:
        return await self.agent_service.get_hosted_actions_service(name=name)

    @activity.defn(name="call_hosted_actions_service")
    async def call_hosted_actions_service(
        self,
        params: CallHostedActionsServiceParams,
    ) -> AgentSpec:
        name = params.name
        port = params.port
        path = params.path
        method = params.method
        payload = params.payload

        return await self.agent_service.call_hosted_actions_service(
            name=name,
            port=port,
            path=path,
            method=method,
            payload=payload
        )

    @activity.defn(name="delete_hosted_actions_deployment")
    async def delete_hosted_actions_deployment(
        self,
        name: str,
    ) -> None:
        await self.agent_service.delete_hosted_actions_deployment(name=name)

    @activity.defn(name="delete_hosted_actions_service")
    async def delete_hosted_actions_service(
        self,
        name: str,
    ) -> None:
        await self.agent_service.delete_hosted_actions_service(name=name)

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


async def build_and_push_agent(
    agent_name: str,
    agent_version: str,
    agent_tar_path: str,
) -> Tuple[str, Job]:
    # Start the agent build
    image_url, job = await workflow.execute_activity(
        activity="build_hosted_actions_service",
        arg=BuildHostedActionsParams(
            name=agent_name,
            version=agent_version,
            zip_file_path=agent_tar_path,
        ),
        start_to_close_timeout=timedelta(seconds=60),
        retry_policy=RetryPolicy(maximum_attempts=0),  # TODO: Temporarily set to 0. Make this idempotent
    )

    job = Job.from_dict(job)

    workflow.logger.info(f"Agent build started: {job}")

    # Poll the build job until it's complete
    max_retries = 360
    retries = 0
    complete = False
    while retries < max_retries:
        job = await workflow.execute_activity(
            activity="get_build_job",
            arg=job.name,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        job = Job.from_dict(job)

        workflow.logger.info(f"Polling build job '{job.name}' status: {job.status}")

        # Exit polling if job has completed
        if job.status in (JobStatus.RUNNING, JobStatus.PENDING):
            await asyncio.sleep(5)
        elif job.status == JobStatus.SUCCEEDED:
            complete = True
            break
        elif job.status == JobStatus.FAILED:
            raise ServiceError(
                f"Error building agent actions. Build job '{job.name}' failed. "
                f"Please confirm that you can build the agent locally before "
                f"trying again."
            )
        else:
            raise ServiceError(
                f"Error building agent actions. Build job '{job.name}' has an unknown status. "
                f"Please try again."
            )

        retries += 1

    # If the job didn't complete in time, raise an error
    if not complete:
        if job:
            try:
                await workflow.execute_activity(
                    activity="delete_build_job",
                    arg=job.name,
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
            finally:
                raise ServiceError(
                    f"Error building agent's actions: Build job '{job.name}' timed out. Please try again."
                )
        else:
            raise ServiceError(
                f"Error building agent's actions: Build job not found. Please try again."
            )

    workflow.logger.info(f"Agent build complete: {job}")

    return image_url, job


async def create_hosted_actions_deployment(
    name: str,
    image: str,
    action_service_port: int
) -> Deployment:
    deployment = await workflow.execute_activity(
        activity="create_hosted_actions_deployment",
        arg=CreateHostedActionsDeploymentParams(
            name=name,
            image=image,
            action_service_port=action_service_port,
        ),
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=0),
    )

    max_retries = 360
    retries = 0
    complete = False
    while retries < max_retries:
        deployment = await workflow.execute_activity(
            activity="get_hosted_actions_deployment",
            arg=name,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        workflow.logger.info(f"Polling agent action deployment '{deployment.name}' status: {deployment.status}")

        if deployment.status == DeploymentStatus.READY:
            complete = True
            break
        else:
            await asyncio.sleep(5)

        retries += 1

    if not complete:
        if deployment:
            try:
                await workflow.execute_activity(
                    activity="delete_hosted_actions_deployment",
                    arg=deployment.name,
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
            finally:
                raise ServiceError(
                    f"Error creating agent action deployment: "
                    f"Deployment '{deployment.name}' timed out. Please try again."
                )
        else:
            raise ServiceError(
                f"Error creating agent action deployment: "
                f"Deployment not found. Please try again."
            )

    workflow.logger.info(f"Agent action deployment created: {deployment}")

    return deployment


async def create_hosted_actions_service(
    name: str,
    action_service_port: int,
) -> Service:
    service = await workflow.execute_activity(
        activity="create_hosted_actions_service",
        arg=CreateHostedActionsServiceParams(
            name=name,
            action_service_port=action_service_port,
        ),
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=0),
    )

    max_retries = 360
    retries = 0
    complete = False
    while retries < max_retries:
        service = await workflow.execute_activity(
            activity="get_hosted_actions_service",
            arg=name,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        workflow.logger.info(f"Polling agent action service '{service.name}' status: {service.status}")

        if service:
            complete = True
            break
        else:
            await asyncio.sleep(5)

        retries += 1

    if not complete:
        if service:
            try:
                await workflow.execute_activity(
                    activity="delete_hosted_actions_service",
                    arg=service.name,
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
            finally:
                raise ServiceError(
                    f"Error creating agent action service: "
                    f"Service '{service.name}' timed out. Please try again."
                )
        else:
            raise ServiceError(
                f"Error creating agent action service: "
                f"Service not found. Please try again."
            )

    workflow.logger.info(f"Agent action service created: {service}")

    return service


async def poll_service_for_agent_spec(
    name: str,
    port: int,
) -> AgentSpec:
    max_retries = 360
    retries = 0
    agent_spec = None
    while retries < max_retries:
        agent_spec = await workflow.execute_activity(
            activity="call_hosted_actions_service",
            arg=CallHostedActionsServiceParams(
                name=name,
                port=port,
                path="/",
            ),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        workflow.logger.info(f"Polling agent action service '{name}' status: {agent_spec}")

        if agent_spec:
            break
        else:
            await asyncio.sleep(5)

        retries += 1

    if not agent_spec:
        raise ServiceError(
            f"Error polling agent action service for agent spec: "
            f"Service '{name}' timed out. Please try again."
        )

    return agent_spec


async def start_hosted_actions_server(agent: Agent) -> HostedActionsService:
    # Create the agent deployment and service to fetch the agent spec
    temp_app_name = f"{agent.name}-{short_id()}-build"
    deployment = await create_hosted_actions_deployment(
        name=temp_app_name,
        image=agent.docker_image,
        action_service_port=agent.action_service_port,
    )

    try:
        service = await create_hosted_actions_service(
            name=temp_app_name,
            action_service_port=agent.action_service_port,
        )
    except Exception as error:
        # Clean up the deployment if the service creation fails
        await workflow.execute_activity(
            activity="delete_hosted_actions_deployment",
            arg=deployment.name,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        raise error

    try:
        agent_spec = await poll_service_for_agent_spec(
            name=temp_app_name,
            port=agent.action_service_port,
        )
    except Exception as error:
        # Clean up the deployment and service if the polling fails
        await delete_hosted_actions_server(
            service_name=service.name,
            deployment_name=deployment.name,
        )
        raise error

    return HostedActionsService(
        service_name=service.name,
        service_namespace=service.namespace,
        service_port=agent.action_service_port,
        deployment_name=deployment.name,
        deployment_namespace=service.namespace,
        agent_spec=agent_spec
    )


async def delete_hosted_actions_server(service_name: str, deployment_name: str):
    await workflow.execute_activity(
        activity="delete_hosted_actions_service",
        arg=service_name,
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=3),
    )
    await workflow.execute_activity(
        activity="delete_hosted_actions_deployment",
        arg=deployment_name,
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=3),
    )