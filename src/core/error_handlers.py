from fastapi import Request
from fastapi.responses import JSONResponse

from core.exceptions import SpectraError
from core.logging import get_logger

logger = get_logger(__name__)


async def spectra_error_handler(request: Request, exc: SpectraError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("server_error", message=exc.message, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )
