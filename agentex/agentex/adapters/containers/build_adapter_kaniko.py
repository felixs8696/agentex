import os
import uuid
from typing import Annotated

from fastapi import Depends
from kubernetes_asyncio import client

from agentex.adapters.containers.build_port import ContainerBuildGateway
from agentex.adapters.kubernetes.adapter_kubernetes import DKubernetesGateway
from agentex.config.dependencies import DEnvironmentVariables


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
    ):
        unique_id = self._uid()
        _image = image.replace('/', '-').replace('_', '-').lower()
        job_name = f"build-{_image}-{tag}-{unique_id}"

        # Create the Kaniko Job spec
        job = client.V1Job(
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
                                    f"--destination={registry_url}/{image}:{tag}",
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

        return await self.k8s.create_job(namespace=namespace, job=job)


#
#     def monitor_job_status(self, job_name: str) -> str:
#         """Monitor job status and return logs."""
#         job_status = self.batch_v1.read_namespaced_job_status(job_name, self.namespace)
#         if job_status.status.succeeded:
#             print(f"Job '{job_name}' succeeded.")
#         elif job_status.status.failed:
#             print(f"Job '{job_name}' failed.")
#         return job_status.status
#
#
# # Instantiate the manager and create the job
# kaniko_manager = KanikoBuildManager(
#     registry_url="harbor.yourdomain.com/library",
#     namespace="default"
# )
#
# # Define the tarball path, the image name, and the job name
# tar_file_path = "/path/to/your/tarball.tar"
# image_name = "my-image"
# job_name = "kaniko-build-job"
#
# # Submit the Kaniko job
# kaniko_manager.submit_kaniko_job(tar_file_path, image_name, job_name)
#
# # Monitor the job status
# status = kaniko_manager.monitor_job_status(job_name)

DKanikoBuildGateway = Annotated[KanikoBuildGateway, Depends(KanikoBuildGateway)]
