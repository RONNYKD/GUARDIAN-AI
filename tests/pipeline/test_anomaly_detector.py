"""
Property-based tests for GuardianAI Anomaly Detector.

Tests baseline learning and anomaly detection.
"""

import pytest
import math
from hypothesis import given, strategies as st, settings, assume

from pipeline.anomaly_detector import (
    AnomalyDetector,
    AnomalyType,
    Baseline,
    DetectedAnomaly,
    RateTracker,
)


# =============================================================================
# Property 11: Baseline learning from samples
# =============================================================================

@given(
    values=st.lists(
        st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=50,
        max_size=200,
    ),
)
@settings(max_examples=30)
def test_property_11_baseline_learning(values: list[float]):
    """
    Property 11: Baselines are learned from samples.
    
    Detector must maintain accurate statistics from samples.
    """
    detector = AnomalyDetector(min_samples=30)
    
    for value in values:
        detector.add_sample("test_metric", value)
    
    baseline = detector.get_baseline("test_metric")
    
    assert baseline is not None, "Baseline should be created"
    assert baseline.sample_count >= 30
    
    # Verify statistics are reasonable
    expected_mean = sum(values) / len(values)
    assert math.isclose(baseline.mean, expected_mean, rel_tol=0.1)
    
    assert baseline.min_value == min(values[-detector.window_size:])
    assert baseline.max_value == max(values[-detector.window_size:])


# =============================================================================
# Property 12: Anomaly detection sensitivity
# =============================================================================

@given(
    normal_value=st.floats(min_value=50.0, max_value=150.0, allow_nan=False),
    deviation_multiplier=st.floats(min_value=4.0, max_value=10.0, allow_nan=False),
)
@settings(max_examples=30)
def test_property_12_anomaly_detection(normal_value: float, deviation_multiplier: float):
    """
    Property 12: Values significantly outside baseline are detected as anomalies.
    """
    detector = AnomalyDetector(z_score_threshold=3.0, min_samples=30)
    
    # Build baseline with normal values (small variance)
    base_values = [normal_value + (i % 10 - 5) for i in range(50)]
    for value in base_values:
        detector.add_sample("test_metric", value)
    
    baseline = detector.get_baseline("test_metric")
    assert baseline is not None
    
    # Create anomalous value
    anomalous_value = normal_value + (baseline.std_dev * deviation_multiplier)
    
    anomalies = detector.check_value("test_metric", anomalous_value)
    
    # Should detect anomaly for high deviations
    if deviation_multiplier >= 4.0 and baseline.std_dev > 0:
        assert len(anomalies) > 0, f"Should detect {deviation_multiplier}x std deviation"


# =============================================================================
# Property: Normal values are not flagged
# =============================================================================

@given(
    values=st.lists(
        st.floats(min_value=90.0, max_value=110.0, allow_nan=False),
        min_size=50,
        max_size=100,
    ),
)
@settings(max_examples=30)
def test_normal_values_not_flagged(values: list[float]):
    """Values within normal range should not trigger anomalies."""
    detector = AnomalyDetector(min_samples=30)
    
    # Build baseline
    for value in values[:40]:
        detector.add_sample("test_metric", value)
    
    # Check remaining values (should be normal)
    for value in values[40:]:
        anomalies = detector.check_value("test_metric", value)
        # Z-score based anomalies should be rare for normal distribution
        z_score_anomalies = [a for a in anomalies if a.deviation > 3.0]
        assert len(z_score_anomalies) == 0


# =============================================================================
# Property: Absolute thresholds are enforced
# =============================================================================

@given(
    latency=st.floats(min_value=5001.0, max_value=100000.0, allow_nan=False),
)
@settings(max_examples=20)
def test_latency_threshold(latency: float):
    """Latency exceeding 5000ms must be flagged."""
    detector = AnomalyDetector()
    
    anomalies = detector.check_value("latency_ms", latency)
    
    latency_anomalies = [
        a for a in anomalies 
        if a.anomaly_type == AnomalyType.LATENCY_SPIKE
    ]
    assert len(latency_anomalies) > 0


@given(
    quality=st.floats(min_value=0.0, max_value=0.69, allow_nan=False),
)
@settings(max_examples=20)
def test_quality_threshold(quality: float):
    """Quality below 0.7 must be flagged."""
    detector = AnomalyDetector()
    
    anomalies = detector.check_value("quality_score", quality)
    
    quality_anomalies = [
        a for a in anomalies 
        if a.anomaly_type == AnomalyType.QUALITY_DEGRADATION
    ]
    assert len(quality_anomalies) > 0


@given(
    error_rate=st.floats(min_value=5.1, max_value=100.0, allow_nan=False),
)
@settings(max_examples=20)
def test_error_rate_threshold(error_rate: float):
    """Error rate exceeding 5% must be flagged."""
    detector = AnomalyDetector()
    
    anomalies = detector.check_value("error_rate", error_rate)
    
    error_anomalies = [
        a for a in anomalies 
        if a.anomaly_type == AnomalyType.ERROR_RATE_SPIKE
    ]
    assert len(error_anomalies) > 0


