import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web
from temporalio.client import Client as TemporalClient
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from agentex.adapters.kv_store.adapter_redis import RedisRepository
from agentex.adapters.llm.adapter_litellm import LiteLLMGateway
from agentex.config.dependencies import GlobalDependencies
from agentex.config.environment_variables import EnvironmentVariables
from agentex.domain.services.agents.agent_state_repository import AgentStateRepository
from agentex.domain.services.agents.agent_state_service import AgentStateService
from agentex.domain.workflows.agent_task_workflow import AgentTaskWorkflow, AgentTaskActivities
from agentex.domain.workflows.constants import AGENT_TASK_TASK_QUEUE, BUILD_ACTION_TASK_QUEUE
from agentex.domain.workflows.create_action_workflow import CreateActionWorkflow, CreateActionActivities

from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class HealthStatus:

    def __init__(self, health: bool = False):
        self.healthy = health

    def set_healthy(self, status: bool):
        self.healthy = status


class OverallHealthStatus:

    def __init__(self):
        self.agent_task_worker_status = HealthStatus(health=False)
        self.create_action_worker_status = HealthStatus(health=False)

    def get_health(self) -> bool:
        return all([self.agent_task_worker_status.healthy, self.create_action_worker_status.healthy])


async def health_check(health_status: OverallHealthStatus):
    return web.json_response(health_status.get_health())


async def run_agent_task_worker(
    temporal_client: TemporalClient,
    environment_variables: EnvironmentVariables,
    health_status: OverallHealthStatus,
    task_queue=AGENT_TASK_TASK_QUEUE,
):
    try:
        agent_activities = AgentTaskActivities(
            agent_state_service=AgentStateService(
                repository=AgentStateRepository(
                    memory_repo=RedisRepository(
                        environment_variables=environment_variables,
                    )
                )
            ),
            llm_gateway=LiteLLMGateway(
                environment_variables=environment_variables,
            ),
        )

        # Run the worker
        worker = Worker(
            temporal_client,
            task_queue=task_queue,
            activity_executor=ThreadPoolExecutor(
                max_workers=10,
            ),
            workflows=[
                AgentTaskWorkflow,
            ],
            activities=[
                agent_activities.init_task_state,
                agent_activities.decide_action,
                agent_activities.take_action,
            ],
            workflow_runner=UnsandboxedWorkflowRunner(),
            max_concurrent_activities=environment_variables.TEMPORAL_WORKER_MAX_ACTIVITIES_PER_WORKER,
            build_id=str(uuid.uuid4()),
        )

        logger.info(f"Starting workers for task queue: {task_queue}")
        # Eagerly set the worker status to healthy
        health_status.agent_task_worker_status.set_healthy(True)
        logger.info(f"Running workers for task queue: {task_queue}")
        await worker.run()

    except Exception as e:
        logger.error(f"Agent task worker encountered an error: {e}")
        health_status.agent_task_worker_status.set_healthy(False)


async def run_create_action_worker(
    temporal_client: TemporalClient,
    environment_variables: EnvironmentVariables,
    health_status: OverallHealthStatus,
    task_queue=BUILD_ACTION_TASK_QUEUE,
):
    try:
        create_action_activities = CreateActionActivities(
            action_repository=AgentStateRepository(
                memory_repo=RedisRepository(
                    environment_variables=environment_variables,
                )
            ),
            agent_repository=AgentStateRepository(
                memory_repo=RedisRepository(
                    environment_variables=environment_variables,
                )
            ),
            action_service=AgentStateService(
                repository=AgentStateRepository(
                    memory_repo=RedisRepository(
                        environment_variables=environment_variables,
                    )
                )
            ),
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
                CreateActionWorkflow,
            ],
            activities=[
                create_action_activities.create_action,
                create_action_activities.build_action,
                create_action_activities.get_build_job,
                create_action_activities.update_action_status,
            ],
            workflow_runner=UnsandboxedWorkflowRunner(),
            max_concurrent_activities=environment_variables.TEMPORAL_WORKER_MAX_ACTIVITIES_PER_WORKER,
            build_id=str(uuid.uuid4()),
        )

        logger.info(f"Starting workers for task queue: {task_queue}")
        # Eagerly set the worker status to healthy
        health_status.create_action_worker_status.set_healthy(True)
        await worker.run()
        logger.info(f"Running workers for task queue: {task_queue}")
    except Exception as e:
        logger.error(f"Create action worker encountered an error: {e}")
        health_status.create_action_worker_status.set_healthy(False)


async def run_workers(health_status: OverallHealthStatus):
    environment_variables = EnvironmentVariables.refresh()
    temporal_address = environment_variables.TEMPORAL_ADDRESS
    logger.info(f"temporal address: {temporal_address}")

    global_dependencies = GlobalDependencies()
    await global_dependencies.load()

    client = global_dependencies.temporal_client

    await asyncio.gather(
        run_agent_task_worker(
            temporal_client=client,
            environment_variables=environment_variables,
            health_status=health_status
        ),
        run_create_action_worker(
            temporal_client=client,
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
