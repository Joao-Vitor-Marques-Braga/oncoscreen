"""Bcrypt password hashing implementation."""

from __future__ import annotations

import bcrypt

from app.domain.interfaces.security import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """Hashes and verifies passwords using bcrypt."""

    def hash(self, plain_password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify(self, plain_password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except Exception:
            return False

