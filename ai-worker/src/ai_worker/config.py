from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_queue_name: str = "ai_jobs"
    job_result_expires_seconds: int = 3600
    job_soft_time_limit_seconds: int = 90
    job_time_limit_seconds: int = 120

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.6-luna"
    openai_timeout_seconds: float = 60.0
    openai_max_output_tokens: int = 1800
    openai_max_retries: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
