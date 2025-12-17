"""
GuardianAI Backend Tests - Data Models

Property-based tests using Hypothesis for model validation.
"""

import pytest
from hypothesis import given, strategies as st, assume
from pydantic import ValidationError

import sys
sys.path.insert(0, str(__file__).replace("\\tests\\backend\\test_models.py", ""))

from backend.models import (
    Threat,
    ThreatType,
    ThreatSeverity,
    TelemetryRecord,
    HealthScore,
    HealthScoreComponent,
)


class TestThreatModel:
    """Tests for Threat model validation."""
    
    def test_threat_creation(self):
        """Test basic threat creation."""
        threat = Threat(
            type=ThreatType.PROMPT_INJECTION,
            severity=ThreatSeverity.CRITICAL,
            confidence=0.95
        )
        assert threat.type == ThreatType.PROMPT_INJECTION
        assert threat.severity == ThreatSeverity.CRITICAL
        assert threat.confidence == 0.95
    
    def test_threat_confidence_bounds(self):
        """Test confidence validation."""
        with pytest.raises(ValidationError):
            Threat(
                type=ThreatType.PII_LEAK,
                severity=ThreatSeverity.HIGH,
                confidence=1.5  # Invalid: > 1.0
            )
        
        with pytest.raises(ValidationError):
            Threat(
                type=ThreatType.PII_LEAK,
                severity=ThreatSeverity.HIGH,
                confidence=-0.1  # Invalid: < 0.0
            )


class TestTelemetryRecord:
    """Tests for TelemetryRecord model."""
    
    def test_telemetry_creation(self):
        """Test basic telemetry record creation."""
        record = TelemetryRecord(
            trace_id="trace_abc123",
            prompt="Hello, world!",
            model="gemini-pro",
            temperature=0.7,
            timestamp="2024-01-01T00:00:00Z",
            input_tokens=10,
            output_tokens=20,
            latency_ms=150.0,
            cost_usd=0.0125
        )
        assert record.trace_id == "trace_abc123"
        assert record.model == "gemini-pro"
    
    # Feature: guardianai, Property 10: Valid Quality Score Range
    @given(score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    def test_quality_score_valid_range_property(self, score: float):
        """
        Property 10: Valid Quality Score Range
        
        For any response analyzed for quality, the generated coherence score
        should be a number between 0.0 and 1.0 inclusive.
        
        Validates: Requirements 3.1
        """
        record = TelemetryRecord(
            trace_id="trace_test",
            prompt="test prompt",
            model="gemini-pro",
            timestamp="2024-01-01T00:00:00Z",
            quality_score=score,
            coherence_score=score
        )
        
        # Assert property holds
        assert 0.0 <= record.quality_score <= 1.0
        assert 0.0 <= record.coherence_score <= 1.0
    
    @given(score=st.floats(min_value=1.01, max_value=100.0, allow_nan=False))
    def test_quality_score_rejects_invalid_high(self, score: float):
        """Test that quality scores > 1.0 are rejected."""
        with pytest.raises(ValidationError):
            TelemetryRecord(
                trace_id="trace_test",
                prompt="test prompt",
                model="gemini-pro",
                timestamp="2024-01-01T00:00:00Z",
                quality_score=score
            )
    
    @given(score=st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False))
    def test_quality_score_rejects_invalid_low(self, score: float):
        """Test that quality scores < 0.0 are rejected."""
        assume(score < 0)
        with pytest.raises(ValidationError):
            TelemetryRecord(
                trace_id="trace_test",
                prompt="test prompt",
                model="gemini-pro",
                timestamp="2024-01-01T00:00:00Z",
                quality_score=score
            )


class TestHealthScore:
    """Tests for HealthScore model and calculation."""
    
    def test_health_score_calculation_basic(self):
        """Test basic health score calculation."""
        health = HealthScore.calculate(
            uptime_pct=100.0,
            quality_score=1.0,
            threat_count=0,
            cost_efficiency_pct=100.0
        )
        
        # Perfect scores should give 100
        assert health.overall_score == 100.0
    
    def test_health_score_weights(self):
        """Test that weights sum to 1.0."""
        health = HealthScore.calculate(
            uptime_pct=100.0,
            quality_score=1.0,
            threat_count=0,
            cost_efficiency_pct=100.0
        )
        
        total_weight = (
            health.uptime.weight +
            health.quality.weight +
            health.security.weight +
            health.cost_efficiency.weight
        )
        assert total_weight == 1.0
    
    # Feature: guardianai, Property 33: Health Score Calculation Formula
    @given(
        uptime=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
        quality=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        threats=st.integers(min_value=0, max_value=20),
        cost_eff=st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
    )
    def test_health_score_calculation_formula_property(
        self,
        uptime: float,
        quality: float,
        threats: int,
        cost_eff: float
    ):
        """
        Property 33: Health Score Calculation Formula
        
        The Backend API SHALL compute weighted average of:
        - uptime (40%)
        - quality score (30%)
        - threat count inverse (20%)
        - cost efficiency (10%)
        normalized to 0-100 scale.
        
        Validates: Requirements 10.1
        """
        health = HealthScore.calculate(
            uptime_pct=uptime,
            quality_score=quality,
            threat_count=threats,
            cost_efficiency_pct=cost_eff
        )
        
        # Manually calculate expected score
        uptime_norm = min(100, max(0, uptime))
        quality_norm = min(100, max(0, quality * 100))
        security_norm = max(0, 100 - (threats * 10))
        cost_norm = min(100, max(0, cost_eff))
        
        expected = (
            uptime_norm * 0.4 +
            quality_norm * 0.3 +
            security_norm * 0.2 +
            cost_norm * 0.1
        )
        
        # Assert property holds: calculated score matches formula
        assert abs(health.overall_score - round(expected, 1)) < 0.1
        
        # Assert score is in valid range
        assert 0.0 <= health.overall_score <= 100.0
    
    @given(
        uptime=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
        quality=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        cost_eff=st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
    )
    def test_health_score_range_property(
        self,
        uptime: float,
        quality: float,
        cost_eff: float
    ):
        """
        For any valid inputs, health score should be in range 0-100.
        """
        health = HealthScore.calculate(
            uptime_pct=uptime,
            quality_score=quality,
            threat_count=0,
            cost_efficiency_pct=cost_eff
        )
        
        assert 0.0 <= health.overall_score <= 100.0
    
    def test_health_score_threat_impact(self):
        """Test that threats reduce security score."""
        health_no_threats = HealthScore.calculate(
            uptime_pct=100.0,
            quality_score=1.0,
            threat_count=0,
            cost_efficiency_pct=100.0
        )
        
        health_with_threats = HealthScore.calculate(
            uptime_pct=100.0,
            quality_score=1.0,
            threat_count=5,
            cost_efficiency_pct=100.0
        )
        
        # More threats = lower score
        assert health_with_threats.overall_score < health_no_threats.overall_score
        assert health_with_threats.security.weighted_score < health_no_threats.security.weighted_score


class TestThreatSeverityAssignment:
    """Tests for threat severity assignment."""
    
    def test_severity_enum_values(self):
        """Test severity enum has correct values."""
        assert ThreatSeverity.LOW.value == "low"
        assert ThreatSeverity.MEDIUM.value == "medium"
        assert ThreatSeverity.HIGH.value == "high"
        assert ThreatSeverity.CRITICAL.value == "critical"
    
    def test_severity_ordering(self):
        """Test severity can be compared by index."""
        severities = list(ThreatSeverity)
        assert severities.index(ThreatSeverity.LOW) < severities.index(ThreatSeverity.CRITICAL)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
