import asyncio
from datetime import timedelta
from typing import Tuple, Optional

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.agent_server import AgentServer
from agentex.domain.entities.agents import Agent, AgentStatus
from agentex.domain.entities.deployment import Deployment, DeploymentStatus
from agentex.domain.entities.job import Job, JobStatus
from agentex.domain.entities.service import Service
from agentex.domain.exceptions import ServiceError
from agentex.domain.services.agents.agent_service import DAgentService
from agentex.domain.workflows.activities.activity_names import AgentActivity
from agentex.domain.workflows.utils.activities import execute_workflow_activity
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class BuildAgentImageParams(BaseModel):
    name: str
    zip_file_path: str


class CreateAgentDeploymentParams(BaseModel):
    name: str
    image: str
    replicas: int = 1


class UpdateAgentStatusParams(BaseModel):
    agent: AgentActivity
    status: AgentStatus
    reason: Optional[str] = None


class BuildAgentActivities:

    def __init__(
        self,
        agent_service: DAgentService,
        environment_variables: DEnvironmentVariables,
    ):
        self.agent_service = agent_service
        self.build_contexts_path = environment_variables.BUILD_CONTEXTS_PATH

    @activity.defn(name=AgentActivity.BUILD_AGENT_IMAGE)
    async def build_agent_image(
        self,
        params: BuildAgentImageParams,
    ) -> Tuple[str, Job]:
        image = params.name
        tag = "latest"
        zip_file_path = params.zip_file_path

        return await self.agent_service.create_build_job(
            image=image,
            tag=tag,
            zip_file_path=zip_file_path
        )

    @activity.defn(name=AgentActivity.GET_BUILD_JOB)
    async def get_build_job(
        self,
        name: str
    ) -> Optional[Job]:
        return await self.agent_service.get_build_job(name=name)

    @activity.defn(name=AgentActivity.DELETE_BUILD_JOB)
    async def delete_build_job(
        self,
        name: str,
    ) -> None:
        await self.agent_service.delete_build_job(name=name)

    @activity.defn(name=AgentActivity.CREATE_AGENT_DEPLOYMENT)
    async def create_agent_deployment(
        self,
        params: CreateAgentDeploymentParams,
    ) -> Deployment:
        name = params.name
        image = params.image
        replicas = params.replicas

        return await self.agent_service.create_agent_deployment(
            name=name,
            image=image,
            replicas=replicas,
        )

    @activity.defn(name=AgentActivity.CREATE_AGENT_SERVICE)
    async def create_agent_service(
        self,
        name: str
    ) -> Service:
        return await self.agent_service.create_agent_service(name=name)

    @activity.defn(name=AgentActivity.CREATE_AGENT_POD_DISRUPTION_BUDGET)
    async def create_agent_pod_disruption_budget(
        self,
        name: str,
    ) -> None:
        await self.agent_service.create_agent_pod_disruption_budget(name=name)

    @activity.defn(name=AgentActivity.GET_AGENT_DEPLOYMENT)
    async def get_agent_deployment(
        self,
        name: str,
    ) -> Optional[Deployment]:
        return await self.agent_service.get_agent_deployment(name=name)

    @activity.defn(name=AgentActivity.GET_AGENT_SERVICE)
    async def get_agent_service(
        self,
        name: str,
    ) -> Optional[Service]:
        return await self.agent_service.get_agent_service(name=name)

    @activity.defn(name=AgentActivity.DELETE_AGENT_DEPLOYMENT)
    async def delete_agent_deployment(
        self,
        name: str,
    ) -> None:
        await self.agent_service.delete_agent_deployment(name=name)

    @activity.defn(name=AgentActivity.DELETE_AGENT_SERVICE)
    async def delete_agent_service(
        self,
        name: str,
    ) -> None:
        await self.agent_service.delete_agent_service(name=name)

    @activity.defn(name=AgentActivity.UPDATE_AGENT_STATUS)
    async def update_agent_status(
        self,
        params: UpdateAgentStatusParams,
    ) -> AgentActivity:
        agent = params.agent

        agent.status = params.status
        agent.status_reason = params.reason
        return await self.agent_service.update_agent(
            agent=agent,
        )

    @activity.defn(name=AgentActivity.UPDATE_AGENT)
    async def update_agent(
        self,
        agent: Agent,
    ) -> Agent:
        return await self.agent_service.update_agent(agent=agent)


