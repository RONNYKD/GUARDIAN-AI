"""
GuardianAI Backend Configuration

Loads configuration from environment variables for:
- Google Cloud Platform (GCP) services
- Datadog observability platform
- Application settings

Environment variables should be set in .env file or system environment.
"""

import os
import json
from pathlib import Path
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # GCP Configuration
    gcp_project_id: str = Field(
        default="",
        alias="GCP_PROJECT_ID",
        description="Google Cloud Platform project ID"
    )
    google_application_credentials: Optional[str] = Field(
        default=None,
        alias="GOOGLE_APPLICATION_CREDENTIALS",
        description="Path to GCP service account key JSON file"
    )
    google_application_credentials_json: Optional[str] = Field(
        default=None,
        alias="GOOGLE_APPLICATION_CREDENTIALS_JSON",
        description="GCP service account key JSON content (for cloud deployment)"
    )

    # Datadog Configuration
    dd_api_key: str = Field(
        default="",
        alias="DD_API_KEY",
        description="Datadog API key for metrics and logs"
    )
    dd_app_key: str = Field(
        default="",
        alias="DD_APP_KEY",
        description="Datadog application key for API access"
    )
    dd_site: str = Field(
        default="datadoghq.com",
        alias="DD_SITE",
        description="Datadog site (e.g., datadoghq.com, datadoghq.eu)"
    )
    dd_service_name: str = Field(
        default="guardianai-backend",
        alias="DD_SERVICE",
        description="Service name for Datadog APM"
    )
    dd_env: str = Field(
        default="development",
        alias="DD_ENV",
        description="Environment tag for Datadog"
    )

    # Pipeline Configuration
    pipeline_url: str = Field(
        default="",
        alias="PIPELINE_URL",
        description="URL of the Processing Pipeline Cloud Function"
    )

    # Application Configuration
    app_name: str = "GuardianAI"
    app_version: str = "0.1.0"
    debug: bool = Field(
        default=False,
        alias="DEBUG",
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        alias="API_HOST"
    )
    api_port: int = Field(
        default=8000,
        alias="API_PORT"
    )

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS"
    )

    # Firestore Collections
    telemetry_collection: str = "telemetry"
    incidents_collection: str = "incidents"
    config_collection: str = "config"
    users_collection: str = "users"
    attacks_collection: str = "attacks"
    rate_limits_collection: str = "rate_limits"

    # Detection Thresholds
    cost_anomaly_tokens_per_hour: int = 400000
    quality_degradation_score: float = 0.7
    latency_spike_p95_ms: int = 5000
    error_rate_percentage: float = 5.0
    high_rate_requests_per_minute: int = 100

    # Pricing (Gemini Pro)
    gemini_input_price_per_token: float = 0.00025
    gemini_output_price_per_token: float = 0.0005

    # JWT Configuration
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Notification Configuration
    slack_webhook_url: Optional[str] = Field(
        default=None,
        alias="SLACK_WEBHOOK_URL"
    )
    slack_escalation_channel: Optional[str] = Field(
        default=None,
        alias="SLACK_ESCALATION_CHANNEL"
    )

    model_config = {
        "env_file": str(Path(__file__).parent / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: Application configuration object

    Example:
        >>> settings = get_settings()
        >>> print(settings.gcp_project_id)
    """
    return Settings()


def get_gcp_credentials():
    """
    Get GCP credentials from either file path or JSON string.
    
    Returns:
        google.oauth2.service_account.Credentials or None
    """
    from google.oauth2 import service_account
    
    settings = get_settings()
    
    # Try to load from JSON string first (for cloud deployment like Render)
    if settings.google_application_credentials_json:
        try:
            credentials_dict = json.loads(settings.google_application_credentials_json)
            return service_account.Credentials.from_service_account_info(credentials_dict)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading credentials from JSON: {e}")
    
    # Fall back to file path (for local development)
    if settings.google_application_credentials and os.path.exists(settings.google_application_credentials):
        return service_account.Credentials.from_service_account_file(
            settings.google_application_credentials
        )
    
    # Use default credentials as last resort
    return None


# Convenience accessors for common settings
settings = get_settings()

# GCP Configuration
GCP_PROJECT_ID = settings.gcp_project_id
GOOGLE_APPLICATION_CREDENTIALS = settings.google_application_credentials

# Datadog Configuration
DD_API_KEY = settings.dd_api_key
DD_APP_KEY = settings.dd_app_key
DD_SITE = settings.dd_site

# Pricing Constants
GEMINI_PRO_PRICING = {
    "input": settings.gemini_input_price_per_token,
    "output": settings.gemini_output_price_per_token,
}

# Detection Thresholds
THRESHOLDS = {
    "cost_anomaly_tokens_per_hour": settings.cost_anomaly_tokens_per_hour,
    "quality_degradation_score": settings.quality_degradation_score,
    "latency_spike_p95_ms": settings.latency_spike_p95_ms,
    "error_rate_percentage": settings.error_rate_percentage,
}
