from typing import Annotated

from fastapi import Depends

from agentex.adapters.containers.build_adapter_kaniko import DKanikoBuildGateway
from agentex.adapters.kubernetes.adapter_kubernetes import DKubernetesGateway
from agentex.config.dependencies import DEnvironmentVariables


class ActionService:
    def __init__(
        self,
        build_gateway: DKanikoBuildGateway,
        kubernetes_gateway: DKubernetesGateway,
        environment_variables: DEnvironmentVariables
    ):
        self.build_namespace = "default"
        self.k8s = kubernetes_gateway
        self.build_gateway = build_gateway
        self.registry_url = environment_variables.BUILD_REGISTRY_URL

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


DActionService = Annotated[ActionService, Depends(ActionService)]
