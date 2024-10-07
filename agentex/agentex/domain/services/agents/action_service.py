from typing import Annotated, Optional, List

from fastapi import Depends

from agentex.adapters.containers.build_adapter_kaniko import DKanikoBuildGateway
from agentex.adapters.kubernetes.adapter_kubernetes import DKubernetesGateway
from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.actions import Action, ActionStatus
from agentex.domain.entities.job import Job
from agentex.domain.exceptions import ClientError
from agentex.domain.services.agents.action_repository import DActionRepository
from agentex.domain.services.agents.agent_repository import DAgentRepository
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class ActionService:
    def __init__(
        self,
        build_gateway: DKanikoBuildGateway,
        action_repository: DActionRepository,
        agent_repository: DAgentRepository,
        kubernetes_gateway: DKubernetesGateway,
        environment_variables: DEnvironmentVariables,
    ):
        self.build_namespace = "default"
        self.k8s = kubernetes_gateway
        self.build_gateway = build_gateway
        self.action_repo = action_repository
        self.agent_repo = agent_repository
        self.registry_url = environment_variables.BUILD_REGISTRY_URL

    async def create_action(self, action: Action, agents: List[str]):
        action = await self.action_repo.create(item=action)

        if agents:
            logger.info("Associating agents with action")
            await self.agent_repo.associate_agents_with_actions(
                agent_names=agents,
                action_ids=[action.id]
            )

        return action

    async def build_action(
        self,
        image: str,
        tag: str,
        zip_file_path: str
    ):
        return await self.build_gateway.build_image(
            namespace=self.build_namespace,
            image=image,
            tag=tag,
            zip_file_path=zip_file_path,
            registry_url=self.registry_url,
        )

    async def get_action_build_job(self, action_name: Optional[str] = None, action: Optional[Action] = None) -> Job:
        if not action and not action_name:
            raise ClientError("Either 'action' or 'action_name' must be provided")

        if not action:
            action = await self.action_repo.get(name=action_name)

        job_name = action.build_job_name
        job_namespace = action.build_job_namespace
        return await self.k8s.get_job(namespace=job_namespace, name=job_name)

    async def update_action(
        self,
        action: Action
    ) -> Action:
        return await self.action_repo.update(item=action)


DActionService = Annotated[ActionService, Depends(ActionService)]
