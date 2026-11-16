"""JWT token provider implementation using PyJWT."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.domain.interfaces.security import TokenProvider


class JWTTokenProvider(TokenProvider):
    """Creates and validates HS256 JWT tokens."""

    def __init__(self, secret_key: str, algorithm: str = "HS256", expire_minutes: int = 480) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    def create_access_token(self, payload: dict[str, Any]) -> str:
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._expire_minutes)
        to_encode["exp"] = expire
        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])

