import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Annotated

from fastapi import Depends, UploadFile

from agentex.adapters.async_runtime.adapter_temporal import DTemporalGateway
from agentex.adapters.async_runtime.port import DuplicateWorkflowPolicy
from agentex.adapters.crud_store.exceptions import ItemDoesNotExist
from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.agents import Agent, AgentStatus
from agentex.domain.services.agents.agent_repository import DAgentRepository
from agentex.domain.workflows.constants import BUILD_AGENT_TASK_QUEUE
from agentex.domain.workflows.create_agent_workflow import BuildAgentWorkflow, BuildAgentWorkflowParams
from agentex.utils.ids import orm_id
from agentex.utils.logging import make_logger
from agentex.utils.timestamp import timestamp

logger = make_logger(__name__)


class AgentsUseCase:

    def __init__(
        self,
        agent_repository: DAgentRepository,
        async_runtime: DTemporalGateway,
        environment_variables: DEnvironmentVariables,
    ):
        self.agent_repo = agent_repository
        self.async_runtime = async_runtime
        self.build_contexts_path = environment_variables.BUILD_CONTEXTS_PATH
        self.task_queue = BUILD_AGENT_TASK_QUEUE

    async def create(
        self,
        agent_package: UploadFile,
        name: str,
        description: str,
        workflow_name: str,
        workflow_queue_name: str,
        update_if_exists: bool = True,
    ) -> Agent:

        # Create a temporary directory in the self.build_contexts_path directory
        # You must put the temporary directory in the build_contexts_path directory, otherwise
        # the builder job will not be able to access the files
        with tempfile.TemporaryDirectory(dir=self.build_contexts_path, delete=False) as temp_dir:
            # Save the uploaded zip file locally
            file_location = Path(temp_dir) / agent_package.filename

            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(agent_package.file, buffer)

            try:
                agent = await self.agent_repo.get(name=name)
            except ItemDoesNotExist:
                agent = Agent(
                    id=orm_id(),
                    name=name,
                    description=description,
                    status=AgentStatus.PENDING,
                    status_reason="Request to create agent received. Waiting for build process to start.",
                    build_job_name=None,
                    build_job_namespace=None,
                    workflow_name=workflow_name,
                    workflow_queue_name=workflow_queue_name,
                )

            if update_if_exists:
                agent.status = AgentStatus.PENDING
                agent.status_reason = "Request to create agent received. Waiting for build process to start."
                agent = await self.agent_repo.update(item=agent)
            else:
                agent = await self.agent_repo.create(item=agent)

            await self._start_build_agent_workflow(
                agent=agent,
                agent_tar_path=str(file_location.absolute()),
            )

            logger.info(f"Agent creation process started for: {agent}")

            return agent

    async def _start_build_agent_workflow(
        self,
        agent: Agent,
        agent_tar_path: str,
    ) -> str:
        return await self.async_runtime.start_workflow(
            BuildAgentWorkflow.run,
            BuildAgentWorkflowParams(
                agent_tar_path=agent_tar_path,
                agent=agent,
            ),
            id=agent.id,
            task_queue=self.task_queue,
            duplicate_policy=DuplicateWorkflowPolicy.TERMINATE_IF_RUNNING,
        )

    async def get(self, id: Optional[str], name: Optional[str]) -> Agent:
        return await self.agent_repo.get(id=id, name=name)

    async def update(self, agent: Agent) -> Agent:
        return await self.agent_repo.update(item=agent)

    async def delete(self, id: Optional[str], name: Optional[str]) -> Agent:
        return await self.agent_repo.delete(id=id, name=name)

    async def list(self) -> List[Agent]:
        return await self.agent_repo.list()


DAgentsUseCase = Annotated[AgentsUseCase, Depends(AgentsUseCase)]
