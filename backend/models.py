"""
GuardianAI Data Models

Pydantic models for:
- Telemetry records
- Incidents
- Threats
- Configuration
- Health scoring

All models include validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class ThreatType(str, Enum):
    """Types of detected threats."""
    PROMPT_INJECTION = "prompt_injection"
    PII_LEAK = "pii_leak"
    TOXIC_CONTENT = "toxic_content"
    COST_ANOMALY = "cost_anomaly"
    JAILBREAK = "jailbreak"


class ThreatSeverity(str, Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident status values."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class RemediationActionType(str, Enum):
    """Types of remediation actions."""
    RATE_LIMIT = "rate_limit"
    CIRCUIT_BREAKER = "circuit_breaker"
    PII_REDACTION = "pii_redaction"
    PROMPT_SANITIZATION = "prompt_sanitization"


# ============================================
# Threat Models
# ============================================

class Threat(BaseModel):
    """
    Detected threat in an LLM interaction.
    
    Attributes:
        type: Type of threat detected
        severity: Severity level (low, medium, high, critical)
        confidence: Detection confidence (0.0-1.0)
        description: Human-readable description
        evidence: Evidence supporting detection
        remediation_action: Action taken (if any)
    """
    type: ThreatType
    severity: ThreatSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    description: Optional[str] = None
    evidence: Optional[str] = None
    remediation_action: Optional[str] = None

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return round(v, 4)


# ============================================
# Telemetry Models
# ============================================

class TelemetryRequest(BaseModel):
    """
    Request portion of telemetry.
    
    Captures: prompt text, model identifier, temperature parameter,
    max_tokens parameter, and request timestamp (Requirement 1.1)
    """
    prompt: str = Field(description="The prompt text sent to the LLM")
    model: str = Field(description="Model identifier (e.g., gemini-pro)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    timestamp: str = Field(description="ISO 8601 timestamp of request")
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class TelemetryResponse(BaseModel):
    """
    Response portion of telemetry.
    
    Captures: complete response text, input token count, output token count,
    total latency in milliseconds, and calculated cost (Requirement 1.2)
    """
    response_text: str = Field(description="Complete response from LLM")
    input_tokens: int = Field(ge=0, description="Number of input tokens")
    output_tokens: int = Field(ge=0, description="Number of output tokens")
    latency_ms: float = Field(ge=0, description="Total latency in milliseconds")
    cost_usd: float = Field(ge=0, description="Calculated cost in USD")
    finish_reason: Optional[str] = None


class TelemetryRecord(BaseModel):
    """
    Complete telemetry record for an LLM interaction.
    
    Combines request and response data with tracing and threat information.
    Implements Requirements 1.1-1.5.
    """
    # Tracing
    trace_id: str = Field(description="Unique trace identifier")
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    
    # Request (Requirement 1.1)
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timestamp: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Response (Requirement 1.2)
    response_text: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    
    # Status
    status: str = "success"  # success, error, timeout
    error_message: Optional[str] = None
    
    # Quality
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    coherence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    # Threats
    threat_detected: bool = False
    threats: list[Threat] = Field(default_factory=list)
    
    # Metadata
    environment: str = "development"
    service_name: Optional[str] = None
    tags: dict[str, str] = Field(default_factory=dict)
    
    @field_validator("quality_score", "coherence_score")
    @classmethod
    def validate_scores(cls, v: Optional[float]) -> Optional[float]:
        """Ensure scores are within valid range (Property 10)."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        return v


# ============================================
# Incident Models
# ============================================

class RemediationAction(BaseModel):
    """
    Record of a remediation action taken.
    """
    action_type: RemediationActionType
    target: str = Field(description="Target of action (user_id, endpoint, etc.)")
    parameters: dict[str, Any] = Field(default_factory=dict)
    executed_at: Optional[str] = None
    success: bool = True
    result: Optional[str] = None


class IncidentContext(BaseModel):
    """
    Context information gathered for an incident.
    
    Includes recent telemetry (limit 10 per Requirement 8.3),
    AI analysis, and recommended actions.
    """
    recent_telemetry: list[TelemetryRecord] = Field(
        default_factory=list,
        max_length=10,  # Requirement 8.3
        description="10 most recent telemetry records"
    )
    related_trace_ids: list[str] = Field(default_factory=list)
    affected_user_ids: list[str] = Field(default_factory=list)
    ai_analysis: Optional[str] = None
    recommended_actions: list[str] = Field(default_factory=list)


class Incident(BaseModel):
    """
    Incident record created from detection rules.
    
    Implements Requirements 8.1-8.5.
    """
    incident_id: str
    created_at: str
    updated_at: str
    triggered_at: str  # When Datadog rule triggered
    
    status: IncidentStatus
    severity: ThreatSeverity
    
    rule_name: str
    title: str
    description: Optional[str] = None
    
    # Context (Requirement 8.3, 8.4)
    context: Optional[IncidentContext] = None
    
    # Remediation
    remediation_actions: list[RemediationAction] = Field(default_factory=list)
    
    # Resolution
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    # Datadog integration
    datadog_alert_id: Optional[str] = None
    datadog_incident_id: Optional[str] = None
    datadog_incident_url: Optional[str] = None


