"""
Property-based tests for GuardianAI Alert Manager.

Tests alert creation and routing.
"""

import pytest
from hypothesis import given, strategies as st, settings

from pipeline.alert_manager import (
    AlertManager,
    Alert,
    AlertPriority,
    AlertStatus,
)


# =============================================================================
# Property 15: Alert priority mapping
# =============================================================================

SEVERITY_PRIORITY_MAP = [
    ("critical", AlertPriority.P1),
    ("high", AlertPriority.P2),
    ("medium", AlertPriority.P3),
    ("low", AlertPriority.P4),
]


@pytest.mark.parametrize("severity,expected_priority", SEVERITY_PRIORITY_MAP)
def test_property_15_severity_to_priority(severity: str, expected_priority: AlertPriority):
    """
    Property 15: Severity correctly maps to alert priority.
    """
    manager = AlertManager()
    
    alert = manager.create_threat_alert(
        threat_type="prompt_injection",
        severity=severity,
        description="Test threat",
        evidence="Test evidence",
    )
    
    assert alert.priority == expected_priority


# =============================================================================
# Property: Alert IDs are unique
# =============================================================================

@given(
    num_alerts=st.integers(min_value=5, max_value=50),
)
@settings(max_examples=20)
def test_unique_alert_ids(num_alerts: int):
    """All generated alert IDs must be unique."""
    manager = AlertManager()
    
    alert_ids = set()
    
    for i in range(num_alerts):
        alert = manager.create_threat_alert(
            threat_type="test",
            severity="medium",
            description=f"Test {i}",
            evidence="Evidence",
        )
        assert alert.alert_id not in alert_ids
        alert_ids.add(alert.alert_id)
    
    assert len(alert_ids) == num_alerts


# =============================================================================
# Property: Alert structure is complete
# =============================================================================

@given(
    threat_type=st.text(min_size=1, max_size=32).filter(lambda x: x.strip()),
    severity=st.sampled_from(["critical", "high", "medium", "low"]),
    description=st.text(min_size=1, max_size=200),
    evidence=st.text(min_size=1, max_size=100),
    trace_id=st.one_of(st.none(), st.text(min_size=8, max_size=32)),
    user_id=st.one_of(st.none(), st.text(min_size=4, max_size=16)),
)
@settings(max_examples=30)
def test_alert_structure(
    threat_type: str,
    severity: str,
    description: str,
    evidence: str,
    trace_id: str | None,
    user_id: str | None,
):
    """Alerts have all required fields."""
    manager = AlertManager()
    
    alert = manager.create_threat_alert(
        threat_type=threat_type,
        severity=severity,
        description=description,
        evidence=evidence,
        trace_id=trace_id,
        user_id=user_id,
    )
    
    assert alert.alert_id is not None
    assert alert.title is not None
    assert alert.message is not None
    assert alert.priority is not None
    assert alert.status == AlertStatus.OPEN
    assert alert.timestamp is not None
    
    if trace_id:
        assert alert.trace_id == trace_id
    if user_id:
        assert alert.user_id == user_id


# =============================================================================
# Property: Anomaly alerts have correct structure
# =============================================================================

@given(
    anomaly_type=st.sampled_from(["cost_spike", "latency_spike", "token_spike", "error_rate_spike"]),
    severity=st.sampled_from(["critical", "high", "medium", "low"]),
    current_value=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False),
    expected_value=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False),
)
@settings(max_examples=30)
def test_anomaly_alert_structure(
    anomaly_type: str,
    severity: str,
    current_value: float,
    expected_value: float,
):
    """Anomaly alerts have correct structure."""
    manager = AlertManager()
    
    alert = manager.create_anomaly_alert(
        anomaly_type=anomaly_type,
        severity=severity,
        current_value=current_value,
        expected_value=expected_value,
        description="Test anomaly",
    )
    
    assert alert.alert_id is not None
    assert anomaly_type in alert.tags.get("anomaly_type", "")
    assert str(current_value) in alert.message or "Current Value" in alert.message


# =============================================================================
# Property: Quality alerts have correct structure
# =============================================================================

@given(
    quality_score=st.floats(min_value=0.0, max_value=0.69, allow_nan=False),
    threshold=st.floats(min_value=0.7, max_value=1.0, allow_nan=False),
    issues=st.lists(st.text(min_size=5, max_size=50), min_size=1, max_size=5),
)
@settings(max_examples=20)
def test_quality_alert_structure(
    quality_score: float,
    threshold: float,
    issues: list[str],
):
    """Quality alerts have correct structure."""
    manager = AlertManager()
    
    alert = manager.create_quality_alert(
        quality_score=quality_score,
        threshold=threshold,
        issues=issues,
    )
    
    assert alert.alert_id is not None
    assert "Quality" in alert.title or "quality" in alert.title.lower()
    assert str(round(quality_score, 2)) in alert.message


# =============================================================================
# Property: Alert serialization
# =============================================================================

