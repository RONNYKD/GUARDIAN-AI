"""
GuardianAI Anomaly Detector

Detects anomalies in LLM usage patterns using statistical analysis.
Implements detection for cost spikes, latency anomalies, and usage patterns.
"""

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""
    COST_SPIKE = "cost_spike"
    LATENCY_SPIKE = "latency_spike"
    TOKEN_SPIKE = "token_spike"
    ERROR_RATE_SPIKE = "error_rate_spike"
    REQUEST_RATE_SPIKE = "request_rate_spike"
    QUALITY_DEGRADATION = "quality_degradation"


@dataclass
class Baseline:
    """Statistical baseline for anomaly detection."""
    metric_name: str
    mean: float
    std_dev: float
    min_value: float
    max_value: float
    sample_count: int
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "mean": self.mean,
            "std_dev": self.std_dev,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "sample_count": self.sample_count,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Baseline":
        """Create from dictionary."""
        return cls(
            metric_name=data["metric_name"],
            mean=data["mean"],
            std_dev=data["std_dev"],
            min_value=data["min_value"],
            max_value=data["max_value"],
            sample_count=data["sample_count"],
            last_updated=data.get("last_updated", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class DetectedAnomaly:
    """A detected anomaly with metadata."""
    anomaly_type: AnomalyType
    severity: str  # "low", "medium", "high", "critical"
    current_value: float
    expected_value: float
    deviation: float  # Standard deviations from mean
    description: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace_id: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity,
            "current_value": self.current_value,
            "expected_value": self.expected_value,
            "deviation": self.deviation,
            "description": self.description,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
        }


class AnomalyDetector:
    """
    Detects anomalies in LLM metrics using statistical analysis.
    
    Uses rolling baselines to detect:
    - Cost spikes (>400,000 tokens/hour threshold)
    - Latency spikes (P95 > 5000ms)
    - Error rate spikes (>5%)
    - Quality degradation (<0.7 score)
    
    Example:
        >>> detector = AnomalyDetector()
        >>> detector.add_sample("latency_ms", 150.0)
        >>> anomalies = detector.check_value("latency_ms", 5500.0)
    """
    
    # Detection thresholds from requirements
    THRESHOLDS = {
        "cost_anomaly_tokens_per_hour": 400000,
        "quality_degradation": 0.7,
        "latency_spike_p95_ms": 5000,
        "error_rate_percent": 5.0,
    }
    
    def __init__(
        self,
        window_size: int = 1000,
        z_score_threshold: float = 3.0,
        min_samples: int = 30,
    ) -> None:
        """
        Initialize anomaly detector.
        
        Args:
            window_size: Number of samples to maintain in rolling window
            z_score_threshold: Z-score threshold for anomaly detection
            min_samples: Minimum samples before detection is enabled
        """
        self.window_size = window_size
        self.z_score_threshold = z_score_threshold
        self.min_samples = min_samples
        
        self._windows: dict[str, deque] = {}
        self._baselines: dict[str, Baseline] = {}
    
    def add_sample(self, metric_name: str, value: float) -> None:
        """
        Add a sample to the rolling window.
        
        Args:
            metric_name: Name of the metric
            value: Sample value
        """
        if metric_name not in self._windows:
            self._windows[metric_name] = deque(maxlen=self.window_size)
        
        self._windows[metric_name].append(value)
        self._update_baseline(metric_name)
    
    def _update_baseline(self, metric_name: str) -> None:
        """Update baseline statistics for a metric."""
        window = self._windows.get(metric_name)
        if not window or len(window) < self.min_samples:
            return
        
        values = list(window)
        n = len(values)
        
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = math.sqrt(variance) if variance > 0 else 0.0
        
        self._baselines[metric_name] = Baseline(
            metric_name=metric_name,
            mean=mean,
            std_dev=std_dev,
            min_value=min(values),
            max_value=max(values),
            sample_count=n,
        )
    
    def get_baseline(self, metric_name: str) -> Optional[Baseline]:
        """Get current baseline for a metric."""
        return self._baselines.get(metric_name)
    
    def check_value(
        self,
        metric_name: str,
        value: float,
        trace_id: Optional[str] = None,
    ) -> list[DetectedAnomaly]:
        """
        Check if a value is anomalous.
        
        Args:
            metric_name: Name of the metric
            value: Current value to check
            trace_id: Trace ID for correlation
        
        Returns:
            List of detected anomalies (empty if normal)
        """
        anomalies = []
        
        baseline = self._baselines.get(metric_name)
        
        if baseline and baseline.std_dev > 0:
            # Z-score based detection
            z_score = abs(value - baseline.mean) / baseline.std_dev
            
            if z_score > self.z_score_threshold:
                severity = self._get_severity_from_z_score(z_score)
                anomaly_type = self._get_anomaly_type(metric_name)
                
                anomalies.append(DetectedAnomaly(
                    anomaly_type=anomaly_type,
                    severity=severity,
                    current_value=value,
                    expected_value=baseline.mean,
                    deviation=z_score,
                    description=f"{metric_name} is {z_score:.1f} standard deviations from mean",
                    trace_id=trace_id,
                ))
        
        # Check absolute thresholds
        threshold_anomalies = self._check_absolute_thresholds(
            metric_name, value, trace_id
        )
        anomalies.extend(threshold_anomalies)
        
        return anomalies
    
    def _get_severity_from_z_score(self, z_score: float) -> str:
        """Map z-score to severity level."""
        if z_score >= 5.0:
            return "critical"
        elif z_score >= 4.0:
            return "high"
        elif z_score >= 3.5:
            return "medium"
        else:
            return "low"
    
    def _get_anomaly_type(self, metric_name: str) -> AnomalyType:
        """Map metric name to anomaly type."""
        mapping = {
            "cost_usd": AnomalyType.COST_SPIKE,
            "latency_ms": AnomalyType.LATENCY_SPIKE,
            "input_tokens": AnomalyType.TOKEN_SPIKE,
            "output_tokens": AnomalyType.TOKEN_SPIKE,
            "total_tokens": AnomalyType.TOKEN_SPIKE,
            "error_rate": AnomalyType.ERROR_RATE_SPIKE,
            "request_rate": AnomalyType.REQUEST_RATE_SPIKE,
            "quality_score": AnomalyType.QUALITY_DEGRADATION,
        }
        return mapping.get(metric_name, AnomalyType.COST_SPIKE)
    
    def _check_absolute_thresholds(
        self,
        metric_name: str,
        value: float,
        trace_id: Optional[str],
    ) -> list[DetectedAnomaly]:
        """Check value against absolute thresholds."""
        anomalies = []
        
        # Latency threshold
        if metric_name == "latency_ms" and value > self.THRESHOLDS["latency_spike_p95_ms"]:
            anomalies.append(DetectedAnomaly(
                anomaly_type=AnomalyType.LATENCY_SPIKE,
                severity="high",
                current_value=value,
                expected_value=self.THRESHOLDS["latency_spike_p95_ms"],
                deviation=value / self.THRESHOLDS["latency_spike_p95_ms"],
                description=f"Latency {value:.0f}ms exceeds threshold {self.THRESHOLDS['latency_spike_p95_ms']}ms",
                trace_id=trace_id,
            ))
        
        # Quality threshold (low is bad)
        if metric_name == "quality_score" and value < self.THRESHOLDS["quality_degradation"]:
            anomalies.append(DetectedAnomaly(
                anomaly_type=AnomalyType.QUALITY_DEGRADATION,
                severity="high",
                current_value=value,
                expected_value=self.THRESHOLDS["quality_degradation"],
                deviation=self.THRESHOLDS["quality_degradation"] - value,
                description=f"Quality score {value:.2f} below threshold {self.THRESHOLDS['quality_degradation']}",
                trace_id=trace_id,
            ))
        
        # Error rate threshold
        if metric_name == "error_rate" and value > self.THRESHOLDS["error_rate_percent"]:
            anomalies.append(DetectedAnomaly(
                anomaly_type=AnomalyType.ERROR_RATE_SPIKE,
                severity="critical",
                current_value=value,
                expected_value=self.THRESHOLDS["error_rate_percent"],
                deviation=value / self.THRESHOLDS["error_rate_percent"],
                description=f"Error rate {value:.1f}% exceeds threshold {self.THRESHOLDS['error_rate_percent']}%",
                trace_id=trace_id,
            ))
        
        return anomalies
    
    def check_hourly_token_rate(
        self,
        tokens_per_hour: float,
        trace_id: Optional[str] = None,
    ) -> Optional[DetectedAnomaly]:
        """
        Check if hourly token rate exceeds threshold.
        
        Implements Requirement: cost_anomaly = 400,000 tokens/hour
        """
        threshold = self.THRESHOLDS["cost_anomaly_tokens_per_hour"]
        
        if tokens_per_hour > threshold:
            return DetectedAnomaly(
                anomaly_type=AnomalyType.TOKEN_SPIKE,
                severity="critical",
                current_value=tokens_per_hour,
                expected_value=threshold,
                deviation=tokens_per_hour / threshold,
                description=f"Token rate {tokens_per_hour:.0f}/hr exceeds threshold {threshold}/hr",
                trace_id=trace_id,
            )
        
        return None
    
    def get_all_baselines(self) -> dict[str, Baseline]:
        """Get all current baselines."""
        return dict(self._baselines)
    
    def set_baseline(self, baseline: Baseline) -> None:
        """Set a baseline directly (e.g., from storage)."""
        self._baselines[baseline.metric_name] = baseline
    
    def clear(self) -> None:
        """Clear all windows and baselines."""
        self._windows.clear()
        self._baselines.clear()


class RateTracker:
    """
    Tracks request rates over time windows.
    
    Used for detecting request rate anomalies.
    """
    
    def __init__(self, window_seconds: int = 3600) -> None:
        """
        Initialize rate tracker.
        
        Args:
            window_seconds: Time window for rate calculation (default 1 hour)
        """
        self.window_seconds = window_seconds
        self._timestamps: deque = deque()
        self._token_counts: deque = deque()
    
    def record_request(self, tokens: int = 0) -> None:
        """Record a request with optional token count."""
        now = datetime.now(timezone.utc)
        self._timestamps.append(now)
        self._token_counts.append(tokens)
        self._cleanup()
    
    def _cleanup(self) -> None:
        """Remove entries outside the window."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.window_seconds)
        
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
            self._token_counts.popleft()
    
    def get_request_rate(self) -> float:
        """Get requests per hour."""
        self._cleanup()
        count = len(self._timestamps)
        
        if count == 0:
            return 0.0
        
        return count * (3600 / self.window_seconds)
    
    def get_token_rate(self) -> float:
        """Get tokens per hour."""
        self._cleanup()
        total_tokens = sum(self._token_counts)
        
        if total_tokens == 0:
            return 0.0
        
        return total_tokens * (3600 / self.window_seconds)
