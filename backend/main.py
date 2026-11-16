"""OncoScreen.AI (OralCare-Vision CDSS) FastAPI Entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database.seed import seed_initial_doctor
from app.infrastructure.database.session import Base
from app.presentation.api.v1 import auth, exams, metrics, patients, settings as settings_router, triage
from app.presentation.dependencies.container import AppContainer


def create_app(custom_settings: Settings | None = None) -> FastAPI:
    cfg = custom_settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        container = AppContainer(cfg)
        app.state.container = container

        async with container.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with container.session_factory() as session:
            await seed_initial_doctor(session, container.password_hasher)

        yield
        await container.engine.dispose()

    app = FastAPI(
        title="OncoScreen.AI — OralCare-Vision CDSS",
        description="Sistema Multimodal de Apoio à Decisão Clínica para Triagem Precoce de HNSCC.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(_req: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)})

    @app.exception_handler(AuthorizationError)
    async def authz_error_handler(_req: Request, exc: AuthorizationError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_req: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_handler(_req: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)})

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "oncoscreen-ai-backend"}

    api_prefix = "/api/v1"
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(patients.router, prefix=api_prefix)
    app.include_router(triage.router, prefix=api_prefix)
    app.include_router(exams.router, prefix=api_prefix)
    app.include_router(metrics.router, prefix=api_prefix)
    app.include_router(settings_router.router, prefix=api_prefix)

    return app


app = create_app()

