from typing import Annotated, Optional, Dict

from fastapi import Depends
from kubernetes_asyncio import client
from kubernetes_asyncio.client import V1Job, ApiClient, ApiException, V1Deployment, V1Service

from agentex.adapters.http.adapter_httpx import DHttpxGateway
from agentex.adapters.kubernetes.port import KubernetesPort
from agentex.config.dependencies import DEnvironmentVariables
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

    def __init__(
        self,
        http_gateway: DHttpxGateway,
        environment_variables: DEnvironmentVariables,
    ):
        self.http_gateway = http_gateway
        self.build_registry_secret_name = environment_variables.BUILD_REGISTRY_SECRET_NAME

    async def create_job(self, namespace: str, job: V1Job, override: bool = False) -> Job:
        try:
            async with ApiClient() as api:
                batch_v1 = client.BatchV1Api(api)
                job = await batch_v1.create_namespaced_job(
                    body=job,
                    namespace=namespace
                )
            return self._convert_job_to_entity(job)
        except ApiException as error:
            if error.status == 409:
                if override:
                    await self.delete_job(namespace=namespace, name=job.metadata.name)
                    return await self.create_job(namespace=namespace, job=job)
                else:
                    job = await self.get_job(namespace=namespace, name=job.metadata.name)
                    return job
            raise KubernetesError(f"Error creating job {job.metadata.name}: {error}") from error

    async def get_job(self, namespace: str, name: str) -> Optional[Job]:
        try:
            async with client.ApiClient() as api:
                batch_v1 = client.BatchV1Api(api)
                job = await batch_v1.read_namespaced_job(name=name, namespace=namespace)
                return self._convert_job_to_entity(job)
        except ApiException as error:
            if error.status == 404:
                return None
            raise KubernetesError(f"Error getting job {name}: {error}") from error

    async def delete_job(self, namespace: str, name: str) -> None:
        async with ApiClient() as api:
            batch_v1 = client.BatchV1Api(api)
            try:
                await batch_v1.delete_namespaced_job(name=name, namespace=namespace)
            except ApiException as error:
                raise KubernetesError(f"Error deleting job {name}: {error}") from error

    async def create_deployment(self, namespace: str, deployment: V1Deployment, override: bool = False) -> Deployment:
        try:
            async with ApiClient() as api:
                apps_v1 = client.AppsV1Api(api)
                v1_deployment = await apps_v1.create_namespaced_deployment(
                    body=deployment,
                    namespace=namespace
                )
            return self._convert_deploy_to_entity(v1_deployment)
        except ApiException as error:
            if error.status == 409:
                if override:
                    await self.delete_deployment(namespace=namespace, name=deployment.metadata.name)
                    return await self.create_deployment(namespace=namespace, deployment=deployment)
                else:
                    v1_deployment = await self.get_deployment(namespace=namespace, name=deployment.metadata.name)
                    return v1_deployment
            raise KubernetesError(f"Error creating deployment {deployment.metadata.name}: {error}") from error

    async def get_deployment(self, namespace: str, name: str) -> Optional[Deployment]:
        try:
            async with ApiClient() as api:
                apps_v1 = client.AppsV1Api(api)
                v1_deployment = await apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        except ApiException as error:
            logger.info("Error getting deployment %s: %s", name, error)
            logger.info(f"Status: {error.status}")
            if error.status == 404:
                return None
            raise KubernetesError(f"Error getting deployment {name}: {error}") from error

        return self._convert_deploy_to_entity(v1_deployment)

    async def delete_deployment(self, namespace: str, name: str) -> None:
        """Delete the deployment by name."""
        async with ApiClient() as api:
            apps_v1 = client.AppsV1Api(api)
            try:
                await apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
            except ApiException as error:
                raise KubernetesError(f"Error deleting deployment {name}: {error}") from error

    async def create_service(self, namespace: str, service: V1Service, override: bool = False) -> Service:
        # Create the service
        try:
            async with ApiClient() as api:
                core_v1 = client.CoreV1Api(api)
                v1_service = await core_v1.create_namespaced_service(
                    body=service,
                    namespace=namespace
                )
            return self._convert_service_to_entity(v1_service)
        except ApiException as error:
            if error.status == 409:
                if override:
                    await self.delete_service(namespace=namespace, name=service.metadata.name)
                    return await self.create_service(namespace=namespace, service=service)
                else:
                    v1_service = await self.get_service(namespace=namespace, name=service.metadata.name)
                    return v1_service
            raise KubernetesError(f"Error creating service {service.metadata.name}: {error}") from error

    async def get_service(self, namespace: str, name: str) -> Optional[Service]:
        try:
            async with ApiClient() as api:
                core_v1 = client.CoreV1Api(api)
                service = await core_v1.read_namespaced_service(name=name, namespace=namespace)
                return self._convert_service_to_entity(service)
        except ApiException as error:
            if error.status == 404:
                return None
            raise KubernetesError(f"Error getting service {name}: {error}") from error

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
        port: Optional[int] = None,
        path: str = "",
        method: str = "GET",
        payload: Optional[Dict] = None
    ) -> Dict:
        if path.startswith("/"):
            path = path[1:]

        if port:
            url = f"http://{name}.{namespace}.svc.cluster.local:{port}/{path}"
        else:
            url = f"http://{name}.{namespace}.svc.cluster.local/{path}"

        logger.info(f"Calling service: {url}")
        return await self.http_gateway.async_call(
            method=method,
            url=url,
            payload=payload
        )

    @staticmethod
    def _convert_job_to_entity(job: Optional[V1Job] = None) -> Optional[Job]:
        """Convert Kubernetes V1Job object to Pydantic JobModel."""
        if not job:
            return None

        job_status = job.status

        # Determine status
        if job_status.succeeded:
            status = JobStatus.SUCCEEDED
        elif job_status.failed:
            status = JobStatus.FAILED
        elif job_status.active:
            status = JobStatus.RUNNING
        else:
            status = JobStatus.PENDING

        return Job(
            name=job.metadata.name,
            namespace=job.metadata.namespace,
            started_at=job_status.start_time.isoformat() if job_status.start_time else None,
            completed_at=job_status.completion_time.isoformat() if job_status.completion_time else None,
            status=status,
            conditions=[JobCondition(**condition.to_dict()) for condition in (job_status.conditions or [])]
        )

    @staticmethod
    def _convert_deploy_to_entity(deployment: Optional[V1Deployment] = None) -> Optional[Deployment]:
        """
        Convert Kubernetes V1Deployment object to Pydantic DeploymentModel.
        """
        if not deployment:
            return None
        deployment_status = deployment.status
        if deployment_status:
            if deployment_status.available_replicas > 0:
                status = DeploymentStatus.READY
            elif deployment_status.available_replicas == 0:
                status = DeploymentStatus.UNAVAILABLE
            else:
                status = DeploymentStatus.UNKNOWN
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
    def _convert_service_to_entity(service: Optional[client.V1Service] = None) -> Optional[Service]:
        """
        Convert Kubernetes V1Service object to Pydantic ServiceModel.
        """
        if not service:
            return None
        metadata = service.metadata
        return Service(
            name=metadata.name,
            namespace=metadata.namespace,
            created_at=metadata.creation_timestamp.isoformat() if metadata.creation_timestamp else None,
            conditions=[
                ServiceCondition(**condition.to_dict()) for condition in (service.status.conditions or [])
            ]
        )


DKubernetesGateway = Annotated[KubernetesGateway, Depends(KubernetesGateway)]
