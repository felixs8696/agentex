from typing import Annotated, Optional, Tuple

from fastapi import Depends
from kubernetes_asyncio import client as k8s_client

from agentex.adapters.containers.build_adapter_kaniko import DKanikoBuildGateway
from agentex.adapters.kubernetes.adapter_kubernetes import DKubernetesGateway
from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.agent_spec import AgentSpec
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
        self.actions_build_namespace = "default"

    async def create_hosted_actions_deployment(
        self,
        name: str,
        image: str,
        action_service_port: int,
        replicas: int = 1,
    ) -> Deployment:
        return await self.k8s.create_deployment(
            namespace=self.agents_namespace,
            deployment=k8s_client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=k8s_client.V1ObjectMeta(name=name),
                spec=k8s_client.V1DeploymentSpec(
                    replicas=replicas,
                    selector={'matchLabels': {'app': name}},
                    template=k8s_client.V1PodTemplateSpec(
                        metadata=k8s_client.V1ObjectMeta(labels={'app': name}),
                        spec=k8s_client.V1PodSpec(
                            containers=[
                                k8s_client.V1Container(
                                    name=name,
                                    image=image,
                                    image_pull_policy="IfNotPresent",
                                    ports=[
                                        k8s_client.V1ContainerPort(
                                            name="http",
                                            container_port=action_service_port,
                                            protocol="TCP",
                                        )
                                    ],
                                ),
                            ],
                            image_pull_secrets=[
                                k8s_client.V1LocalObjectReference(name=self.build_registry_secret_name)
                            ],
                        )
                    )
                )
            ),
        )

    async def create_hosted_actions_service(
        self,
        name: str,
    ) -> Service:
        return await self.k8s.create_service(
            namespace=self.agents_namespace,
            service=k8s_client.V1Service(
                api_version="v1",
                kind="Service",
                metadata=k8s_client.V1ObjectMeta(name=name),
                spec=k8s_client.V1ServiceSpec(
                    selector={'app': name},
                    ports=[
                        k8s_client.V1ServicePort(
                            name="http",
                            port=80,
                            target_port="http",
                            protocol="TCP"
                        )
                    ]
                )
            ),
        )

    async def get_hosted_actions_deployment(self, name: str) -> Optional[Deployment]:
        return await self.k8s.get_deployment(namespace=self.agents_namespace, name=name)

    async def get_hosted_actions_service(self, name: str) -> Optional[Service]:
        return await self.k8s.get_service(namespace=self.agents_namespace, name=name)

    async def call_hosted_actions_service(
        self,
        name: str,
        path: str,
        method: str = "GET",
        payload: Optional[dict] = None
    ):
        agent_spec = await self.k8s.call_service(
            namespace=self.agents_namespace,
            name=name,
            port=80,
            path=path,
            method=method,
            payload=payload
        )
        return AgentSpec.from_dict(agent_spec)

    async def delete_hosted_actions_deployment(self, name: str):
        return await self.k8s.delete_deployment(namespace=self.agents_namespace, name=name)

    async def delete_hosted_actions_service(self, name: str):
        return await self.k8s.delete_service(namespace=self.agents_namespace, name=name)

    async def create_build_job(self, image: str, tag: str, zip_file_path: str) -> Tuple[str, Job]:
        return await self.build_gateway.build_image(
            namespace=self.actions_build_namespace,
            image=image,
            tag=tag,
            zip_file_path=zip_file_path,
            registry_url=self.registry_url,
        )

    async def get_build_job(self, name: str) -> Optional[Job]:
        return await self.k8s.get_job(namespace=self.actions_build_namespace, name=name)

    async def delete_build_job(self, name: str):
        return await self.k8s.delete_job(namespace=self.actions_build_namespace, name=name)

    async def update_agent(self, agent: Agent) -> Agent:
        return await self.agent_repo.update(item=agent)


DAgentService = Annotated[AgentService, Depends(AgentService)]