# =============================================================================
# Property: Token rate threshold
# =============================================================================

@given(
    tokens_per_hour=st.floats(min_value=400001.0, max_value=10000000.0, allow_nan=False),
)
@settings(max_examples=20)
def test_token_rate_threshold(tokens_per_hour: float):
    """Token rate exceeding 400,000/hr must be flagged."""
    detector = AnomalyDetector()
    
    anomaly = detector.check_hourly_token_rate(tokens_per_hour)
    
    assert anomaly is not None
    assert anomaly.anomaly_type == AnomalyType.TOKEN_SPIKE
    assert anomaly.severity == "critical"


def test_token_rate_below_threshold():
    """Token rate below threshold should not flag."""
    detector = AnomalyDetector()
    
    anomaly = detector.check_hourly_token_rate(300000)
    
    assert anomaly is None


# =============================================================================
# Property: Baseline serialization
# =============================================================================

@given(
    metric_name=st.text(min_size=1, max_size=32).filter(lambda x: x.strip()),
    mean=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False),
    std_dev=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False),
    min_value=st.floats(min_value=0.0, max_value=5000.0, allow_nan=False),
    max_value=st.floats(min_value=5000.0, max_value=10000.0, allow_nan=False),
    sample_count=st.integers(min_value=1, max_value=10000),
)
@settings(max_examples=30)
def test_baseline_serialization(
    metric_name: str,
    mean: float,
    std_dev: float,
    min_value: float,
    max_value: float,
    sample_count: int,
):
    """Baseline serializes and deserializes correctly."""
    baseline = Baseline(
        metric_name=metric_name,
        mean=mean,
        std_dev=std_dev,
        min_value=min_value,
        max_value=max_value,
        sample_count=sample_count,
    )
    
    data = baseline.to_dict()
    restored = Baseline.from_dict(data)
    
    assert restored.metric_name == metric_name
    assert restored.mean == mean
    assert restored.std_dev == std_dev
    assert restored.sample_count == sample_count


# =============================================================================
# Property: DetectedAnomaly structure
# =============================================================================

@given(
    anomaly_type=st.sampled_from(list(AnomalyType)),
    severity=st.sampled_from(["low", "medium", "high", "critical"]),
    current_value=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False),
    expected_value=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False),
    deviation=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
)
@settings(max_examples=30)
def test_detected_anomaly_structure(
    anomaly_type: AnomalyType,
    severity: str,
    current_value: float,
    expected_value: float,
    deviation: float,
):
    """DetectedAnomaly has correct structure."""
    anomaly = DetectedAnomaly(
        anomaly_type=anomaly_type,
        severity=severity,
        current_value=current_value,
        expected_value=expected_value,
        deviation=deviation,
        description="Test anomaly",
    )
    
    data = anomaly.to_dict()
    
    assert data["anomaly_type"] == anomaly_type.value
    assert data["severity"] == severity
    assert data["current_value"] == current_value
    assert data["expected_value"] == expected_value


# =============================================================================
# Property: Severity mapping from z-score
# =============================================================================

@given(
    z_score=st.floats(min_value=3.0, max_value=10.0, allow_nan=False),
)
@settings(max_examples=20)
def test_severity_from_z_score(z_score: float):
    """Severity increases with z-score."""
    detector = AnomalyDetector()
    
    severity = detector._get_severity_from_z_score(z_score)
    
    assert severity in ("low", "medium", "high", "critical")
    
    if z_score >= 5.0:
        assert severity == "critical"
    elif z_score >= 4.0:
        assert severity == "high"


# =============================================================================
# Property: Rate tracker accuracy
# =============================================================================

@given(
    request_count=st.integers(min_value=1, max_value=100),
    tokens_per_request=st.integers(min_value=100, max_value=10000),
)
@settings(max_examples=20)
def test_rate_tracker(request_count: int, tokens_per_request: int):
    """Rate tracker counts accurately."""
    tracker = RateTracker(window_seconds=3600)
    
    for _ in range(request_count):
        tracker.record_request(tokens_per_request)
    
    # Should have recorded all requests
    assert tracker.get_request_rate() >= request_count
    
    # Token rate should be proportional
    total_tokens = request_count * tokens_per_request
    assert tracker.get_token_rate() >= total_tokens


# =============================================================================
# Property: Clear resets state
# =============================================================================

@given(
    values=st.lists(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
        min_size=50,
        max_size=100,
    ),
)
@settings(max_examples=10)
def test_clear_resets_state(values: list[float]):
    """Clear removes all baselines and samples."""
    detector = AnomalyDetector(min_samples=30)
    
    for value in values:
        detector.add_sample("test_metric", value)
    
    assert detector.get_baseline("test_metric") is not None
    
    detector.clear()
    
    assert detector.get_baseline("test_metric") is None
    assert len(detector.get_all_baselines()) == 0
