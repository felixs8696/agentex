from typing import Annotated

from fastapi import Depends
from kubernetes_asyncio import client
from kubernetes_asyncio.client import V1Job, ApiClient

from agentex.adapters.kubernetes.port import KubernetesPort
from agentex.domain.entities.job import Job, JobStatus


class KubernetesGateway(KubernetesPort):

    async def create_job(self, namespace: str, job: V1Job) -> Job:
        async with ApiClient() as api:
            batch_v1 = client.BatchV1Api(api)
            job = await batch_v1.create_namespaced_job(
                body=job,
                namespace=namespace
            )
        return self._convert_job_to_entity(job)

    async def get_job(self, namespace: str, name: str) -> Job:
        async with client.ApiClient() as api:
            batch_v1 = client.BatchV1Api(api)
            job = await batch_v1.read_namespaced_job(name=name, namespace=namespace)
            return self._convert_job_to_entity(job)

    @staticmethod
    def _convert_job_to_entity(job: V1Job) -> Job:
        """Convert Kubernetes V1Job object to Pydantic JobModel."""
        job_status = job.status

        # Determine status
        if job_status.succeeded:
            status = JobStatus.SUCCEEDED
        elif job_status.failed:
            status = JobStatus.FAILED
        elif job_status.active:
            status = JobStatus.RUNNING
        else:
            status = JobStatus.PENDING if job_status.start_time is None else JobStatus.UNKNOWN

        return Job(
            job_name=job.metadata.name,
            namespace=job.metadata.namespace,
            start_time=job_status.start_time.isoformat() if job_status.start_time else None,
            completion_time=job_status.completion_time.isoformat() if job_status.completion_time else None,
            status=status,
            active_pods=job_status.active or 0,
            succeeded_pods=job_status.succeeded or 0,
            failed_pods=job_status.failed or 0
        )


async def get_async_kubernetes_gateway() -> KubernetesGateway:
    return KubernetesGateway()


DKubernetesGateway = Annotated[KubernetesGateway, Depends(get_async_kubernetes_gateway)]
