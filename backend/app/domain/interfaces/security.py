"""Abstract security contracts for password hashing and token issuance."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PasswordHasher(ABC):
    """Port for password hashing and verification."""

    @abstractmethod
    def hash(self, plain_password: str) -> str:
        """Hash a plain-text password."""

    @abstractmethod
    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Verify plain-text password against stored hash."""


class TokenProvider(ABC):
    """Port for creating and decoding authentication tokens."""

    @abstractmethod
    def create_access_token(self, payload: dict[str, Any]) -> str:
        """Sign and return a bearer access token."""

    @abstractmethod
    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate an access token."""

