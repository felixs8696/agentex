from abc import ABC, abstractmethod


class ContainerBuildGateway(ABC):

    @abstractmethod
    async def build_image(
        self,
        namespace: str,
        image: str,
        tag: str,
        zip_file_path: str,
        registry_url: str,
    ):
        pass
