from typing import Annotated, Optional, List, Tuple

from fastapi import Depends
from kubernetes_asyncio import client as k8s_client

from agentex.adapters.containers.build_adapter_kaniko import DKanikoBuildGateway
from agentex.adapters.kubernetes.adapter_kubernetes import DKubernetesGateway
from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.actions import Action
from agentex.domain.entities.agent_spec import AgentSpec
from agentex.domain.entities.agents import Agent
from agentex.domain.entities.deployment import Deployment
from agentex.domain.entities.job import Job
from agentex.domain.entities.service import Service
from agentex.domain.services.agents.action_repository import DActionRepository
from agentex.domain.services.agents.agent_repository import DAgentRepository
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class AgentService:
    def __init__(
        self,
        build_gateway: DKanikoBuildGateway,
        action_repository: DActionRepository,
        agent_repository: DAgentRepository,
        kubernetes_gateway: DKubernetesGateway,
        environment_variables: DEnvironmentVariables,
    ):
        self.default_namespace = "default"
        self.k8s = kubernetes_gateway
        self.build_gateway = build_gateway
        self.action_repo = action_repository
        self.agent_repo = agent_repository
        self.registry_url = environment_variables.BUILD_REGISTRY_URL
        self.build_registry_secret_name = environment_variables.BUILD_REGISTRY_SECRET_NAME

    async def create_agent_with_actions(self, agent: Agent, actions: List[Action]) -> Tuple[Agent, List[Action]]:
        agent = await self.agent_repo.create(item=agent)
        actions = await self.action_repo.batch_create(item=actions)

        await self.agent_repo.associate_agents_with_actions(
            agents=[agent],
            actions=actions,
        )

        return agent, actions

    async def create_hosted_actions_deployment(
        self,
        name: str,
        image: str,
        action_service_port: int,
        replicas: int = 1,
    ) -> Deployment:
        return await self.k8s.create_deployment(
            namespace=self.default_namespace,
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
                                    ports=[k8s_client.V1ContainerPort(container_port=action_service_port)],
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
        action_service_port: int,
    ) -> Service:
        return await self.k8s.create_service(
            namespace=self.default_namespace,
            service=k8s_client.V1Service(
                api_version="v1",
                kind="Service",
                metadata=k8s_client.V1ObjectMeta(name=name),
                spec=k8s_client.V1ServiceSpec(
                    selector={'app': name},
                    ports=[
                        k8s_client.V1ServicePort(
                            port=80,
                            target_port=action_service_port,
                            protocol="TCP"
                        )
                    ]
                )
            ),
        )

    async def get_hosted_actions_deployment(self, name: str) -> Optional[Deployment]:
        return await self.k8s.get_deployment(namespace=self.default_namespace, name=name)

    async def get_hosted_actions_service(self, name: str) -> Optional[Service]:
        return await self.k8s.get_service(namespace=self.default_namespace, name=name)

    async def call_hosted_actions_service(
        self,
        name: str,
        port: int,
        path: str,
        method: str = "GET",
        payload: Optional[dict] = None
    ):
        agent_spec = await self.k8s.call_service(
            namespace=self.default_namespace,
            name=name,
            port=port,
            path=path,
            method=method,
            payload=payload
        )
        return AgentSpec.from_dict(agent_spec)

    async def delete_hosted_actions_deployment(self, name: str):
        return await self.k8s.delete_deployment(namespace=self.default_namespace, name=name)

    async def delete_hosted_actions_service(self, name: str):
        return await self.k8s.delete_service(namespace=self.default_namespace, name=name)

    async def build_hosted_actions_service(self, image: str, tag: str, zip_file_path: str) -> Tuple[str, Job]:
        return await self.build_gateway.build_image(
            namespace=self.default_namespace,
            image=image,
            tag=tag,
            zip_file_path=zip_file_path,
            registry_url=self.registry_url,
        )

    async def get_build_job(self, name: str) -> Optional[Job]:
        return await self.k8s.get_job(namespace=self.default_namespace, name=name)

    async def delete_build_job(self, name: str):
        return await self.k8s.delete_job(namespace=self.default_namespace, name=name)

    async def update_agent(self, agent: Agent) -> Agent:
        return await self.agent_repo.update(item=agent)


DAgentService = Annotated[AgentService, Depends(AgentService)]
