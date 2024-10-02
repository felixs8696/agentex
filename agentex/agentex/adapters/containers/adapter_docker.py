import asyncio
import json
import os
import tempfile
from typing import Dict, Any, Annotated

from aiodocker import DockerError, DockerContainerError
from docker.types import Mount
from fastapi import Depends

from agentex.adapters.containers.port import ContainerManagementGateway
from agentex.config.dependencies import DDockerClient
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class DockerGateway(ContainerManagementGateway):
    def __init__(self, docker_client: DDockerClient):
        self.client = docker_client

    async def build_image(self, image_name: str, path: str) -> None:
        """Build a Docker image from a directory."""
        try:
            await asyncio.to_thread(self._build_image, image_name, path)
        except DockerError as error:
            raise Exception(f"Error building Docker image: {error}")

    def _build_image(self, image_name: str, path: str):
        """Blocking function to build the image and return logs."""
        # Return the generator that yields log messages
        image, build_logs = self.client.images.build(path=path, tag=image_name)
        logger.info(f"Building Docker image {image_name} from {path}")
        for chunk in build_logs:
            if 'stream' in chunk:
                for line in chunk['stream'].splitlines():
                    logger.info(line)

    async def run_container(self, image_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run a Docker container with parameters passed via a mounted file and return the JSON result."""
        try:
            # Use context managers to automatically handle file cleanup
            with (
                tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as param_file,
                tempfile.NamedTemporaryFile(mode='r+', suffix='.json', delete=False) as result_file
            ):
                # Write parameters to the temporary parameter file
                json.dump(parameters, param_file)
                param_file.flush()  # Ensure data is written before container reads it
                param_file_path = os.path.abspath(param_file.name)
                result_file_path = os.path.abspath(result_file.name)

                # Run the container with mounted volumes
                await asyncio.to_thread(
                    self._run_container, image_name, param_file_path, result_file_path
                )

                # Read the JSON result from the output file
                result_file.seek(0)  # Move to the start of the result file before reading
                logger.info(f"Result file {result_file_path} contents:")
                for line in result_file:
                    logger.info(line)
                result_file.seek(0)
                result = json.load(result_file)

                os.remove(param_file_path)
                os.remove(result_file_path)

                return result

        except DockerContainerError as error:
            raise Exception(f"Error running Docker container: {error}")

    def _run_container(self, image_name: str, param_file_path: str, result_file_path: str):
        """Blocking function to run a Docker container and return logs."""
        # Define paths in the container
        mount_params_path = '/app/config/params.json'
        mount_result_path = '/app/output/result.json'

        # Verify that parameters and results are mounted correctly
        assert os.path.exists(param_file_path), f"Parameters file {param_file_path} does not exist"
        # show what is in the file
        logger.info("Parameters file contents:")
        with open(param_file_path, 'r') as f:
            for line in f:
                logger.info(line)
        assert os.path.exists(result_file_path), f"Result file {result_file_path} does not exist"

        # Return the generator that yields log messages
        container = self.client.containers.run(
            image=image_name,
            detach=True,
            # remove=True,
            # stdout=True,
            # stderr=True,
            mounts=[
                Mount(target=mount_params_path, source=param_file_path, type='bind', read_only=True),  # Read-only for parameters
                Mount(target=mount_result_path, source=result_file_path, type='bind', read_only=False)  # Read-write for the result
            ]
        )
        logger.info(f"Running Docker container {image_name}:")
        for chunk in container.logs(stream=True):
            for line in chunk.decode('utf-8').splitlines():
                logger.info(line)

        return container

    async def remove_image(self, image_name: str) -> None:
        """Remove a Docker image."""
        await asyncio.to_thread(self._remove_image, image_name)

    def _remove_image(self, image_name: str) -> None:
        """Blocking function to remove a Docker image."""
        self.client.images.remove(image=image_name, force=True)


DDockerGateway = Annotated[DockerGateway, Depends(DockerGateway)]
