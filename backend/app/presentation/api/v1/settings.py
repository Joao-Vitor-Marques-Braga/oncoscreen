"""Model settings & runtime diagnostics endpoints."""

from fastapi import APIRouter, Depends

from app.presentation.dependencies.container import (
    AppContainer,
    CurrentUserContext,
    get_container,
    require_doctor,
)
from app.presentation.schemas.settings import (
    SystemStatusResponse,
    UpdateThresholdRequest,
)

router = APIRouter(prefix="/settings", tags=["Configurações do Modelo"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    _doctor: CurrentUserContext = Depends(require_doctor),
    container: AppContainer = Depends(get_container),
) -> SystemStatusResponse:
    ollama_health = await container.slm_engine.health_check()
    whatsapp_health = await container.whatsapp_client.health_check()
    return SystemStatusResponse(
        default_threshold=container.default_threshold,
        vision=container.vision_engine.status(),
        ollama=ollama_health,
        whatsapp=whatsapp_health,
    )


@router.put("/threshold")
async def update_default_threshold(
    body: UpdateThresholdRequest,
    _doctor: CurrentUserContext = Depends(require_doctor),
    container: AppContainer = Depends(get_container),
) -> dict[str, float]:
    container.default_threshold = body.default_threshold
    return {"default_threshold": container.default_threshold}

