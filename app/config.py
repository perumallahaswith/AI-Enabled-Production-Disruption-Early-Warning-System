"""Application Configuration Module.

Loads and validates all environment variables and configuration settings for
the AI-Enabled Production Disruption Early Warning System.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Metadata
    APP_NAME: str = "AI-Enabled Production Disruption Early Warning System"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key-production-disruption-auth"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Fab Facility Metadata
    FAB_NAME: str = "AI-Enabled Product Disruption Early Warning System"
    FAB_LOCATION: str = "Production Unit 04 - Cleanroom Bay B"
    DEFAULT_CURRENCY: str = "USD"
    COST_PER_WAFER: float = 1450.00
    COST_PER_LOT: float = 36250.00
    DOWNTIME_COST_PER_HOUR: float = 25000.00

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./semiconductor_fab.db"

    # Early Warning Engine Thresholds (0 - 100 scale)
    THRESHOLD_NORMAL: float = 20.0
    THRESHOLD_LOW: float = 40.0
    THRESHOLD_MEDIUM: float = 60.0
    THRESHOLD_HIGH: float = 80.0
    THRESHOLD_CRITICAL: float = 100.0

    # Risk Prioritization Weights (Sum = 1.0)
    WEIGHT_PREDICTION_RISK: float = 0.35
    WEIGHT_ANOMALY_SEVERITY: float = 0.25
    WEIGHT_BUSINESS_IMPACT: float = 0.20
    WEIGHT_TREND_ESCALATION: float = 0.10
    WEIGHT_PRODUCTION_CRITICALITY: float = 0.10

    # Email & Notification Settings
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "alerts-noreply@plant-warning.local"
    EMAIL_ALERT_RECIPIENTS: str = "supervisor@plant.local,maintenance@plant.local,plant-manager@plant.local"
    ALERT_COOLDOWN_MINUTES: int = 15

    # Optional LLM Integration
    LLM_ENABLED: bool = False
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_PROVIDER: str = "openai"

    # Server Host & Ports
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    DASHBOARD_PORT: int = 8501
    BACKEND_API_URL: str = "http://127.0.0.1:8000"

    # Directories
    DATA_RAW_DIR: str = "data/raw"
    DATA_PROCESSED_DIR: str = "data/processed"
    DATA_SYNTHETIC_DIR: str = "data/synthetic"
    MODELS_DIR: str = "models/trained"

    @property
    def alert_recipients_list(self) -> List[str]:
        """Return recipients as a parsed list."""
        if not self.EMAIL_ALERT_RECIPIENTS:
            return []
        return [r.strip() for r in self.EMAIL_ALERT_RECIPIENTS.split(",") if r.strip()]

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            return "sqlite:///./semiconductor_fab.db"
        return v


@lru_cache()
def get_settings() -> Settings:
    """Cached accessor for application settings."""
    return Settings()


# Export singleton instance
settings = get_settings()
