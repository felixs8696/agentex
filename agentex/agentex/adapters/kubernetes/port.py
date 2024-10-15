from abc import abstractmethod, ABC
from typing import Optional, Dict

from kubernetes_asyncio.client import V1Job

from agentex.domain.entities.deployment import Deployment
from agentex.domain.entities.job import Job
from agentex.domain.entities.service import Service


class KubernetesPort(ABC):

    @abstractmethod
    async def create_job(self, job_name: str, job: V1Job) -> Job:
        pass

    @abstractmethod
    async def get_job(self, namespace: str, name: str) -> Optional[Job]:
        pass

    @abstractmethod
    async def delete_job(self, namespace: str, name: str) -> None:
        pass

    @abstractmethod
    async def create_deployment(
        self,
        namespace: str,
        name: str,
        image: str,
        container_port: int = 8000,
        replicas: Optional[int] = 1
    ) -> Deployment:
        pass

    @abstractmethod
    async def get_deployment(self, namespace: str, name: str) -> Optional[Deployment]:
        pass

    @abstractmethod
    async def delete_deployment(self, namespace: str, name: str) -> None:
        pass

    @abstractmethod
    async def create_service(
        self,
        namespace: str,
        name: str,
        service_port: int = 80,
        container_port: int = 8000,
    ) -> Service:
        pass

    @abstractmethod
    async def get_service(self, namespace: str, name: str) -> Optional[Service]:
        pass

    @abstractmethod
    async def delete_service(self, namespace: str, name: str) -> None:
        pass

    @abstractmethod
    async def call_service(
        self,
        namespace: str,
        name: str, 
        path: str = "",
        method: str = "GET",
        payload: Optional[Dict] = None
    ) -> Dict:
        pass
