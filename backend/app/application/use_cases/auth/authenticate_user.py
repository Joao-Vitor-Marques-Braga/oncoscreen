"""Authenticate user (Doctor by email or Patient by CPF)."""

from __future__ import annotations

import re

from app.application.dtos import AuthTokenDTO
from app.application.exceptions import AuthenticationError
from app.domain.interfaces.repositories import UserRepository
from app.domain.interfaces.security import PasswordHasher, TokenProvider


class AuthenticateUserUseCase:
    """Validates credentials and issues a JWT access token."""

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        token_provider: TokenProvider,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._token_provider = token_provider

    async def execute(self, identifier: str, password: str) -> AuthTokenDTO:
        normalized = identifier.strip()
        # If identifier is not an email, normalize CPF digits
        if "@" not in normalized:
            normalized = re.sub(r"\D", "", normalized)

        user = await self._user_repo.get_by_email_or_cpf(normalized)
        if not user or not user.is_active:
            raise AuthenticationError("Credenciais inválidas.")

        if not self._password_hasher.verify(password, user.password_hash):
            raise AuthenticationError("Credenciais inválidas.")

        token = self._token_provider.create_access_token(
            {
                "sub": user.id,
                "role": user.role.value,
                "full_name": user.full_name,
                "patient_id": user.patient_id,
            }
        )
        return AuthTokenDTO(
            access_token=token,
            token_type="bearer",
            user_id=user.id,
            full_name=user.full_name,
            role=user.role,
            patient_id=user.patient_id,
        )

