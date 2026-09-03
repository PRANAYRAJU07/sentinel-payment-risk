"""
Sentinel Backend — Application Configuration
Loads all settings from environment variables.
NEVER hardcode secrets here.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Sentinel"
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_debug: bool = True
    demo_mode: bool = False

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://sentinel:sentinel_password@localhost:5432/sentinel_db"

    # Security
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Razorpay (TEST MODE ONLY)
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # LLM
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"

    # Risk Policy Thresholds (configurable)
    risk_low_threshold: int = 40
    risk_high_threshold: int = 75
    
    # Risk Aggregation Weights
    risk_ml_weight: float = 0.60
    risk_behavior_weight: float = 0.20
    risk_rule_weight: float = 0.15
    risk_graph_weight: float = 0.05

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def has_razorpay(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    @property
    def has_llm(self) -> bool:
        return bool(self.llm_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