async def build_and_push_agent(
    agent_name: str,
    agent_tar_path: str,
) -> Tuple[str, Job]:
    # Start the agent build
    image_url, job = await workflow.execute_activity(
        activity=AgentActivity.BUILD_AGENT_IMAGE,
        arg=BuildAgentImageParams(
            name=agent_name,
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
        job = await execute_workflow_activity(
            activity_name=AgentActivity.GET_BUILD_JOB,
            arg=job.name,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
            response_model=Job,
        )

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
                await execute_workflow_activity(
                    activity_name=AgentActivity.DELETE_BUILD_JOB,
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


async def create_agent_deployment(
    name: str,
    image: str,
) -> Deployment:
    deployment = await execute_workflow_activity(
        activity_name=AgentActivity.CREATE_AGENT_DEPLOYMENT,
        arg=CreateAgentDeploymentParams(
            name=name,
            image=image,
        ),
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=0),
        response_model=Deployment,
    )

    max_retries = 360
    retries = 0
    complete = False
    while retries < max_retries:
        deployment = await execute_workflow_activity(
            activity_name=AgentActivity.GET_AGENT_DEPLOYMENT,
            arg=name,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
            response_model=Deployment,
        )

        workflow.logger.info(f"Polling agent deployment '{deployment.name}' status: {deployment.status}")

        if deployment.status == DeploymentStatus.READY:
            complete = True
            break
        else:
            await asyncio.sleep(5)

        retries += 1

    if not complete and not deployment:
        raise ServiceError(
            f"Error creating agent action deployment: "
            f"Deployment not found. Please try again."
        )

    workflow.logger.info(f"Agent action deployment created: {deployment}")

    return deployment


async def create_agent_service(name: str) -> Service:
    service = await execute_workflow_activity(
        activity_name=AgentActivity.CREATE_AGENT_SERVICE,
        arg=name,
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=0),
        response_model=Service,
    )

    max_retries = 360
    retries = 0
    complete = False
    while retries < max_retries:
        service = await execute_workflow_activity(
            activity_name=AgentActivity.GET_AGENT_SERVICE,
            arg=name,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
            response_model=Service,
        )

        workflow.logger.info(f"Polling agent action service '{service.name}'.")

        if service:
            complete = True
            break
        else:
            await asyncio.sleep(5)

        retries += 1

    if not complete and not service:
        raise ServiceError(
            f"Error creating agent action service: "
            f"Service not found. Please try again."
        )

    workflow.logger.info(f"Agent action service created: {service}")

    return service


async def create_agent_pod_disruption_budget(name: str):
    await execute_workflow_activity(
        activity_name=AgentActivity.CREATE_AGENT_POD_DISRUPTION_BUDGET,
        arg=name,
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=0),
    )


async def start_agent_server(agent: Agent) -> AgentServer:
    # Create the agent deployment and service to fetch the agent spec
    server_name = f"{agent.name}".replace(".", "-").replace("_", "-")
    deployment = await create_agent_deployment(
        name=server_name,
        image=agent.docker_image,
    )

    try:
        service = await create_agent_service(name=server_name)
    except Exception as error:
        # Clean up the deployment if the service creation fails
        await execute_workflow_activity(
            activity_name=AgentActivity.DELETE_AGENT_DEPLOYMENT,
            arg=deployment.name,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        raise error

    await create_agent_pod_disruption_budget(name=server_name)

    return AgentServer(
        service_name=service.name,
        service_namespace=service.namespace,
        service_port=80,
        deployment_name=deployment.name,
        deployment_namespace=service.namespace,
    )


async def delete_agent_server(service_name: str, deployment_name: str):
    await execute_workflow_activity(
        activity_name=AgentActivity.DELETE_AGENT_SERVICE,
        arg=service_name,
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=3),
    )
    await execute_workflow_activity(
        activity_name=AgentActivity.DELETE_AGENT_DEPLOYMENT,
        arg=deployment_name,
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(maximum_attempts=3),
    )
