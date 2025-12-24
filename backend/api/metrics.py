"""
GuardianAI Metrics API

Provides endpoints for:
- System metrics summaries
- Performance metrics (latency, throughput)
- Cost metrics and token usage
- Quality scores
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from config import get_settings, Settings

router = APIRouter()


class MetricsSummary(BaseModel):
    """Summary metrics for dashboard."""
    total_requests_24h: int = Field(description="Total requests in last 24 hours")
    avg_latency_ms: float = Field(description="Average latency in milliseconds")
    cost_today_usd: float = Field(description="Cost today in USD")
    active_threats: int = Field(description="Currently active threat count")
    health_score: float = Field(description="Overall health score 0-100")
    uptime_percentage: float = Field(description="Uptime percentage")
    quality_score: float = Field(description="Average quality score")
    error_rate: float = Field(description="Error rate percentage")


class LatencyMetrics(BaseModel):
    """Latency percentile metrics."""
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float


class TokenUsage(BaseModel):
    """Token usage metrics."""
    total_tokens: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    requests_count: int


class TimeSeriesPoint(BaseModel):
    """Single point in a time series."""
    timestamp: str
    value: float


class HealthScoreComponents(BaseModel):
    """Health score breakdown by component."""
    uptime_score: float = Field(description="Uptime contribution (40%)")
    quality_score: float = Field(description="Quality contribution (30%)")
    security_score: float = Field(description="Security contribution (20%)")
    cost_efficiency_score: float = Field(description="Cost efficiency contribution (10%)")
    overall_score: float = Field(description="Weighted overall score 0-100")


def calculate_health_score(
    uptime: float,
    quality: float,
    threat_count: int,
    cost_efficiency: float
) -> HealthScoreComponents:
    """
    Calculate health score using weighted average formula.
    
    Formula:
    overall = (uptime * 0.4) + (quality * 0.3) + (security * 0.2) + (cost * 0.1)
    
    Args:
        uptime: Uptime percentage (0-100)
        quality: Quality score (0-1, normalized to 0-100)
        threat_count: Number of active threats (inverted to score)
        cost_efficiency: Cost efficiency percentage (0-100)
    
    Returns:
        HealthScoreComponents with breakdown and overall score
    """
    # Normalize inputs
    uptime_normalized = min(100, max(0, uptime))
    quality_normalized = min(100, max(0, quality * 100))
    
    # Security score: 100 if no threats, decreases with more threats
    security_normalized = max(0, 100 - (threat_count * 10))
    
    cost_normalized = min(100, max(0, cost_efficiency))
    
    # Calculate weighted average
    overall = (
        (uptime_normalized * 0.4) +
        (quality_normalized * 0.3) +
        (security_normalized * 0.2) +
        (cost_normalized * 0.1)
    )
    
    return HealthScoreComponents(
        uptime_score=uptime_normalized * 0.4,
        quality_score=quality_normalized * 0.3,
        security_score=security_normalized * 0.2,
        cost_efficiency_score=cost_normalized * 0.1,
        overall_score=round(overall, 1)
    )


@router.get("/metrics/summary", response_model=MetricsSummary)
async def get_metrics_summary(
    settings: Settings = Depends(get_settings)
) -> MetricsSummary:
    """
    Get summary metrics for the dashboard overview.
    
    Returns aggregated metrics for the last 24 hours including
    request count, latency, cost, threats, and health score.
    """
    # TODO: Replace with actual Firestore queries
    # For now, return placeholder data
    
    # Calculate health score
    health = calculate_health_score(
        uptime=99.5,
        quality=0.85,
        threat_count=2,
        cost_efficiency=90
    )
    
    return MetricsSummary(
        total_requests_24h=15420,
        avg_latency_ms=245.5,
        cost_today_usd=42.75,
        active_threats=2,
        health_score=health.overall_score,
        uptime_percentage=99.5,
        quality_score=0.85,
        error_rate=0.3
    )


@router.get("/metrics/health-score", response_model=HealthScoreComponents)
async def get_health_score(
    settings: Settings = Depends(get_settings)
) -> HealthScoreComponents:
    """
    Get detailed health score breakdown.
    
    Returns health score components showing contribution
    from uptime, quality, security, and cost efficiency.
    """
    # TODO: Fetch actual metrics from Firestore/Datadog
    return calculate_health_score(
        uptime=99.5,
        quality=0.85,
        threat_count=2,
        cost_efficiency=90
    )


@router.get("/metrics/latency", response_model=LatencyMetrics)
async def get_latency_metrics(
    time_range_hours: int = Query(default=24, ge=1, le=168),
    model: Optional[str] = Query(default=None)
) -> LatencyMetrics:
    """
    Get latency metrics for the specified time range.
    
    Args:
        time_range_hours: Number of hours to look back (1-168)
        model: Optional model filter
    
    Returns:
        LatencyMetrics with percentiles
    """
    # TODO: Fetch from Firestore and calculate percentiles
    return LatencyMetrics(
        p50_ms=180.0,
        p95_ms=450.0,
        p99_ms=850.0,
        avg_ms=245.5,
        min_ms=45.0,
        max_ms=2500.0
    )


@router.get("/metrics/tokens", response_model=TokenUsage)
async def get_token_usage(
    time_range_hours: int = Query(default=24, ge=1, le=720),
    model: Optional[str] = Query(default=None)
) -> TokenUsage:
    """
    Get token usage metrics for the specified time range.
    
    Args:
        time_range_hours: Number of hours to look back
        model: Optional model filter
    
    Returns:
        TokenUsage with counts and cost
    """
    settings = get_settings()
    
    # TODO: Fetch from Firestore
    input_tokens = 125000
    output_tokens = 85000
    
    cost = (
        input_tokens * settings.gemini_input_price_per_token +
        output_tokens * settings.gemini_output_price_per_token
    )
    
    return TokenUsage(
        total_tokens=input_tokens + output_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=round(cost, 2),
        requests_count=1542
    )


@router.get("/metrics/timeseries/requests")
async def get_requests_timeseries(
    time_range_hours: int = Query(default=168, ge=1, le=720),
    interval: str = Query(default="1h", pattern="^(1h|6h|1d)$")
) -> list[TimeSeriesPoint]:
    """
    Get request count time series for charting.
    
    Args:
        time_range_hours: Number of hours to look back
        interval: Aggregation interval (1h, 6h, 1d)
    
    Returns:
        List of time series points
    """
    # TODO: Fetch from Firestore and aggregate
    # Return placeholder data
    import random
    
    points = []
    now = datetime.now(timezone.utc)
    
    if interval == "1h":
        intervals = min(time_range_hours, 168)
        delta = timedelta(hours=1)
    elif interval == "6h":
        intervals = time_range_hours // 6
        delta = timedelta(hours=6)
    else:
        intervals = time_range_hours // 24
        delta = timedelta(days=1)
    
    for i in range(intervals):
        timestamp = now - (delta * (intervals - i - 1))
        points.append(TimeSeriesPoint(
            timestamp=timestamp.isoformat(),
            value=random.randint(500, 1500)
        ))
    
    return points


@router.get("/metrics/timeseries/cost")
async def get_cost_timeseries(
    time_range_days: int = Query(default=30, ge=1, le=90)
) -> list[TimeSeriesPoint]:
    """
    Get daily cost time series for charting.
    
    Args:
        time_range_days: Number of days to look back
    
    Returns:
        List of daily cost points
    """
    # TODO: Fetch from Firestore
    import random
    
    points = []
    now = datetime.now(timezone.utc)
    
    for i in range(time_range_days):
        timestamp = now - timedelta(days=time_range_days - i - 1)
        points.append(TimeSeriesPoint(
            timestamp=timestamp.date().isoformat(),
            value=round(random.uniform(30, 60), 2)
        ))
    
    return points
