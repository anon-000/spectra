from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.router import api_router, webhook_router
from config import get_settings
from core.error_handlers import spectra_error_handler
from core.exceptions import SpectraError
from core.logging import setup_logging
from core.middleware import RequestIdMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Spectra", version="0.1.0", lifespan=lifespan)

    # CORS — must be added before other middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_exception_handler(SpectraError, spectra_error_handler)
    app.include_router(api_router)
    app.include_router(webhook_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
