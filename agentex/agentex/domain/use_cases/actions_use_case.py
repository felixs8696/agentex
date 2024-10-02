import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, List, Annotated, Dict, Any

from fastapi import Depends, UploadFile

from agentex.adapters.containers.adapter_docker import DDockerGateway
from agentex.domain.entities.actions import Action
from agentex.domain.exceptions import ClientError
from agentex.domain.services.agents.action_repository import DActionRepository
from agentex.domain.services.agents.agent_repository import DAgentRepository
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
        container_manager: DDockerGateway  # Injecting the Docker container manager
    ):
        self.action_repo = action_repository
        self.agent_repo = agent_repository
        self.container_manager = container_manager

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

        # Create a temporary directory for extracting the zip file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the uploaded zip file locally
            file_location = Path(temp_dir) / code_package.filename

            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(code_package.file, buffer)

            # Extract the zip file
            try:
                with zipfile.ZipFile(file_location, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                    # List the contents of the extracted zip file
                    extracted_files = zip_ref.namelist()  # Get list of file names in the zip
                    logger.info(f"Extracted files: {extracted_files}")
            except Exception as e:
                raise ActionUnzipError(f"Error extracting zip file: {e}")

            # Run Docker container to validate the code package using the gateway
            try:
                docker_image_uri = f"agentex/actions/temp/{name}:latest"
                await self.container_manager.build_image(path=temp_dir, image_name=docker_image_uri)
                result = await self.container_manager.run_container(docker_image_uri, test_payload)
                logger.info(f"Action Test Output: {result}")
                await self.container_manager.remove_image(docker_image_uri)
            except Exception as e:
                raise InvalidActionError(f"Encounter error running action: {e}")

            action = await self.action_repo.create(
                item=Action(
                    id=orm_id(),  # Assuming orm_id() generates a unique ID
                    name=name,
                    description=description,
                    version=version,
                    parameters=parameters,
                    test_payload=test_payload,
                    docker_image=docker_image_uri,
                )
            )

            if agents:
                logger.info("Associating agents with action")
                await self.agent_repo.associate_agents_with_actions(
                    agent_names=agents,
                    action_ids=[action.id]
                )

            return action

    async def get(self, id: Optional[str], name: Optional[str]) -> Action:
        return await self.action_repo.get(id=id, name=name)

    async def update(self, action: Action) -> Action:
        return await self.action_repo.update(item=action)

    async def delete(self, id: Optional[str], name: Optional[str]) -> Action:
        return await self.action_repo.delete(id=id, name=name)

    async def list(self) -> List[Action]:
        return await self.action_repo.list()


DActionsUseCase = Annotated[ActionsUseCase, Depends(ActionsUseCase)]
