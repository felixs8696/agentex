from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI
from fastapi import status
from starlette.responses import Response

from agentex.api.schemas.tasks import TaskResponse, TaskRequest
from agentex.config import dependencies
from agentex.internal.services.task_service import DTaskService
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await dependencies.startup_global_dependencies()
    yield
    await dependencies.async_shutdown()
    dependencies.shutdown()


app = FastAPI(
    title=f"Agentex API",
    openapi_url="/openapi.json",
    docs_url="/swagger",
    redoc_url="/docs",
    swagger_ui_oauth2_redirect_url="/swagger/oauth2-redirect",
    root_path="",
    root_path_in_servers=False,
    lifespan=lifespan
)


class RouteTag(str, Enum):
    TASKS = "Tasks"


def healthcheck() -> Response:
    """Returns 200 if the app is healthy."""
    return Response(status_code=status.HTTP_200_OK)


health_check_urls = ["healthcheck", "healthz", "readyz"]
for health_check_url in health_check_urls:
    app.get(
        path=f"/{health_check_url}",
        operation_id=health_check_url,
        include_in_schema=False
    )(healthcheck)


@app.post(
    "/tasks",
    response_model=TaskResponse,
    tags=[RouteTag.TASKS],
)
async def submit_task(
    task_service: DTaskService,
    request: TaskRequest,
) -> TaskResponse:
    message = await task_service.execute(prompt=request.prompt)
    return TaskResponse(
        content=message.content,
    )
