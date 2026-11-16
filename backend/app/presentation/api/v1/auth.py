"""Authentication endpoints."""

from fastapi import APIRouter, Depends

from app.application.use_cases.auth.authenticate_user import AuthenticateUserUseCase
from app.infrastructure.database.repositories import SQLAlchemyUserRepository
from app.presentation.dependencies.container import (
    AppContainer,
    CurrentUserContext,
    get_container,
    get_current_user,
    get_user_repo,
)
from app.presentation.schemas.auth import CurrentUserResponse, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repo),
    container: AppContainer = Depends(get_container),
) -> TokenResponse:
    use_case = AuthenticateUserUseCase(
        user_repo=user_repo,
        password_hasher=container.password_hasher,
        token_provider=container.token_provider,
    )
    dto = await use_case.execute(identifier=body.identifier, password=body.password)
    return TokenResponse(
        access_token=dto.access_token,
        token_type=dto.token_type,
        user_id=dto.user_id,
        full_name=dto.full_name,
        role=dto.role.value,
        patient_id=dto.patient_id,
    )


@router.get("/me", response_model=CurrentUserResponse)
async def me(
    current_user: CurrentUserContext = Depends(get_current_user),
) -> CurrentUserResponse:
    return CurrentUserResponse(
        user_id=current_user.user_id,
        full_name=current_user.full_name,
        role=current_user.role.value,
        patient_id=current_user.patient_id,
    )

