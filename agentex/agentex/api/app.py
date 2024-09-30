import sys
from contextlib import asynccontextmanager
from enum import Enum
from typing import Optional, Dict

from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.responses import Response
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

from agentex.api.schemas.agents import CreateAgentResponse, CreateAgentRequest
from agentex.api.schemas.tasks import CreateTaskResponse, CreateTaskRequest
from agentex.config import dependencies
from agentex.domain.exceptions import GenericException
from agentex.domain.use_cases.crud.agent_crud_service import DAgentCRUDService
from agentex.domain.use_cases.task_use_case import DTaskUseCase
from agentex.utils.logging import make_logger

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
    path="/agents",
    response_model=CreateAgentResponse,
    tags=[RouteTag.AGENTS],
)
async def create_agent(
    request: CreateAgentRequest,
    agent_crud_service: DAgentCRUDService,
) -> CreateAgentResponse:
    logger.info(f"Creating agent: {request}")
    agent = await agent_crud_service.create(name=request.name)
    return CreateAgentResponse.from_orm(agent)


@app.post(
    "/tasks",
    response_model=CreateTaskResponse,
    tags=[RouteTag.TASKS],
)
async def submit_task(
    request: CreateTaskRequest,
    task_use_case: DTaskUseCase,
) -> CreateTaskResponse:
    task = await task_use_case.execute(
        agent_name=request.agent,
        prompt=request.prompt
    )
    return CreateTaskResponse.from_orm(task)
