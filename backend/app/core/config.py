from functools import lru_cache
from pathlib import Path
from typing import List, Union
from pydantic import Field, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "JOMO"
    API_PREFIX: str = "/api/v1"
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    DATABASE_URL: str = "sqlite:///./jomo_dev.db"
    # Optional direct/session connection when the runtime uses a transaction pooler.
    MIGRATION_DATABASE_URL: str = ""

    AUTH_PROVIDER: str = "supabase"
    AUTH_ISSUER_URL: str = ""
    AUTH_JWKS_URL: str = ""
    AUTH_PUBLIC_KEY: str = ""
    AUTH_AUDIENCE: str = "authenticated"
    AUTH_TIMEOUT_SECONDS: float = Field(default=5, gt=0, le=30)
    FRONTEND_URL: str = "http://localhost:3000"
    DEV_AUTH_ENABLED: bool = False
    DEV_AUTH_SECRET: str = "jomo-dev-super-secret-key-change-in-production"

    STORAGE_PROVIDER: str = "supabase"
    STORAGE_BUCKET: str = "activity-proofs"

    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"
    REQUEST_MAX_BODY_BYTES: int = Field(default=1024 * 1024, ge=1)
    RATE_LIMIT_IP_PER_MINUTE: int = Field(default=600, ge=1)
    RATE_LIMIT_USER_PER_MINUTE: int = Field(default=120, ge=1)

    SCREENING_MAX_TEXT_LENGTH: int = Field(default=10000, ge=1, le=10000)
    SCREENING_STORE_RAW_TEXT: bool = False

    LOCATION_RETENTION_HOURS: int = 24

    AI_MISSION_PROVIDER: str = "catalogue"
    AI_EXTERNAL_MODEL_ENABLED: bool = False
    # Empty installations must stay empty until data is deliberately added.
    AUTO_SEED_CATALOG: bool = False

    # Presidio PII screening (blueprint §0.4 / §6.2)
    AI_PRESIDIO_ENABLED: bool = False
    # spaCy model for NER-based detection. Optional: if missing, screening falls
    # back to pattern-only Presidio (blueprint §0.2 "Graceful fallback").
    AI_SPACY_MODEL: str = "en_core_web_sm"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def dev_auth_allowed(self) -> bool:
        return self.DEV_AUTH_ENABLED and self.APP_ENV in ("development", "test")

    @field_validator("DATABASE_URL", "MIGRATION_DATABASE_URL")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value

    @model_validator(mode="after")
    def validate_security_settings(self):
        if self.APP_ENV not in ("development", "test"):
            if self.DEV_AUTH_ENABLED:
                raise ValueError("Development authentication must be disabled outside development/test")
            if self.AUTH_PROVIDER != "supabase" or not self.AUTH_PUBLIC_KEY:
                raise ValueError("Configure Supabase authentication before deployment")
            if not self.AUTH_ISSUER_URL.startswith("https://"):
                raise ValueError("AUTH_ISSUER_URL must use HTTPS outside development/test")
            if not self.FRONTEND_URL.startswith("https://"):
                raise ValueError("FRONTEND_URL must use HTTPS outside development/test")
            if "*" in self.cors_origins_list:
                raise ValueError("Credentialed CORS requires explicit origins")
        return self

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
