from typing import Annotated

from fastapi import Depends
from kubernetes_asyncio import client
from kubernetes_asyncio.client import V1Job

from agentex.adapters.kubernetes.port import KubernetesPort


class KubernetesGateway(KubernetesPort):
    def __init__(self):
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()

    async def create_configmap(self, name: str, namespace: str, data: dict):
        """Create a ConfigMap for passing parameters to the container."""
        config_map = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(name=name),
            data=data
        )
        await self.core_v1.create_namespaced_config_map(namespace=namespace, body=config_map)

    async def create_job(self, namespace: str, job: V1Job):
        await self.batch_v1.create_namespaced_job(
            body=job,
            namespace=namespace
        )


DKubernetesGateway = Annotated[KubernetesGateway, Depends(KubernetesGateway)]
