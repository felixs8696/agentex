import asyncio
from datetime import timedelta
from typing import List, Dict

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.actions import Action, ActionStatus
from agentex.domain.entities.job import Job, JobStatus
from agentex.domain.exceptions import ServiceError
from agentex.domain.services.agents.action_repository import DActionRepository
from agentex.domain.services.agents.action_service import DActionService
from agentex.domain.services.agents.agent_repository import DAgentRepository
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class CreateActionWorkflowParams(BaseModel):
    action: Action
    agents: List[str]
    action_tar_path: str


class CreateActionParams(BaseModel):
    action: Action
    agents: List[str]


class UpdateActionWithBuildInfoParams(BaseModel):
    action: Action
    job_dict: Dict


class BuildActionParams(BaseModel):
    action: Action
    zip_file_path: str


class UpdateActionStatusParams(BaseModel):
    action: Action
    status: ActionStatus


class CreateActionActivities:

    def __init__(
        self,
        action_repository: DActionRepository,
        agent_repository: DAgentRepository,
        action_service: DActionService,
        environment_variables: DEnvironmentVariables,
    ):
        self.action_repo = action_repository
        self.agent_repo = agent_repository
        self.action_service = action_service
        self.build_contexts_path = environment_variables.BUILD_CONTEXTS_PATH

    @activity.defn(name="create_action")
    async def create_action(self, params: CreateActionParams) -> Action:
        return await self.action_service.create_action(
            action=params.action,
            agents=params.agents
        )

    @activity.defn(name="start_action_build")
    async def build_action(
        self,
        params: BuildActionParams,
    ) -> Dict:
        image = params.action.name
        tag = params.action.version

        job = await self.action_service.build_action(
            image=image,
            tag=tag,
            zip_file_path=params.zip_file_path
        )

        return job.to_dict(mode='json')

    @activity.defn(name="update_action_with_build_info")
    async def update_action_with_build_info(
        self,
        params: UpdateActionWithBuildInfoParams,
    ) -> Action:
        action = params.action
        job_dict = params.job_dict

        job = Job.from_dict(job_dict)

        action.status = ActionStatus.BUILDING
        action.build_job_name = job.name
        action.build_job_namespace = job.namespace
        return await self.action_service.update_action(action=action)

    @activity.defn(name="get_action_build_job")
    async def get_action_build_job(
        self,
        action: Action,
    ) -> Dict:
        job = await self.action_service.get_action_build_job(
            action=action,
        )
        return job.to_dict(mode='json')

    @activity.defn(name="update_action_status")
    async def update_action_status(
        self,
        params: UpdateActionStatusParams,
    ) -> Action:
        action = params.action
        action.status = params.status
        return await self.action_service.update_action(action=action)


@workflow.defn
class CreateActionWorkflow:

    @workflow.run
    async def run(self, params: CreateActionWorkflowParams):
        action = params.action

        # Start the action build
        job_dict = await workflow.execute_activity(
            activity="start_action_build",
            arg=BuildActionParams(
                action=action,
                zip_file_path=params.action_tar_path,
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=0),
        )

        workflow.logger.info(f"Action build started: {job_dict}")

        action = await workflow.execute_activity(
            activity="update_action_with_build_info",
            arg=UpdateActionWithBuildInfoParams(
                action=action,
                job_dict=job_dict,
            ),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        workflow.logger.info(f"Action updated with build info: {action}")

        # Poll the build job until it's complete
        max_retries = 360
        retries = 0
        complete = False
        job = None
        while retries < max_retries:
            job_dict = await workflow.execute_activity(
                activity="get_action_build_job",
                arg=action,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            job = Job.from_dict(job_dict)

            workflow.logger.info(f"Polling build job '{job.name}' status: {job.status}")

            # Exit polling if job has completed
            if job.status in (JobStatus.RUNNING, JobStatus.PENDING):
                await asyncio.sleep(5)
            elif job.status == JobStatus.SUCCEEDED:
                complete = True
                break
            elif job.status == JobStatus.FAILED:
                raise ServiceError(f"Build job '{job.name}' failed")
            else:
                raise ServiceError(f"Build job '{job.name}' has an unknown status")

            retries += 1

        # Update the action status to built
        if complete:
            action = await workflow.execute_activity(
                activity="update_action_status",
                arg=UpdateActionStatusParams(
                    action=action,
                    status=ActionStatus.READY,
                ),
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        else:
            if job:
                raise ServiceError(f"Build job '{job.name}' timed out")
            else:
                raise ServiceError(f"Build job not found")

        return action
