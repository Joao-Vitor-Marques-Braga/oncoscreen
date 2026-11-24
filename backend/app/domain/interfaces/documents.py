"""Abstract file storage contract for lightweight image persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod


class FileStorage(ABC):
    """Port for lightweight local file storage (compressed images)."""

    @abstractmethod
    def save_bytes(self, relative_path: str, data: bytes) -> str:
        """Persist bytes under storage root and return the relative path."""

    @abstractmethod
    def read_bytes(self, relative_path: str) -> bytes:
        """Read bytes from a stored relative path."""

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Check whether a stored file exists."""
