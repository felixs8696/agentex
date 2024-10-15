import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Annotated

from fastapi import Depends, UploadFile

from agentex.adapters.async_runtime.adapter_temporal import DTemporalGateway
from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.agents import Agent, AgentStatus
from agentex.domain.services.agents.action_repository import DActionRepository
from agentex.domain.services.agents.agent_repository import DAgentRepository
from agentex.domain.workflows.constants import BUILD_AGENT_TASK_QUEUE
from agentex.domain.workflows.create_agent_workflow import CreateAgentWorkflow, CreateAgentWorkflowParams
from agentex.utils.ids import orm_id
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class AgentsUseCase:

    def __init__(
        self,
        agent_repository: DAgentRepository,
        action_repository: DActionRepository,
        async_runtime: DTemporalGateway,
        environment_variables: DEnvironmentVariables,
    ):
        self.agent_repo = agent_repository
        self.action_repo = action_repository
        self.async_runtime = async_runtime
        self.build_contexts_path = environment_variables.BUILD_CONTEXTS_PATH
        self.task_queue = BUILD_AGENT_TASK_QUEUE

    async def create(
        self,
        agent_package: UploadFile,
        name: str,
        description: str,
        version: str,
        action_service_port: int
    ) -> Agent:

        # Create a temporary directory in the self.build_contexts_path directory
        # You must put the temporary directory in the build_contexts_path directory, otherwise
        # the builder job will not be able to access the files
        with tempfile.TemporaryDirectory(dir=self.build_contexts_path, delete=False) as temp_dir:
            # Save the uploaded zip file locally
            file_location = Path(temp_dir) / agent_package.filename

            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(agent_package.file, buffer)

            agent = Agent(
                id=orm_id(),
                name=name,
                description=description,
                version=version,
                action_service_port=action_service_port,
                status=AgentStatus.PENDING,
                status_reason="Request to create agent received. Waiting for build process to start.",
                build_job_name=None,
                build_job_namespace=None,
            )

            agent = await self.agent_repo.create(item=agent)

            await self._start_create_agent_workflow(
                agent=agent,
                agent_tar_path=str(file_location.absolute()),
            )

            logger.info(f"Agent creation process started for: {agent}")

            return agent

    async def _start_create_agent_workflow(
        self,
        agent: Agent,
        agent_tar_path: str,
    ) -> str:
        return await self.async_runtime.start_workflow(
            CreateAgentWorkflow.run,
            CreateAgentWorkflowParams(
                agent_tar_path=agent_tar_path,
                agent=agent,
            ),
            id=agent.id,
            task_queue=self.task_queue,
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
