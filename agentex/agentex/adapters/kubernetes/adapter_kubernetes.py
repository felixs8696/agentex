from typing import Annotated, Optional, Dict

import httpx
from fastapi import Depends
from kubernetes_asyncio import client
from kubernetes_asyncio.client import V1Job, ApiClient, ApiException, V1Deployment

from agentex.adapters.http.adapter_httpx import DHttpxGateway
from agentex.adapters.kubernetes.port import KubernetesPort
from agentex.domain.entities.deployment import Deployment, DeploymentStatus, DeploymentCondition
from agentex.domain.entities.job import Job, JobStatus, JobCondition
from agentex.domain.entities.service import Service, ServiceCondition
from agentex.domain.exceptions import ServiceError
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class KubernetesError(ServiceError):
    """
    Base class for Kubernetes errors.
    """

    code = 500


class KubernetesGateway(KubernetesPort):

    def __init__(self, http_gateway: DHttpxGateway):
        self.http_gateway = http_gateway

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

    async def delete_job(self, namespace: str, name: str) -> None:
        async with ApiClient() as api:
            batch_v1 = client.BatchV1Api(api)
            try:
                await batch_v1.delete_namespaced_job(name=name, namespace=namespace)
            except ApiException as error:
                raise KubernetesError(f"Error deleting job {name}: {error}") from error

    async def create_deployment(
        self,
        namespace: str,
        name: str,
        image: str,
        container_port: int = 8000,
        replicas: Optional[int] = 1
    ) -> Deployment:
        async with ApiClient() as api:
            apps_v1 = client.AppsV1Api(api)
            deployment = await apps_v1.create_namespaced_deployment(
                body=client.V1Deployment(
                    api_version="apps/v1",
                    kind="Deployment",
                    metadata=client.V1ObjectMeta(name=name),
                    spec=client.V1DeploymentSpec(
                        replicas=replicas,
                        selector={'matchLabels': {'app': name}},
                        template=client.V1PodTemplateSpec(
                            metadata=client.V1ObjectMeta(labels={'app': name}),
                            spec=client.V1PodSpec(
                                containers=[
                                    client.V1Container(
                                        name=name,
                                        image=image,
                                        ports=[client.V1ContainerPort(container_port=container_port)]
                                    )
                                ]
                            )
                        )
                    )
                ),
                namespace=namespace
            )
        return self._convert_deploy_to_entity(deployment)

    async def get_deployment(self, namespace: str, name: str) -> Deployment:
        async with ApiClient() as api:
            apps_v1 = client.AppsV1Api(api)
            deployment = await apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            return self._convert_deploy_to_entity(deployment)

    async def delete_deployment(self, namespace: str, name: str) -> None:
        """Delete the deployment by name."""
        async with ApiClient() as api:
            apps_v1 = client.AppsV1Api(api)
            try:
                await apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
            except ApiException as error:
                raise KubernetesError(f"Error deleting deployment {name}: {error}") from error

    async def create_service(
        self,
        namespace: str,
        name: str,
        service_port: int = 80,
        container_port: int = 8000,
    ) -> Service:
        # Create the service
        async with ApiClient() as api:
            core_v1 = client.CoreV1Api(api)
            service = await core_v1.create_namespaced_service(
                body=client.V1Service(
                    api_version="v1",
                    kind="Service",
                    metadata=client.V1ObjectMeta(name=name),
                    spec=client.V1ServiceSpec(
                        selector={'app': name},
                        ports=[
                            client.V1ServicePort(
                                port=service_port,
                                target_port=container_port,
                                protocol="TCP"
                            )
                        ]
                    )
                ),
                namespace=namespace
            )
        return self._convert_service_to_entity(service)

    async def get_service(self, namespace: str, name: str) -> Service:
        async with ApiClient() as api:
            core_v1 = client.CoreV1Api(api)
            service = await core_v1.read_namespaced_service(name=name, namespace=namespace)
            return self._convert_service_to_entity(service)

    async def delete_service(self, namespace: str, name: str) -> None:
        """Delete the service by name."""
        async with ApiClient() as api:
            core_v1 = client.CoreV1Api(api)
            try:
                await core_v1.delete_namespaced_service(name=name, namespace=namespace)
            except ApiException as error:
                raise KubernetesError(f"Error deleting service {name}: {error}") from error

    async def call_service(
        self,
        namespace: str,
        name: str,
        path: str = "",
        method: str = "GET",
        payload: Optional[Dict] = None
    ) -> Dict:
        return await self.http_gateway.async_call(
            method="GET",
            url=f"http://{name}.{namespace}.svc.cluster.local/{path}",
            payload=payload
        )

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

    @staticmethod
    def _convert_deploy_to_entity(deployment: V1Deployment) -> Deployment:
        """
        Convert Kubernetes V1Deployment object to Pydantic DeploymentModel.
        """
        deployment_status = deployment.status
        if deployment_status.available_replicas > 0:
            status = DeploymentStatus.READY
        elif deployment_status.available_replicas == 0:
            status = DeploymentStatus.UNAVAILABLE
        else:
            status = DeploymentStatus.UNKNOWN

        metadata = deployment.metadata

        return Deployment(
            name=metadata.name,
            namespace=metadata.namespace,
            created_at=metadata.creation_timestamp.isoformat() if metadata.creation_timestamp else None,
            status=status,
            conditions=[
                DeploymentCondition(**condition.to_dict()) for condition in
                (deployment_status.conditions or [])
            ]
        )

    @staticmethod
    def _convert_service_to_entity(service: client.V1Service) -> Service:
        """
        Convert Kubernetes V1Service object to Pydantic ServiceModel.
        """
        metadata = service.metadata
        return Service(
            name=metadata.name,
            namespace=metadata.namespace,
            created_at=metadata.creation_timestamp.isoformat() if metadata.creation_timestamp else None,
            conditions=[
                ServiceCondition(**condition.to_dict()) for condition in (service.status.conditions or [])
            ]
        )


async def get_async_kubernetes_gateway() -> KubernetesGateway:
    return KubernetesGateway()


DKubernetesGateway = Annotated[KubernetesGateway, Depends(get_async_kubernetes_gateway)]
