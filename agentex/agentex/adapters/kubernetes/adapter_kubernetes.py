from typing import Annotated

from fastapi import Depends
from kubernetes_asyncio import client
from kubernetes_asyncio.client import V1Job, ApiClient

from agentex.adapters.kubernetes.port import KubernetesPort


class KubernetesGateway(KubernetesPort):

    async def create_job(self, namespace: str, job: V1Job):
        async with ApiClient() as api:
            batch_v1 = client.BatchV1Api(api)
            await batch_v1.create_namespaced_job(
                body=job,
                namespace=namespace
            )


async def get_async_kubernetes_gateway() -> KubernetesGateway:
    return KubernetesGateway()


DKubernetesGateway = Annotated[KubernetesGateway, Depends(get_async_kubernetes_gateway)]
