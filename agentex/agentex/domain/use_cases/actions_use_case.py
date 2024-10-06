import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Optional, List, Annotated, Dict, Any

from fastapi import Depends, UploadFile

from agentex.adapters.async_runtime.adapter_temporal import DTemporalGateway
from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.actions import Action, ActionStatus
from agentex.domain.exceptions import ClientError
from agentex.domain.services.agents.action_repository import DActionRepository
from agentex.domain.services.agents.action_service import DActionService
from agentex.domain.services.agents.agent_repository import DAgentRepository
from agentex.domain.workflows.constants import BUILD_ACTION_TASK_QUEUE
from agentex.domain.workflows.create_action_workflow import CreateActionWorkflow, CreateActionWorkflowParams
from agentex.utils.ids import orm_id
from agentex.utils.json_schema import validate_payload, JSONSchemaValidationError
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class ActionUnzipError(ClientError):
    """
    Error raised when there is an issue with unzipping the code package.
    """
    code = 400


class InvalidActionError(ClientError):
    """
    Error raised when there is an issue running the action
    """
    code = 400


class ActionsUseCase:

    def __init__(
        self,
        action_repository: DActionRepository,
        agent_repository: DAgentRepository,
        action_service: DActionService,
        async_runtime: DTemporalGateway,
        environment_variables: DEnvironmentVariables,
    ):
        self.action_repo = action_repository
        self.agent_repo = agent_repository
        self.action_service = action_service
        self.async_runtime = async_runtime
        self.build_contexts_path = environment_variables.BUILD_CONTEXTS_PATH
        self.task_queue = BUILD_ACTION_TASK_QUEUE

    async def create(
        self,
        name: str,
        description: str,
        version: str,
        parameters: Dict[str, Any],
        test_payload: Dict[str, Any],
        code_package: UploadFile,  # Assuming UploadFile is imported from FastAPI
        agents: List[str],
    ) -> Action:
        try:
            validate_payload(json_schema=parameters, payload=test_payload)
        except JSONSchemaValidationError as error:
            raise ClientError(f"Test payload does not match parameters schema: {error}") from error

        # Create a temporary directory in the self.build_contexts_path directory
        # You must put the temporary directory in the build_contexts_path directory, otherwise
        # the builder job will not be able to access the files
        with tempfile.TemporaryDirectory(dir=self.build_contexts_path, delete=False) as temp_dir:
            # Save the uploaded zip file locally
            file_location = Path(temp_dir) / code_package.filename

            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(code_package.file, buffer)

            # Extract the zip file
            try:
                with tarfile.open(file_location, 'r:gz') as tar_ref:
                    tar_ref.extractall(path=temp_dir)  # Extract to the temporary directory

                    # List the contents of the extracted tar.gz file
                    extracted_files = [member.name for member in tar_ref.getmembers()]  # Get list of file names
                    logger.info(f"Extracted files: {extracted_files}")
            except Exception as e:
                raise ActionUnzipError(f"Error extracting tar file: {e}") from e

            # Run Docker container to validate the code package using the gateway
            image = name
            docker_image_uri = f"{image}:{version}"

            await self.action_service.build_action(
                image=image,
                tag=version,
                zip_file_path=file_location.absolute()
            )
            # await self.container_manager.build_image(path=temp_dir, image_name=docker_image_uri)
            # result = await self.container_manager.run_container(docker_image_uri, test_payload)
            # logger.info(f"Action Test Output: {result}")
            # await self.container_manager.remove_image(docker_image_uri)

            action = Action(
                id=orm_id(),
                name=name,
                description=description,
                version=version,
                parameters=parameters,
                test_payload=test_payload,
                docker_image=docker_image_uri,
                status=ActionStatus.PENDING,
                build_job_name=None,
                build_job_namespace=None,
            )

            await self._start_create_action_workflow(
                action=action,
                agents=agents,
                action_tar_path=str(file_location.absolute()),
            )

            logger.info(f"Action creation process started for: {action}")

            return action

    async def _start_create_action_workflow(
        self,
        action: Action,
        agents: List[str],
        action_tar_path: str,
    ) -> str:
        return await self.async_runtime.start_workflow(
            CreateActionWorkflow.run,
            CreateActionWorkflowParams(
                action=action,
                agents=agents,
                action_tar_path=action_tar_path,
            ),
            id=action.id,
            task_queue=self.task_queue,
        )

    async def get(self, id: Optional[str], name: Optional[str]) -> Action:
        return await self.action_repo.get(id=id, name=name)

    async def update(self, action: Action) -> Action:
        return await self.action_repo.update(item=action)

    async def delete(self, id: Optional[str], name: Optional[str]) -> Action:
        return await self.action_repo.delete(id=id, name=name)

    async def list(self) -> List[Action]:
        return await self.action_repo.list()


DActionsUseCase = Annotated[ActionsUseCase, Depends(ActionsUseCase)]