# ============================================
# Health Score Models
# ============================================

class HealthScoreComponent(BaseModel):
    """Individual component contribution to health score."""
    name: str
    raw_value: float
    weight: float
    weighted_score: float


class HealthScore(BaseModel):
    """
    System health score calculation.
    
    Formula (Requirement 10.1):
    overall = (uptime * 0.4) + (quality * 0.3) + (security * 0.2) + (cost * 0.1)
    
    All scores normalized to 0-100 scale.
    """
    overall_score: float = Field(ge=0.0, le=100.0)
    
    # Component scores
    uptime: HealthScoreComponent
    quality: HealthScoreComponent
    security: HealthScoreComponent
    cost_efficiency: HealthScoreComponent
    
    # Metadata
    calculated_at: str
    period_hours: int = 24

    @classmethod
    def calculate(
        cls,
        uptime_pct: float,
        quality_score: float,
        threat_count: int,
        cost_efficiency_pct: float
    ) -> "HealthScore":
        """
        Calculate health score from component metrics.
        
        Property 33: Health Score Calculation Formula
        
        Args:
            uptime_pct: Uptime percentage (0-100)
            quality_score: Quality score (0.0-1.0)
            threat_count: Number of active threats
            cost_efficiency_pct: Cost efficiency percentage (0-100)
        
        Returns:
            HealthScore with all components
        """
        from datetime import timezone
        
        # Normalize inputs
        uptime_norm = min(100, max(0, uptime_pct))
        quality_norm = min(100, max(0, quality_score * 100))
        security_norm = max(0, 100 - (threat_count * 10))
        cost_norm = min(100, max(0, cost_efficiency_pct))
        
        # Calculate weighted scores
        uptime_weighted = uptime_norm * 0.4
        quality_weighted = quality_norm * 0.3
        security_weighted = security_norm * 0.2
        cost_weighted = cost_norm * 0.1
        
        overall = uptime_weighted + quality_weighted + security_weighted + cost_weighted
        
        return cls(
            overall_score=round(overall, 1),
            uptime=HealthScoreComponent(
                name="uptime",
                raw_value=uptime_norm,
                weight=0.4,
                weighted_score=round(uptime_weighted, 2)
            ),
            quality=HealthScoreComponent(
                name="quality",
                raw_value=quality_norm,
                weight=0.3,
                weighted_score=round(quality_weighted, 2)
            ),
            security=HealthScoreComponent(
                name="security",
                raw_value=security_norm,
                weight=0.2,
                weighted_score=round(security_weighted, 2)
            ),
            cost_efficiency=HealthScoreComponent(
                name="cost_efficiency",
                raw_value=cost_norm,
                weight=0.1,
                weighted_score=round(cost_weighted, 2)
            ),
            calculated_at=datetime.now(timezone.utc).isoformat(),
            period_hours=24
        )


# ============================================
# Configuration Models
# ============================================

class DetectionThresholds(BaseModel):
    """
    Detection rule thresholds.
    
    Implements Requirement 7 detection rules.
    """
    cost_anomaly_tokens_per_hour: int = Field(
        default=400000,
        description="Token threshold for cost anomaly (Req 7.1)"
    )
    quality_degradation_score: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Quality score threshold (Req 7.3)"
    )
    latency_spike_p95_ms: int = Field(
        default=5000,
        description="P95 latency threshold in ms (Req 7.4)"
    )
    error_rate_percentage: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="Error rate threshold (Req 7.5)"
    )


class SystemConfig(BaseModel):
    """
    System configuration.
    """
    detection_thresholds: DetectionThresholds = Field(
        default_factory=DetectionThresholds
    )
    
    # Notification settings
    slack_webhook_url: Optional[str] = None
    slack_escalation_channel: Optional[str] = None
    email_recipients: list[str] = Field(default_factory=list)
    
    # Rate limiting defaults
    default_rate_limit: int = 100
    rate_limit_window_seconds: int = 60
    
    # Budget settings
    daily_budget_usd: float = 100.0
    monthly_budget_usd: float = 3000.0
    budget_alert_threshold_pct: float = 80.0


# ============================================
# Metrics Models
# ============================================

class LatencyPercentiles(BaseModel):
    """Latency percentile metrics."""
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float


class TokenUsageMetrics(BaseModel):
    """Token usage metrics."""
    total_tokens: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    requests_count: int
    period_hours: int


class MetricsSummary(BaseModel):
    """Summary metrics for dashboard."""
    total_requests_24h: int
    avg_latency_ms: float
    cost_today_usd: float
    active_threats: int
    health_score: float
    uptime_percentage: float
    quality_score: float
    error_rate: float
