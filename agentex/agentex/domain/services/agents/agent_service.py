from typing import Annotated, Optional, Tuple, Union

from fastapi import Depends
from kubernetes_asyncio import client as k8s_client

from agentex.adapters.containers.build_adapter_kaniko import DKanikoBuildGateway
from agentex.adapters.kubernetes.adapter_kubernetes import DKubernetesGateway
from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.agents import Agent
from agentex.domain.entities.deployment import Deployment
from agentex.domain.entities.job import Job
from agentex.domain.entities.service import Service
from agentex.domain.services.agents.agent_repository import DAgentRepository
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class AgentService:
    def __init__(
        self,
        build_gateway: DKanikoBuildGateway,
        agent_repository: DAgentRepository,
        kubernetes_gateway: DKubernetesGateway,
        environment_variables: DEnvironmentVariables,
    ):
        self.k8s = kubernetes_gateway
        self.build_gateway = build_gateway
        self.agent_repo = agent_repository
        self.registry_url = environment_variables.BUILD_REGISTRY_URL
        self.build_registry_secret_name = environment_variables.BUILD_REGISTRY_SECRET_NAME
        self.agents_namespace = environment_variables.AGENTS_NAMESPACE
        self.build_namespace = "default"
        self.environment = environment_variables

    async def create_agent_deployment(
        self,
        name: str,
        image: str,
        replicas: int = 1,
    ) -> Deployment:
        # Define container
        container = k8s_client.V1Container(
            name=name,
            image=image,
            image_pull_policy="Always",
            env=[
                k8s_client.V1EnvVar(name="TEMPORAL_ADDRESS", value=self.environment.TEMPORAL_ADDRESS),
                k8s_client.V1EnvVar(name="REDIS_URL", value=self.environment.REDIS_URL),
                k8s_client.V1EnvVar(
                    name="OPENAI_API_KEY",
                    value_from=k8s_client.V1EnvVarSource(
                        secret_key_ref=k8s_client.V1SecretKeySelector(
                            name="openai-api-key",
                            key="api-key",
                        )
                    )
                ),
            ],
            ports=[
                k8s_client.V1ContainerPort(
                    name="http",
                    container_port=80,
                    protocol="TCP",
                )
            ],
            liveness_probe=k8s_client.V1Probe(
                failure_threshold=3,
                period_seconds=10,
                success_threshold=1,
                timeout_seconds=1,
                http_get=k8s_client.V1HTTPGetAction(
                    path="/readyz",
                    port="http",
                )
            ),
            readiness_probe=k8s_client.V1Probe(
                failure_threshold=3,
                period_seconds=10,
                success_threshold=1,
                timeout_seconds=1,
                http_get=k8s_client.V1HTTPGetAction(
                    path="/readyz",
                    port="http",
                )
            ),
        )

        # Define pod spec
        pod_spec = k8s_client.V1PodSpec(
            restart_policy="Always",
            containers=[container],
        )

        # Define pod template
        template = k8s_client.V1PodTemplateSpec(
            metadata=k8s_client.V1ObjectMeta(
                labels={
                    "app.kubernetes.io/name": name,
                    "app.kubernetes.io/instance": name,
                },
                name=name,
                namespace=self.agents_namespace,
            ),
            spec=pod_spec,
        )

        # Define deployment spec
        deployment_spec = k8s_client.V1DeploymentSpec(
            replicas=replicas,
            selector={
                "matchLabels": {
                    "app.kubernetes.io/name": name,
                    "app.kubernetes.io/instance": name,
                }
            },
            template=template,
        )

        # Define deployment
        deployment = k8s_client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=k8s_client.V1ObjectMeta(
                name=name,
                labels={
                    "app.kubernetes.io/name": name,
                    "app.kubernetes.io/instance": name,
                },
            ),
            spec=deployment_spec,
        )

        # Create the deployment
        return await self.k8s.create_deployment(
            namespace=self.agents_namespace, deployment=deployment
        )

    async def create_agent_service(
        self,
        name: str,
        port: int = 80,
        service_type: str = "ClusterIP",
    ) -> Service:
        service = k8s_client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=k8s_client.V1ObjectMeta(
                name=name,
                labels={
                    "app.kubernetes.io/name": name,
                    "app.kubernetes.io/instance": name,
                },
            ),
            spec=k8s_client.V1ServiceSpec(
                type=service_type,
                selector={
                    "app.kubernetes.io/name": name,
                    "app.kubernetes.io/instance": name,
                },
                ports=[
                    k8s_client.V1ServicePort(
                        name="http",
                        port=port,
                        target_port="http",
                        protocol="TCP",
                    )
                ],
            ),
        )

        return await self.k8s.create_service(
            namespace=self.agents_namespace, service=service
        )

    async def get_agent_deployment(self, name: str) -> Optional[Deployment]:
        return await self.k8s.get_deployment(namespace=self.agents_namespace, name=name)

    async def get_agent_service(self, name: str) -> Optional[Service]:
        return await self.k8s.get_service(namespace=self.agents_namespace, name=name)

    async def delete_agent_deployment(self, name: str):
        return await self.k8s.delete_deployment(namespace=self.agents_namespace, name=name)

    async def delete_agent_service(self, name: str):
        return await self.k8s.delete_service(namespace=self.agents_namespace, name=name)

    async def create_build_job(self, image: str, tag: str, zip_file_path: str) -> Tuple[str, Job]:
        return await self.build_gateway.build_image(
            namespace=self.build_namespace,
            image=image,
            tag=tag,
            zip_file_path=zip_file_path,
            registry_url=self.registry_url,
        )

    async def get_build_job(self, name: str) -> Optional[Job]:
        return await self.k8s.get_job(namespace=self.build_namespace, name=name)

    async def delete_build_job(self, name: str):
        return await self.k8s.delete_job(namespace=self.build_namespace, name=name)

    async def update_agent(self, agent: Agent) -> Agent:
        return await self.agent_repo.update(item=agent)


DAgentService = Annotated[AgentService, Depends(AgentService)]
