import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from agentex.adapters.kv_store.adapter_redis import RedisRepository
from agentex.adapters.llm.adapter_litellm import LiteLLMGateway
from agentex.config.dependencies import GlobalDependencies
from agentex.config.environment_variables import EnvironmentVariables
from agentex.domain.services.agents.agent_state_repository import AgentStateRepository
from agentex.domain.services.agents.agent_state_service import AgentStateService
from agentex.domain.workflows.agent_task_workflow import AgentTaskWorkflow, AgentTaskActivities
from agentex.domain.workflows.constants import AGENT_TASK_TASK_QUEUE
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


async def run_worker(task_queue=AGENT_TASK_TASK_QUEUE):
    environment_variables = EnvironmentVariables.refresh()
    temporal_address = environment_variables.TEMPORAL_ADDRESS
    logger.info(f"temporal address: {temporal_address}")

    global_dependencies = GlobalDependencies()
    await global_dependencies.load()

    client = global_dependencies.temporal_client

    logger.info(
        f"Continuing on from run_worker with temporal client - {client is not None}. Task queue: {task_queue}"
    )

    agent_activities = AgentTaskActivities(
        agent_state_service=AgentStateService(
            repository=AgentStateRepository(
                memory_repo=RedisRepository(
                    redis_url=environment_variables.REDIS_URL,
                )
            )
        ),
        llm_gateway=LiteLLMGateway(
            environment_variables=environment_variables,
        ),
    )

    # Run the worker
    worker = Worker(
        client,
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
    await worker.run()


async def main():
    await run_worker()


if __name__ == "__main__":
    asyncio.run(main())
