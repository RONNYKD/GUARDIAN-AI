"""
Pipeline Configuration Module

Centralizes all configuration settings for the GuardianAI processing pipeline.
Includes Gemini model settings, thresholds, retry logic, and environment-specific configs.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class GeminiConfig:
    """Configuration for Gemini AI model."""
    
    # API Configuration
    api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    model_name: str = "gemini-2.0-flash"
    api_url: str = field(init=False)
    
    # Model Parameters
    temperature: float = 0.3  # Lower = more deterministic (0.0-1.0)
    top_p: float = 0.95  # Nucleus sampling threshold
    top_k: int = 40  # Top-k sampling parameter
    max_output_tokens: int = 2048  # Maximum response length
    
    # Safety Settings
    block_none: bool = False  # If True, disables safety filters
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay_seconds: int = 2
    timeout_seconds: int = 30
    
    def __post_init__(self):
        """Set computed fields after initialization."""
        self.api_url = f"https://generativelanguage.googleapis.com/v1/models/{self.model_name}:generateContent"
        
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable must be set or api_key provided"
            )


@dataclass
class VertexAIConfig:
    """Configuration for Vertex AI (alternative to AI Studio)."""
    
    project_id: str = field(default_factory=lambda: os.getenv("GCP_PROJECT_ID", ""))
    location: str = "us-central1"
    model_name: str = "gemini-1.5-flash"
    
    # Model Parameters (same as Gemini)
    temperature: float = 0.3
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 2048
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay_seconds: int = 2
    timeout_seconds: int = 30
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.project_id:
            raise ValueError(
                "GCP_PROJECT_ID environment variable must be set or project_id provided"
            )


@dataclass
class ThresholdConfig:
    """Detection thresholds for anomaly and threat detection."""
    
    # Cost Anomaly Thresholds
    cost_anomaly_threshold_usd: float = 400000.0  # Daily cost spike threshold
    cost_z_score_threshold: float = 3.0  # Standard deviations for anomaly
    
    # Latency Thresholds
    latency_spike_threshold_ms: int = 5000  # Maximum acceptable latency
    latency_p95_threshold_ms: int = 3000  # P95 latency threshold
    
    # Quality Thresholds
    quality_degradation_threshold: float = 0.7  # Minimum acceptable quality score
    coherence_min: float = 0.6
    relevance_min: float = 0.6
    completeness_min: float = 0.5
    
    # Error Rate Thresholds
    error_rate_threshold: float = 0.05  # 5% error rate triggers alert
    
    # Threat Detection Thresholds
    threat_confidence_threshold: float = 0.75  # Minimum confidence to flag threat
    toxicity_threshold: float = 0.7  # Perspective API toxicity threshold
    
    # Volume Thresholds
    request_spike_multiplier: float = 3.0  # 3x normal traffic = spike
    min_requests_for_analysis: int = 100  # Minimum data points for statistical analysis


@dataclass
class PubSubConfig:
    """Configuration for Google Cloud Pub/Sub."""
    
    project_id: str = field(default_factory=lambda: os.getenv("GCP_PROJECT_ID", ""))
    
    # Topic Names
    telemetry_topic: str = "guardianai-telemetry"
    incident_topic: str = "guardianai-incidents"
    alert_topic: str = "guardianai-alerts"
    
    # Subscription Names
    telemetry_subscription: str = "guardianai-telemetry-sub"
    
    # Processing Configuration
    max_messages: int = 100  # Max messages to pull at once
    ack_deadline_seconds: int = 60  # Time to process before re-delivery
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable must be set")


@dataclass
class FirestoreConfig:
    """Configuration for Google Cloud Firestore."""
    
    project_id: str = field(default_factory=lambda: os.getenv("GCP_PROJECT_ID", ""))
    database: str = field(default_factory=lambda: os.getenv("FIRESTORE_DATABASE", "guardianai"))
    
    # Collection Names
    telemetry_collection: str = "telemetry"
    incidents_collection: str = "incidents"
    users_collection: str = "users"
    config_collection: str = "config"
    metrics_collection: str = "metrics"
    
    # Query Limits
    default_query_limit: int = 100
    max_query_limit: int = 1000
    
    # Retention Settings
    telemetry_retention_days: int = 30  # Auto-delete old telemetry
    incident_retention_days: int = 90
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable must be set")


@dataclass
class DatadogConfig:
    """Configuration for Datadog integration."""
    
    api_key: str = field(default_factory=lambda: os.getenv("DD_API_KEY", ""))
    app_key: str = field(default_factory=lambda: os.getenv("DD_APP_KEY", ""))
    site: str = field(default_factory=lambda: os.getenv("DD_SITE", "datadoghq.com"))
    
    # Metric Prefixes
    metric_prefix: str = "guardianai"
    
    # Alert Settings
    enable_alerts: bool = True
    alert_priority: str = "normal"  # low, normal, high
    
    # Metric Submission
    batch_size: int = 100  # Metrics per batch
    flush_interval_seconds: int = 10
    
    def __post_init__(self):
        """Validate configuration."""
        # Only require keys if alerts are enabled and we're not in development
        env = os.getenv("ENVIRONMENT", "development")
        if self.enable_alerts and env == "production":
            if not self.api_key or not self.app_key:
                raise ValueError(
                    "DD_API_KEY and DD_APP_KEY environment variables must be set for Datadog alerts in production"
                )


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    
    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Cloud Logging
    enable_cloud_logging: bool = True
    project_id: str = field(default_factory=lambda: os.getenv("GCP_PROJECT_ID", ""))
    
    # Log Retention
    retention_days: int = 30


@dataclass
class PipelineConfig:
    """Main pipeline configuration combining all sub-configs."""
    
    # Environment
    environment: Environment = field(
        default_factory=lambda: Environment(os.getenv("ENVIRONMENT", "development"))
    )
    
    # Sub-configurations
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    vertex_ai: Optional[VertexAIConfig] = None  # Use Vertex AI instead of AI Studio
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    pubsub: PubSubConfig = field(default_factory=PubSubConfig)
    firestore: FirestoreConfig = field(default_factory=FirestoreConfig)
    datadog: DatadogConfig = field(default_factory=DatadogConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Processing Options
    enable_threat_detection: bool = True
    enable_anomaly_detection: bool = True
    enable_quality_analysis: bool = True
    enable_auto_remediation: bool = True
    
    # Parallelization
    max_concurrent_analyses: int = 10  # Max parallel Gemini requests
    worker_threads: int = 4
    
    # Batch Processing
    batch_size: int = 50
    batch_timeout_seconds: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment.value,
            "gemini": {
                "model_name": self.gemini.model_name,
                "temperature": self.gemini.temperature,
                "top_p": self.gemini.top_p,
                "top_k": self.gemini.top_k,
                "max_output_tokens": self.gemini.max_output_tokens,
            },
            "thresholds": {
                "cost_anomaly_threshold_usd": self.thresholds.cost_anomaly_threshold_usd,
                "quality_degradation_threshold": self.thresholds.quality_degradation_threshold,
                "latency_spike_threshold_ms": self.thresholds.latency_spike_threshold_ms,
                "error_rate_threshold": self.thresholds.error_rate_threshold,
                "threat_confidence_threshold": self.thresholds.threat_confidence_threshold,
            },
            "features": {
                "threat_detection": self.enable_threat_detection,
                "anomaly_detection": self.enable_anomaly_detection,
                "quality_analysis": self.enable_quality_analysis,
                "auto_remediation": self.enable_auto_remediation,
            },
            "processing": {
                "max_concurrent_analyses": self.max_concurrent_analyses,
                "worker_threads": self.worker_threads,
                "batch_size": self.batch_size,
            }
        }
    
    @classmethod
    def from_environment(cls) -> "PipelineConfig":
        """
        Create configuration from environment variables.
        
        Environment Variables:
            - ENVIRONMENT: development, staging, production
            - GOOGLE_API_KEY: Google AI Studio API key
            - GCP_PROJECT_ID: Google Cloud project ID
            - DD_API_KEY: Datadog API key
            - DD_APP_KEY: Datadog application key
            - DD_SITE: Datadog site (default: datadoghq.com)
            - LOG_LEVEL: Logging level (default: INFO)
        """
        return cls()
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Ensure at least one AI provider is configured
        if not self.gemini.api_key and not (self.vertex_ai and self.vertex_ai.project_id):
            raise ValueError(
                "Either GOOGLE_API_KEY (for AI Studio) or GCP_PROJECT_ID (for Vertex AI) must be set"
            )
        
        # Validate thresholds are positive
        if self.thresholds.cost_anomaly_threshold_usd <= 0:
            raise ValueError("cost_anomaly_threshold_usd must be positive")
        
        if self.thresholds.quality_degradation_threshold < 0 or self.thresholds.quality_degradation_threshold > 1:
            raise ValueError("quality_degradation_threshold must be between 0 and 1")
        
        # Validate processing limits
        if self.max_concurrent_analyses < 1:
            raise ValueError("max_concurrent_analyses must be at least 1")
        
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        
        return True


# Global configuration instance
_config: Optional[PipelineConfig] = None


def get_config() -> PipelineConfig:
    """
    Get global pipeline configuration.
    
    Lazily creates configuration from environment on first call.
    
    Returns:
        PipelineConfig instance
    """
    global _config
    if _config is None:
        _config = PipelineConfig.from_environment()
        _config.validate()
    return _config


def set_config(config: PipelineConfig) -> None:
    """
    Set global pipeline configuration.
    
    Args:
        config: PipelineConfig instance
    """
    global _config
    config.validate()
    _config = config


# Example usage
if __name__ == "__main__":
    import json
    
    print("GuardianAI Pipeline Configuration")
    print("=" * 60)
    
    # Load configuration from environment
    config = get_config()
    
    print(f"\nEnvironment: {config.environment.value}")
    print(f"Gemini Model: {config.gemini.model_name}")
    print(f"Temperature: {config.gemini.temperature}")
    print(f"Max Tokens: {config.gemini.max_output_tokens}")
    
    print("\nThresholds:")
    print(f"  Cost Anomaly: ${config.thresholds.cost_anomaly_threshold_usd:,.0f}")
    print(f"  Quality Min: {config.thresholds.quality_degradation_threshold}")
    print(f"  Latency Max: {config.thresholds.latency_spike_threshold_ms}ms")
    print(f"  Error Rate Max: {config.thresholds.error_rate_threshold * 100}%")
    
    print("\nFeatures:")
    print(f"  Threat Detection: {'✅' if config.enable_threat_detection else '❌'}")
    print(f"  Anomaly Detection: {'✅' if config.enable_anomaly_detection else '❌'}")
    print(f"  Quality Analysis: {'✅' if config.enable_quality_analysis else '❌'}")
    print(f"  Auto Remediation: {'✅' if config.enable_auto_remediation else '❌'}")
    
    print("\nProcessing:")
    print(f"  Max Concurrent: {config.max_concurrent_analyses}")
    print(f"  Worker Threads: {config.worker_threads}")
    print(f"  Batch Size: {config.batch_size}")
    
    print("\n" + "=" * 60)
    print("Configuration JSON:")
    print(json.dumps(config.to_dict(), indent=2))
    
    print("\n✅ Configuration loaded successfully!")