@given(
    title=st.text(min_size=5, max_size=100),
    message=st.text(min_size=10, max_size=500),
    priority=st.sampled_from(list(AlertPriority)),
)
@settings(max_examples=30)
def test_alert_serialization(title: str, message: str, priority: AlertPriority):
    """Alerts serialize correctly."""
    alert = Alert(
        alert_id="test_123",
        title=title,
        message=message,
        priority=priority,
    )
    
    data = alert.to_dict()
    
    assert data["alert_id"] == "test_123"
    assert data["title"] == title
    assert data["message"] == message
    assert data["priority"] == priority.value
    assert data["status"] == AlertStatus.OPEN.value


# =============================================================================
# Property: Datadog event format
# =============================================================================

@given(
    priority=st.sampled_from(list(AlertPriority)),
)
@settings(max_examples=10)
def test_datadog_event_format(priority: AlertPriority):
    """Datadog event format is valid."""
    alert = Alert(
        alert_id="test_123",
        title="Test Alert",
        message="Test message",
        priority=priority,
        tags={"service": "test", "env": "development"},
        trace_id="trace_abc",
    )
    
    event = alert.to_datadog_event()
    
    assert "title" in event
    assert "text" in event
    assert "priority" in event
    assert event["priority"] in ("normal", "low")
    assert "alert_type" in event
    assert event["alert_type"] in ("error", "warning", "info")
    assert "tags" in event
    assert isinstance(event["tags"], list)
    assert any("priority:" in t for t in event["tags"])


# =============================================================================
# Property: Alert lifecycle management
# =============================================================================

def test_alert_acknowledge():
    """Acknowledging an alert changes its status."""
    manager = AlertManager()
    
    alert = manager.create_threat_alert(
        threat_type="test",
        severity="medium",
        description="Test",
        evidence="Evidence",
    )
    
    assert alert.status == AlertStatus.OPEN
    
    success = manager.acknowledge_alert(alert.alert_id)
    
    assert success is True
    assert alert.status == AlertStatus.ACKNOWLEDGED


def test_alert_resolve():
    """Resolving an alert changes its status."""
    manager = AlertManager()
    
    alert = manager.create_threat_alert(
        threat_type="test",
        severity="medium",
        description="Test",
        evidence="Evidence",
    )
    
    success = manager.resolve_alert(alert.alert_id)
    
    assert success is True
    assert alert.status == AlertStatus.RESOLVED


def test_acknowledge_nonexistent_alert():
    """Acknowledging nonexistent alert returns False."""
    manager = AlertManager()
    
    success = manager.acknowledge_alert("nonexistent")
    
    assert success is False


# =============================================================================
# Property: Active alerts filtering
# =============================================================================

@given(
    num_alerts=st.integers(min_value=3, max_value=10),
)
@settings(max_examples=10)
def test_active_alerts_filtering(num_alerts: int):
    """Active alerts excludes resolved alerts."""
    manager = AlertManager()
    
    alerts = []
    for i in range(num_alerts):
        alert = manager.create_threat_alert(
            threat_type="test",
            severity="medium",
            description=f"Test {i}",
            evidence="Evidence",
        )
        alerts.append(alert)
    
    # All should be active
    active = manager.get_active_alerts()
    assert len(active) == num_alerts
    
    # Resolve some
    for alert in alerts[:num_alerts // 2]:
        manager.resolve_alert(alert.alert_id)
    
    # Should have fewer active
    active = manager.get_active_alerts()
    assert len(active) == num_alerts - (num_alerts // 2)


# =============================================================================
# Property: Remediation suggestions
# =============================================================================

THREAT_TYPES_WITH_REMEDIATION = [
    "prompt_injection",
    "pii_leakage",
    "toxic_content",
    "jailbreak",
]


@pytest.mark.parametrize("threat_type", THREAT_TYPES_WITH_REMEDIATION)
def test_remediation_provided(threat_type: str):
    """Known threat types have remediation suggestions."""
    manager = AlertManager()
    
    alert = manager.create_threat_alert(
        threat_type=threat_type,
        severity="high",
        description="Test",
        evidence="Evidence",
    )
    
    assert alert.remediation is not None
    assert len(alert.remediation) > 10


# =============================================================================
# Property: Default tags are included
# =============================================================================

@given(
    default_tag_key=st.text(min_size=3, max_size=20).filter(lambda x: x.isidentifier()),
    default_tag_value=st.text(min_size=3, max_size=50),
)
@settings(max_examples=20)
def test_default_tags_included(default_tag_key: str, default_tag_value: str):
    """Default tags are included in all alerts."""
    manager = AlertManager(
        default_tags={default_tag_key: default_tag_value}
    )
    
    alert = manager.create_threat_alert(
        threat_type="test",
        severity="medium",
        description="Test",
        evidence="Evidence",
    )
    
    assert alert.tags.get(default_tag_key) == default_tag_value
