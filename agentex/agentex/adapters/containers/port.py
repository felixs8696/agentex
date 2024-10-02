from abc import ABC, abstractmethod
from typing import Dict, Any


class ContainerManagementGateway(ABC):

    @abstractmethod
    def build_image(self, image_name: str, path: str) -> None:
        pass

    @abstractmethod
    def run_container(self, image_name: str, parameters: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def remove_image(self, image_name: str) -> None:
        pass
