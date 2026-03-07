from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    APP_NAME: str = "SafePassage"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    SECRET_KEY: str = Field(min_length=32)
    ALLOWED_HOSTS: list[str] = ["*"]
    DATABASE_URL: str = "postgresql://safepassage:safepassage_dev@postgres:5432/safepassage"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_ALERT_CHANNEL: str = "safepassage:alerts"
    ANTHROPIC_API_KEY: str = "not_set"
    AI_MODEL: str = "claude-sonnet-4-20250514"
    AI_MAX_TOKENS: int = 1024
    AI_RISK_ASSESSMENT_PROMPT: str = "You are a humanitarian AI assistant specializing in war zone civilian safety and evacuation planning."
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    MAX_REPORT_RADIUS_KM: float = 50.0
    ROUTE_DANGER_THRESHOLD: float = 0.7
    SHELTER_SEARCH_RADIUS_KM: float = 30.0
    SOS_BROADCAST_RADIUS_KM: float = 100.0
    RATE_LIMIT_REPORTS: str = "30/minute"
    RATE_LIMIT_SOS: str = "5/minute"
    RATE_LIMIT_AI: str = "10/minute"
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS_PER_ZONE: int = 10000
    vonage_api_key: str = ""
    vonage_api_secret: str = ""
    vonage_from: str = "SafePassage"
    alert_phone: str = ""

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def database_url_async(self) -> str:
        url = str(self.DATABASE_URL)
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
