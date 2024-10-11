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

    @activity.defn(name="build_agent_action_service")
    async def build_agent_action_service(
        self,
        params: BuildAgentParams,
    ) -> Tuple[str, Job]:
        image = params.name
        tag = params.version

        return await self.agent_service.build_agent_action_service(
            image=image,
            tag=tag,
            zip_file_path=params.zip_file_path
        )

    @activity.defn(name="create_agent_action_deployment")
    async def create_agent_action_deployment(
        self,
        params: CreateAgentActionDeploymentParams,
    ) -> Deployment:
        name = params.name
        image = params.image
        action_service_port = params.action_service_port
        replicas = params.replicas

        return await self.agent_service.create_agent_action_deployment(
            name=name,
            image=image,
            action_service_port=action_service_port,
            replicas=replicas,
        )

    @activity.defn(name="create_agent_action_service")
    async def create_agent_action_service(
        self,
        params: CreateAgentActionServiceParams,
    ) -> Service:
        name = params.name
        action_service_port = params.action_service_port

        return await self.agent_service.create_agent_action_service(
            name=name,
            action_service_port=action_service_port,
        )

    @activity.defn(name="get_agent_action_deployment")
    async def get_agent_action_deployment(
        self,
        name: str,
    ) -> Deployment:
        return await self.agent_service.get_agent_action_deployment(name=name)

    @activity.defn(name="get_agent_action_service")
    async def get_agent_action_service(
        self,
        name: str,
    ) -> Service:
        return await self.agent_service.get_agent_action_service(name=name)

    @activity.defn(name="call_agent_action_service")
    async def call_agent_action_service(
        self,
        params: CallAgentActionServiceParams,
    ) -> AgentSpec:
        name = params.name
        port = params.port
        method = params.method
        payload = params.payload

        return await self.agent_service.call_agent_action_service(
            name=name,
            port=port,
            method=method,
            payload=payload
        )

    @activity.defn(name="delete_agent_action_deployment")
    async def delete_agent_action_deployment(
        self,
        name: str,
    ) -> None:
        await self.agent_service.delete_agent_action_deployment(name=name)

    @activity.defn(name="delete_agent_action_service")
    async def delete_agent_action_service(
        self,
        name: str,
    ) -> None:
        await self.agent_service.delete_agent_action_service(name=name)

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
        image_url, job = await self._build_and_push_agent(
            agent_name=agent_name,
            agent_version=agent_version,
            agent_tar_path=agent_tar_path,
        )

        # Create the agent deployment and service to fetch the agent spec
        temp_app_name = f"{agent_name}-{short_id()}-build"
        deployment = await self._create_agent_deployment(
            name=temp_app_name,
            image=image_url,
            action_service_port=action_service_port,
        )

        try:
            service = await self._create_agent_service(
                name=temp_app_name,
                action_service_port=action_service_port,
            )
        except Exception as error:
            # Clean up the deployment if the service creation fails
            await workflow.execute_activity(
                activity="delete_agent_action_deployment",
                arg=deployment.name,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            raise error

        try:
            agent_spec = await self._poll_service_for_agent_spec(
                name=temp_app_name,
                port=action_service_port,
            )
        except Exception as error:
            # Clean up the deployment and service if the polling fails
            await workflow.execute_activity(
                activity="delete_agent_action_deployment",
                arg=deployment.name,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            await workflow.execute_activity(
                activity="delete_agent_action_service",
                arg=service.name,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            raise error

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

    @staticmethod
    async def _build_and_push_agent(
        agent_name: str,
        agent_version: str,
        agent_tar_path: str,
    ) -> Tuple[str, Job]:
        # Start the agent build
        image_url, job = await workflow.execute_activity(
            activity="build_agent_action_service",
            arg=BuildAgentParams(
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

    @staticmethod
    async def _create_agent_deployment(
        name: str,
        image: str,
        action_service_port: int
    ) -> Deployment:
        deployment = await workflow.execute_activity(
            activity="create_agent_action_deployment",
            arg=CreateAgentActionDeploymentParams(
                name=name,
                image=image,
                action_service_port=action_service_port,
            ),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        max_retries = 360
        retries = 0
        complete = False
        while retries < max_retries:
            deployment = await workflow.execute_activity(
                activity="get_agent_action_deployment",
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
                        activity="delete_agent_action_deployment",
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

    @staticmethod
    async def _create_agent_service(
        name: str,
        action_service_port: int,
    ) -> Service:
        service = await workflow.execute_activity(
            activity="create_agent_action_service",
            arg=CreateAgentActionServiceParams(
                name=name,
                action_service_port=action_service_port,
            ),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        max_retries = 360
        retries = 0
        complete = False
        while retries < max_retries:
            service = await workflow.execute_activity(
                activity="get_agent_action_service",
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
                        activity="delete_agent_action_service",
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

    @staticmethod
    async def _poll_service_for_agent_spec(
        name: str,
        port: int,
    ) -> AgentSpec:
        max_retries = 360
        retries = 0
        agent_spec = None
        while retries < max_retries:
            agent_spec = await workflow.execute_activity(
                activity="call_agent_action_service",
                arg=CallAgentActionServiceParams(
                    name=name,
                    port=port,
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
