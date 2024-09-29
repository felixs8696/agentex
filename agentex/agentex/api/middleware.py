import sys
from typing import Optional, Dict

from fastapi import Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

from agentex.domain.exceptions import GenericException
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
