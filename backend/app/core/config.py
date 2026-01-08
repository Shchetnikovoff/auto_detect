"""Конфигурация приложения AlloyPredictor."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Настройки приложения."""

    # App
    app_name: str = "AlloyPredictor"
    app_version: str = "1.0.0"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ML Models
    models_dir: Path = Path("app/ml/models")

    # Data
    datasets_dir: Path = Path("app/data/datasets")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Получить настройки (кэшированные)."""
    return Settings()


settings = get_settings()
