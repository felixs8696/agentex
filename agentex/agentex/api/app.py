import sys
from contextlib import asynccontextmanager
from enum import Enum
from typing import Optional, Dict, List

from fastapi import FastAPI, UploadFile, File, Body
from fastapi import Request
from fastapi import status
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.responses import Response
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

from agentex.api.schemas.agents import CreateAgentRequest, AgentModel
from agentex.api.schemas.tasks import CreateTaskRequest, TaskModel, ModifyTaskRequest
from agentex.config import dependencies
from agentex.domain.exceptions import GenericException
from agentex.domain.use_cases.agents_use_case import DAgentsUseCase
from agentex.domain.use_cases.tasks_use_case import DTaskUseCase
from agentex.utils.logging import make_logger
from agentex.utils.model_utils import BaseModel

logger = make_logger(__name__)


class HTTPExceptionWithMessage(HTTPException):
    """
    HTTPException with request ID header.
    """

    message: str | None

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
        message: Optional[str] = None,
    ):
        headers = headers or {}
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.message = message


@asynccontextmanager
async def lifespan(_: FastAPI):
    await dependencies.startup_global_dependencies()
    yield
    await dependencies.async_shutdown()
    dependencies.shutdown()


app = FastAPI(
    # debug=True,
    title=f"Agentex API",
    openapi_url="/openapi.json",
    docs_url="/swagger",
    redoc_url="/docs",
    swagger_ui_oauth2_redirect_url="/swagger/oauth2-redirect",
    root_path="",
    root_path_in_servers=False,
    lifespan=lifespan
)


@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, error: Exception):
    logger.error("Unhandled exception caught by route handler", exc_info=sys.exc_info())
    if isinstance(error, GenericException):
        http_error = HTTPExceptionWithMessage(status_code=error.code, detail=error.message)
    elif isinstance(error, RequestValidationError):
        # RequestValidationError is thrown by the FastAPI schema validation middleware
        http_error = HTTPExceptionWithMessage(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )
    elif isinstance(error, HTTPException):
        http_error = HTTPExceptionWithMessage(
            status_code=error.status_code, detail=error.detail
        )
    else:
        # This is the catch-all for everything. Because we don't know what generic exception was thrown
        http_error = HTTPExceptionWithMessage(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {error.__class__}: {error}",
        )
    logger.error(
        "Unhandled exception caught by route handler: " + str(http_error.detail),
        exc_info=sys.exc_info(),
    )
    return await http_exception_handler(request, http_error)


class RouteTag(str, Enum):
    AGENTS = "Agents"
    TASKS = "Tasks"
    ACTIONS = "Actions"


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


@app.get(path="/")
async def root():
    return {"message": "Welcome to Agentex!"}


class EchoMessage(BaseModel):
    message: str


@app.post(path="/echo")
async def echo(request: EchoMessage):
    return request


@app.post(
    path="/agents",
    response_model=AgentModel,
    tags=[RouteTag.AGENTS],
)
async def create_agent(
    agents_use_case: DAgentsUseCase,
    agent_package: UploadFile = File(...),
    request: CreateAgentRequest = Body(...),
) -> AgentModel:
    logger.info(f"Creating agent: {request}")
    agent = await agents_use_case.create(
        agent_package=agent_package,
        action_service_port=request.action_service_port,
        name=request.name,
        description=request.description,
        version=request.version,
    )
    return AgentModel.from_orm(agent)


@app.get(
    path="/agents/{agent_id}",
    response_model=AgentModel,
    tags=[RouteTag.AGENTS],
)
async def get_agent(
    agent_id: str,
    agents_use_case: DAgentsUseCase,
):
    agent = await agents_use_case.get(id=agent_id)
    return AgentModel.from_orm(agent)


@app.get(
    path="/agents",
    response_model=List[AgentModel],
    tags=[RouteTag.AGENTS],
)
async def list_agents(
    agents_use_case: DAgentsUseCase,
):
    agents = await agents_use_case.list()
    return [AgentModel.from_orm(agent) for agent in agents]


@app.delete(
    path="/agents/{agent_name}",
    response_model=AgentModel,
    tags=[RouteTag.AGENTS],
)
async def delete_agent(
    agent_name: str,
    agents_use_case: DAgentsUseCase,
):
    agent = await agents_use_case.delete(name=agent_name)
    return AgentModel.from_orm(agent)


@app.post(
    "/tasks",
    response_model=TaskModel,
    tags=[RouteTag.TASKS],
)
async def create_task(
    request: CreateTaskRequest,
    task_use_case: DTaskUseCase,
) -> TaskModel:
    task = await task_use_case.create(
        agent_name=request.agent_name,
        agent_version=request.agent_version,
        prompt=request.prompt,
        require_approval=request.require_approval,
    )
    return TaskModel.from_orm(task)


@app.get(
    "/tasks/{task_id}",
    response_model=TaskModel,
    tags=[RouteTag.TASKS],
)
async def get_task(
    task_id: str,
    task_use_case: DTaskUseCase,
) -> TaskModel:
    get_task_response = await task_use_case.get(task_id)
    return get_task_response


@app.get(
    path="/tasks",
    response_model=List[TaskModel],
    tags=[RouteTag.TASKS],
)
async def list_tasks(
    task_use_case: DTaskUseCase,
):
    tasks = await task_use_case.list()
    return [TaskModel.from_orm(task) for task in tasks]


@app.delete(
    "/tasks/{task_id}",
    response_model=TaskModel,
    tags=[RouteTag.TASKS],
)
async def delete_task(
    task_id: str,
    task_use_case: DTaskUseCase,
) -> TaskModel:
    task = await task_use_case.delete(id=task_id)
    return TaskModel.from_orm(task)


@app.post(
    "/tasks/{task_id}/modify",
    tags=[RouteTag.TASKS],
)
async def modify_task(
    request: ModifyTaskRequest,
    task_id: str,
    task_use_case: DTaskUseCase,
) -> None:
    return await task_use_case.modify(
        task_id=task_id,
        modification_request=request,
    )
