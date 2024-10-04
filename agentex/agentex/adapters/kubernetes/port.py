from abc import abstractmethod, ABC

from kubernetes_asyncio.client import V1Job


class KubernetesPort(ABC):

    @abstractmethod
    async def create_configmap(self, name: str, namespace: str, data: dict):
        pass

    @abstractmethod
    async def create_job(self, job_name: str, job: V1Job):
        pass
