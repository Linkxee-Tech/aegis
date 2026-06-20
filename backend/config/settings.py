"""
Centralized environment configuration for Aegis.

All values are loaded from environment variables (or a local .env file during
development). Nothing here should contain real secrets — see .env.example at
the project root for the variables this expects.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "Aegis"
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Qwen Cloud (DashScope OpenAI-compatible endpoint) ---
    qwen_api_key: str = Field(default="", description="API key for Qwen Cloud / DashScope")
    qwen_api_base: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_model_flash: str = "qwen-flash"
    qwen_model_plus: str = "qwen-plus"
    qwen_model_coder: str = "qwen-coder"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://aegis:aegis@localhost:5432/aegis"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Alibaba Cloud ---
    alibaba_cloud_access_key: str = ""
    alibaba_cloud_secret_key: str = ""
    alibaba_cloud_region: str = "ap-southeast-1"
    alibaba_oss_bucket: str = "aegis-reports"

    # --- Memory / Vector matching ---
    memory_similarity_threshold: float = 0.85
    memory_auto_apply_threshold: float = 0.92

    # --- Human approval ---
    approval_timeout_seconds: int = 900
    require_approval_for_high_risk: bool = True

    # --- Monitoring sources (Detective Agent) ---
    monitored_servers: list[str] = Field(default_factory=list)
    poll_interval_seconds: int = 15


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — import this rather than instantiating Settings() directly."""
    return Settings()
