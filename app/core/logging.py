import sys
import uuid

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


def configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | req={extra[request_id]} | {message}",
    )
    logger.configure(extra={"request_id": "-"})


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Tags every request/log line with a correlation ID, returned via the X-Request-ID header."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        with logger.contextualize(request_id=request_id):
            response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
