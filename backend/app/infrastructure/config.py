"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for OncoScreen.AI backend."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Security
    jwt_secret_key: str = "oncoscreen-dev-secret-change-in-production-256bit"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Database & Storage
    database_url: str = "sqlite+aiosqlite:///./storage/oncoscreen.db"
    storage_dir: str = "./storage"
    weights_path: str = "./weights/melhor_modelo_visao.pth"

    # ML / CPU Optimization
    torch_num_threads: int = 4
    default_cnn_threshold: float = 0.50

    # Ollama Local SLM
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout_seconds: int = 60

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()

