from pathlib import Path

import requests
from agentex.src.models.action_manifest import ActionManifestConfig

from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class Agentex:

    def __init__(self, base_url: str = "http://localhost:5003/actions"):
        self.base_url = base_url





class Action:

    def __init__(self, base_url: str = "http://localhost:5003/actions"):
        self.base_url = base_url

    def create(self, manifest_path: str):
        action_manifest = ActionManifestConfig.from_yaml(file_path=manifest_path)
        build_context_root = (Path(manifest_path).parent / action_manifest.build.build_context.root).resolve()
        with action_manifest.context_manager(build_context_root) as build_context:
            with build_context.zip_stream(build_context.path) as zip_stream:
                logger.info(f"Sending zipped build context to FastAPI service at {self.base_url}...")

                # Prepare the files for the POST request
                files = {'file': ('context.tar.gz', zip_stream, 'application/gzip')}

                try:
                    # Make a POST request to the FastAPI service
                    response = requests.post(self.base_url, files=files)

                    # Check if the request was successful
                    if response.status_code == 200:
                        logger.info("Zipped build context successfully uploaded to FastAPI service.")
                    else:
                        logger.error(f"Failed to upload build context: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    logger.error(f"An error occurred while sending build context: {e}")
