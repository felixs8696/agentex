import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web
from temporalio.client import Client as TemporalClient
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from agentex.adapters.containers.build_adapter_kaniko import KanikoBuildGateway
from agentex.adapters.http.adapter_httpx import HttpxGateway
from agentex.adapters.kubernetes.adapter_kubernetes import KubernetesGateway
from agentex.config.dependencies import GlobalDependencies, database_async_read_write_session_maker
from agentex.config.environment_variables import EnvironmentVariables
from agentex.domain.services.agents.agent_repository import AgentRepository
from agentex.domain.services.agents.agent_service import AgentService
from agentex.domain.workflows.activities.build_agent import BuildAgentActivities
from agentex.domain.workflows.constants import BUILD_AGENT_TASK_QUEUE
from agentex.domain.workflows.create_agent_workflow import BuildAgentWorkflow
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class HealthStatus:

    def __init__(self, health: bool = False):
        self.healthy = health

    def set_healthy(self, status: bool):
        self.healthy = status


class OverallHealthStatus:

    def __init__(self):
        self.create_agent_worker_status = HealthStatus(health=False)

    def get_health(self) -> bool:
        return all([self.create_agent_worker_status.healthy])


async def health_check(health_status: OverallHealthStatus):
    return web.json_response(health_status.get_health())


async def run_create_agent_worker(
    temporal_client: TemporalClient,
    global_dependencies: GlobalDependencies,
    environment_variables: EnvironmentVariables,
    health_status: OverallHealthStatus,
    task_queue=BUILD_AGENT_TASK_QUEUE,
):
    try:
        async_read_write_session_maker = database_async_read_write_session_maker(
            db_async_read_write_engine=global_dependencies.database_async_read_write_engine,
        )
        agent_repository = AgentRepository(
            async_read_write_session_maker=async_read_write_session_maker,
        )
        k8s_gateway = KubernetesGateway(
            http_gateway=HttpxGateway(),
            environment_variables=environment_variables,
        )
        build_gateway = KanikoBuildGateway(
            kubernetes_gateway=k8s_gateway,
            environment_variables=environment_variables,
        )
        agent_service = AgentService(
            build_gateway=build_gateway,
            agent_repository=agent_repository,
            kubernetes_gateway=k8s_gateway,
            environment_variables=environment_variables,
        )

        create_agent_activities = BuildAgentActivities(
            agent_service=agent_service,
            environment_variables=environment_variables,
        )

        build_agent_activities = BuildAgentActivities(
            agent_service=agent_service,
            environment_variables=environment_variables,
        )

        # Run the worker
        worker = Worker(
            temporal_client,
            task_queue=task_queue,
            activity_executor=ThreadPoolExecutor(
                max_workers=10,
            ),
            workflows=[
                BuildAgentWorkflow,
            ],
            activities=[
                create_agent_activities.update_agent,
                build_agent_activities.build_agent_image,
                build_agent_activities.get_build_job,
                build_agent_activities.delete_build_job,
                build_agent_activities.create_agent_service,
                build_agent_activities.create_agent_deployment,
                build_agent_activities.create_agent_pod_disruption_budget,
                build_agent_activities.get_agent_service,
                build_agent_activities.get_agent_deployment,
                build_agent_activities.delete_agent_service,
                build_agent_activities.delete_agent_deployment,
                build_agent_activities.update_agent_status,
            ],
            workflow_runner=UnsandboxedWorkflowRunner(),
            max_concurrent_activities=environment_variables.TEMPORAL_WORKER_MAX_ACTIVITIES_PER_WORKER,
            build_id=str(uuid.uuid4()),
        )

        logger.info(f"Starting workers for task queue: {task_queue}")
        # Eagerly set the worker status to healthy
        health_status.create_agent_worker_status.set_healthy(True)
        await worker.run()
        logger.info(f"Running workers for task queue: {task_queue}")
    except Exception as e:
        logger.error(f"Create agent worker encountered an error: {e}")
        health_status.create_agent_worker_status.set_healthy(False)


async def run_workers(health_status: OverallHealthStatus):
    environment_variables = EnvironmentVariables.refresh()
    temporal_address = environment_variables.TEMPORAL_ADDRESS
    logger.info(f"temporal address: {temporal_address}")

    global_dependencies = GlobalDependencies()
    await global_dependencies.load()

    client = global_dependencies.temporal_client

    await asyncio.gather(
        run_create_agent_worker(
            temporal_client=client,
            global_dependencies=global_dependencies,
            environment_variables=environment_variables,
            health_status=health_status
        ),

    )


async def start_health_check_server(health_status: OverallHealthStatus):
    app = web.Application()
    app.router.add_get('/readyz', lambda request: health_check(health_status))  # Updated endpoint

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)  # Expose on port 80
    await site.start()
    logger.info("Health check server running on http://0.0.0.0:80/readyz")


async def main():
    health_status = OverallHealthStatus()  # Create health status object
    await start_health_check_server(health_status)
    await run_workers(health_status=health_status)


if __name__ == "__main__":
    asyncio.run(main())
