from abc import ABC, abstractmethod
from typing import Tuple

from agentex.domain.entities.job import Job


class ContainerBuildGateway(ABC):

    @abstractmethod
    async def build_image(
        self,
        namespace: str,
        image: str,
        tag: str,
        zip_file_path: str,
        registry_url: str,
    ) -> Tuple[str, Job]:
        pass
