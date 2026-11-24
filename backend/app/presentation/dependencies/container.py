"""Dependency Injection Container and RBAC dependencies for FastAPI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.domain.entities.user import UserRole
from app.domain.interfaces.documents import FileStorage
from app.domain.interfaces.slm_engine import SLMEngine
from app.domain.interfaces.vision_engine import VisionEngine
from app.domain.interfaces.whatsapp_client import WhatsAppClient
from app.domain.services.clinical_guardrails import ClinicalGuardrailsService
from app.infrastructure.config import Settings
from app.infrastructure.database.repositories import (
    SQLAlchemyExamRepository,
    SQLAlchemyPatientRepository,
    SQLAlchemyUserRepository,
)
from app.infrastructure.database.session import create_engine_and_sessionmaker
from app.infrastructure.llm.ollama_slm_client import OllamaSLMClient
from app.infrastructure.messaging.evolution_whatsapp_adapter import EvolutionWhatsAppAdapter
from app.infrastructure.ml.efficientnet_vision_engine import EfficientNetVisionEngine
from app.infrastructure.security.jwt_handler import JWTTokenProvider
from app.infrastructure.security.password_hasher import BcryptPasswordHasher
from app.infrastructure.storage.local_storage import LocalFileStorage

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUserContext:
    user_id: str
    full_name: str
    role: UserRole
    patient_id: Optional[str] = None


class AppContainer:
    """Holds singleton infrastructure adapters and configuration."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.default_threshold: float = settings.default_cnn_threshold

        self.engine: AsyncEngine
        self.session_factory: async_sessionmaker[AsyncSession]
        self.engine, self.session_factory = create_engine_and_sessionmaker(settings.database_url)

        self.password_hasher = BcryptPasswordHasher()
        self.token_provider = JWTTokenProvider(
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expire_minutes=settings.jwt_expire_minutes,
        )
        self.file_storage: FileStorage = LocalFileStorage(settings.storage_path)
        self.guardrails_service = ClinicalGuardrailsService()

        self.vision_engine: VisionEngine = EfficientNetVisionEngine(
            weights_path=settings.weights_path,
            num_threads=settings.torch_num_threads,
        )
        self.slm_engine: SLMEngine = OllamaSLMClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
        self.whatsapp_client: WhatsAppClient = EvolutionWhatsAppAdapter(
            api_url=settings.evolution_api_url,
            api_key=settings.evolution_api_key,
            instance_name=settings.evolution_instance_name,
        )


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


async def get_db_session(
    container: AppContainer = Depends(get_container),
) -> AsyncGenerator[AsyncSession, None]:
    async with container.session_factory() as session:
        yield session


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    container: AppContainer = Depends(get_container),
) -> CurrentUserContext:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente.",
        )
    try:
        payload = container.token_provider.decode_token(credentials.credentials)
        return CurrentUserContext(
            user_id=str(payload["sub"]),
            full_name=str(payload.get("full_name", "")),
            role=UserRole(payload["role"]),
            patient_id=payload.get("patient_id"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        ) from exc


async def require_doctor(
    current_user: CurrentUserContext = Depends(get_current_user),
) -> CurrentUserContext:
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao perfil Médico (DOCTOR).",
        )
    return current_user


def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session)


def get_patient_repo(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyPatientRepository:
    return SQLAlchemyPatientRepository(session)


def get_exam_repo(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyExamRepository:
    return SQLAlchemyExamRepository(session)

