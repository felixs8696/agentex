from typing import Annotated

from fastapi import Depends
from kubernetes_asyncio import client
from kubernetes_asyncio.client import V1Job, ApiClient

from agentex.adapters.kubernetes.port import KubernetesPort
from agentex.domain.entities.job import Job, JobStatus, JobCondition


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
            name=job.metadata.name,
            namespace=job.metadata.namespace,
            started_at=job_status.start_time.isoformat() if job_status.start_time else None,
            completed_at=job_status.completion_time.isoformat() if job_status.completion_time else None,
            status=status,
            conditions=[JobCondition(**condition.to_dict()) for condition in (job_status.conditions or [])]
        )


async def get_async_kubernetes_gateway() -> KubernetesGateway:
    return KubernetesGateway()


DKubernetesGateway = Annotated[KubernetesGateway, Depends(get_async_kubernetes_gateway)]
