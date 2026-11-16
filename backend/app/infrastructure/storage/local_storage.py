"""Local file storage implementation for compressed images and PDFs."""

from __future__ import annotations

from pathlib import Path

from app.domain.interfaces.documents import FileStorage


class LocalFileStorage(FileStorage):
    """Stores binary artifacts on the local filesystem under a root directory."""

    def __init__(self, root_dir: Path) -> None:
        self._root = root_dir.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, relative_path: str) -> Path:
        target = (self._root / relative_path).resolve()
        if not str(target).startswith(str(self._root)):
            raise ValueError("Caminho de arquivo inválido fora do diretório de armazenamento.")
        return target

    def save_bytes(self, relative_path: str, data: bytes) -> str:
        target = self._safe_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return relative_path.replace("\\", "/")

    def read_bytes(self, relative_path: str) -> bytes:
        target = self._safe_path(relative_path)
        return target.read_bytes()

    def exists(self, relative_path: str) -> bool:
        try:
            target = self._safe_path(relative_path)
            return target.is_file()
        except ValueError:
            return False

