import uuid
from typing import Annotated, Tuple

from fastapi import Depends
from kubernetes_asyncio import client

from agentex.adapters.containers.build_port import ContainerBuildGateway
from agentex.adapters.kubernetes.adapter_kubernetes import DKubernetesGateway
from agentex.config.dependencies import DEnvironmentVariables
from agentex.domain.entities.job import Job


class KanikoBuildGateway(ContainerBuildGateway):
    def __init__(
        self,
        kubernetes_gateway: DKubernetesGateway,
        environment_variables: DEnvironmentVariables,
    ):
        self.k8s = kubernetes_gateway
        self.build_contexts_path = environment_variables.BUILD_CONTEXTS_PATH
        self.build_context_pvc_name = environment_variables.BUILD_CONTEXT_PVC_NAME
        self.build_registry_secret_name = environment_variables.BUILD_REGISTRY_SECRET_NAME

    @staticmethod
    def _uid():
        return uuid.uuid4().hex[:8]

    async def build_image(
        self,
        namespace: str,
        image: str,
        tag: str,
        zip_file_path: str,
        registry_url: str,
    ) -> Tuple[str, Job]:
        unique_id = self._uid()
        _image = image.replace('/', '-').replace('_', '-').lower()
        job_name = f"build-{_image}-{tag}-{unique_id}"
        full_image_url = f"{registry_url}/{image}:{tag}"

        # Create the Kaniko Job spec
        job_spec = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=job_name),
            spec=client.V1JobSpec(
                template=client.V1PodTemplateSpec(
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="kaniko",
                                image="gcr.io/kaniko-project/executor:latest",
                                image_pull_policy="IfNotPresent",
                                args=[
                                    f"--context=tar://{zip_file_path}",  # Use tar if you compress the zip
                                    "--dockerfile=Dockerfile",  # Adjust based on your file structure
                                    f"--destination={full_image_url}",
                                ],
                                env=[
                                    client.V1EnvVar(
                                        name="DOCKER_CONFIG",
                                        value="/kaniko/.docker"
                                    )
                                ],
                                lifecycle=client.V1Lifecycle(
                                    pre_stop=client.V1LifecycleHandler(
                                        _exec=client.V1ExecAction(
                                            command=["sh", "-c", f"rm -f {zip_file_path}"]
                                        )
                                    )
                                ),
                                volume_mounts=[
                                    client.V1VolumeMount(
                                        name=self.build_context_pvc_name,  # Mount the existing PVC
                                        mount_path=self.build_contexts_path  # Mount the PVC where the zip is located
                                    ),
                                    client.V1VolumeMount(
                                        name="build-registry-secret",  # Mount the existing PVC
                                        mount_path="/kaniko/.docker"  # Mount the PVC where the zip is located
                                    ),
                                ]
                            )
                        ],
                        restart_policy="Never",
                        volumes=[
                            client.V1Volume(
                                name=self.build_context_pvc_name,
                                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                    claim_name=self.build_context_pvc_name,
                                ),
                            ),
                            client.V1Volume(
                                name="build-registry-secret",
                                secret=client.V1SecretVolumeSource(
                                    secret_name=self.build_registry_secret_name,
                                ),
                            ),
                        ],
                    )
                )
            )
        )

        job = await self.k8s.create_job(namespace=namespace, job=job_spec)

        return full_image_url, job


DKanikoBuildGateway = Annotated[KanikoBuildGateway, Depends(KanikoBuildGateway)]
