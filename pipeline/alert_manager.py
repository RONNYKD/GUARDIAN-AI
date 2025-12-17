"""
GuardianAI Alert Manager

Manages alert generation and routing to Datadog.
Implements alert creation for detected threats and anomalies.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AlertPriority(str, Enum):
    """Alert priority levels."""
    P1 = "p1"  # Critical - immediate action required
    P2 = "p2"  # High - action within 1 hour
    P3 = "p3"  # Medium - action within 4 hours
    P4 = "p4"  # Low - action within 24 hours
    P5 = "p5"  # Informational - no action required


class AlertStatus(str, Enum):
    """Alert status."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """An alert to be sent to monitoring systems."""
    alert_id: str
    title: str
    message: str
    priority: AlertPriority
    status: AlertStatus = AlertStatus.OPEN
    source: str = "guardianai"
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    remediation: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "status": self.status.value,
            "source": self.source,
            "tags": self.tags,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "remediation": self.remediation,
        }
    
    def to_datadog_event(self) -> dict[str, Any]:
        """Convert to Datadog event format."""
        priority_map = {
            AlertPriority.P1: "normal",  # Datadog only has normal/low
            AlertPriority.P2: "normal",
            AlertPriority.P3: "normal",
            AlertPriority.P4: "low",
            AlertPriority.P5: "low",
        }
        
        alert_type_map = {
            AlertPriority.P1: "error",
            AlertPriority.P2: "error",
            AlertPriority.P3: "warning",
            AlertPriority.P4: "warning",
            AlertPriority.P5: "info",
        }
        
        tags = [f"{k}:{v}" for k, v in self.tags.items()]
        tags.append(f"priority:{self.priority.value}")
        tags.append(f"source:{self.source}")
        
        if self.trace_id:
            tags.append(f"trace_id:{self.trace_id}")
        
        return {
            "title": self.title,
            "text": self.message,
            "priority": priority_map[self.priority],
            "alert_type": alert_type_map[self.priority],
            "tags": tags,
            "source_type_name": "guardianai",
        }


class AlertManager:
    """
    Manages alert generation and routing.
    
    Creates alerts from detected threats and anomalies,
    routes to Datadog, and tracks alert state.
    
    Example:
        >>> manager = AlertManager()
        >>> alert = manager.create_threat_alert(threat)
        >>> await manager.send_to_datadog(alert)
    """
    
    def __init__(
        self,
        datadog_api_key: Optional[str] = None,
        datadog_app_key: Optional[str] = None,
        default_tags: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Initialize alert manager.
        
        Args:
            datadog_api_key: Datadog API key
            datadog_app_key: Datadog App key
            default_tags: Default tags for all alerts
        """
        self.datadog_api_key = datadog_api_key
        self.datadog_app_key = datadog_app_key
        self.default_tags = default_tags or {}
        
        self._alert_counter = 0
        self._active_alerts: dict[str, Alert] = {}
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        self._alert_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"alert_{timestamp}_{self._alert_counter:04d}"
    
    def create_threat_alert(
        self,
        threat_type: str,
        severity: str,
        description: str,
        evidence: str,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Alert:
        """
        Create alert from detected threat.
        
        Args:
            threat_type: Type of threat
            severity: Threat severity
            description: Threat description
            evidence: Evidence of threat
            trace_id: Trace ID
            user_id: User ID
        
        Returns:
            Alert object
        """
        # Map severity to priority
        priority_map = {
            "critical": AlertPriority.P1,
            "high": AlertPriority.P2,
            "medium": AlertPriority.P3,
            "low": AlertPriority.P4,
        }
        priority = priority_map.get(severity, AlertPriority.P3)
        
        # Generate remediation suggestion
        remediation = self._get_threat_remediation(threat_type)
        
        tags = dict(self.default_tags)
        tags.update({
            "threat_type": threat_type,
            "severity": severity,
        })
        
        alert = Alert(
            alert_id=self._generate_alert_id(),
            title=f"[{severity.upper()}] {threat_type.replace('_', ' ').title()} Detected",
            message=f"{description}\n\nEvidence: {evidence}",
            priority=priority,
            tags=tags,
            trace_id=trace_id,
            user_id=user_id,
            remediation=remediation,
        )
        
        self._active_alerts[alert.alert_id] = alert
        return alert
    
    def create_anomaly_alert(
        self,
        anomaly_type: str,
        severity: str,
        current_value: float,
        expected_value: float,
        description: str,
        trace_id: Optional[str] = None,
    ) -> Alert:
        """
        Create alert from detected anomaly.
        
        Args:
            anomaly_type: Type of anomaly
            severity: Anomaly severity
            current_value: Current metric value
            expected_value: Expected/baseline value
            description: Anomaly description
            trace_id: Trace ID
        
        Returns:
            Alert object
        """
        priority_map = {
            "critical": AlertPriority.P1,
            "high": AlertPriority.P2,
            "medium": AlertPriority.P3,
            "low": AlertPriority.P4,
        }
        priority = priority_map.get(severity, AlertPriority.P3)
        
        remediation = self._get_anomaly_remediation(anomaly_type)
        
        tags = dict(self.default_tags)
        tags.update({
            "anomaly_type": anomaly_type,
            "severity": severity,
        })
        
        message = (
            f"{description}\n\n"
            f"Current Value: {current_value:.2f}\n"
            f"Expected Value: {expected_value:.2f}"
        )
        
        alert = Alert(
            alert_id=self._generate_alert_id(),
            title=f"[{severity.upper()}] {anomaly_type.replace('_', ' ').title()} Anomaly",
            message=message,
            priority=priority,
            tags=tags,
            trace_id=trace_id,
            remediation=remediation,
        )
        
        self._active_alerts[alert.alert_id] = alert
        return alert
    
    def create_quality_alert(
        self,
        quality_score: float,
        threshold: float,
        issues: list[str],
        trace_id: Optional[str] = None,
    ) -> Alert:
        """
        Create alert for quality degradation.
        
        Args:
            quality_score: Current quality score
            threshold: Quality threshold
            issues: List of quality issues
            trace_id: Trace ID
        
        Returns:
            Alert object
        """
        severity = "high" if quality_score < 0.5 else "medium"
        priority = AlertPriority.P2 if severity == "high" else AlertPriority.P3
        
        tags = dict(self.default_tags)
        tags.update({
            "anomaly_type": "quality_degradation",
            "severity": severity,
        })
        
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        message = (
            f"Response quality score {quality_score:.2f} below threshold {threshold}\n\n"
            f"Issues:\n{issues_text}"
        )
        
        alert = Alert(
            alert_id=self._generate_alert_id(),
            title=f"[{severity.upper()}] Quality Degradation Detected",
            message=message,
            priority=priority,
            tags=tags,
            trace_id=trace_id,
            remediation="Review model outputs and consider adjusting temperature or prompts",
        )
        
        self._active_alerts[alert.alert_id] = alert
        return alert
    
    def _get_threat_remediation(self, threat_type: str) -> str:
        """Get remediation suggestion for threat type."""
        remediations = {
            "prompt_injection": (
                "1. Block the request immediately\n"
                "2. Log user details for investigation\n"
                "3. Consider rate-limiting the user\n"
                "4. Review and strengthen input validation"
            ),
            "pii_leakage": (
                "1. Redact the response before delivery\n"
                "2. Review prompt for PII extraction attempts\n"
                "3. Implement output filtering\n"
                "4. Audit model training data"
            ),
            "toxic_content": (
                "1. Block the content from being delivered\n"
                "2. Log for content moderation review\n"
                "3. Consider user warning/suspension\n"
                "4. Review content filtering rules"
            ),
            "jailbreak": (
                "1. Block the request immediately\n"
                "2. Reset conversation context\n"
                "3. Log user for investigation\n"
                "4. Review and strengthen system prompts"
            ),
        }
        return remediations.get(threat_type, "Review the threat and take appropriate action")
    
    def _get_anomaly_remediation(self, anomaly_type: str) -> str:
        """Get remediation suggestion for anomaly type."""
        remediations = {
            "cost_spike": (
                "1. Enable rate limiting for affected service\n"
                "2. Review recent traffic patterns\n"
                "3. Check for runaway processes\n"
                "4. Consider temporary token limits"
            ),
            "latency_spike": (
                "1. Check model provider status\n"
                "2. Review request complexity\n"
                "3. Consider request queuing\n"
                "4. Check infrastructure health"
            ),
            "token_spike": (
                "1. Enable token rate limiting\n"
                "2. Review prompts for excessive length\n"
                "3. Check for prompt stuffing attacks\n"
                "4. Implement input truncation"
            ),
            "error_rate_spike": (
                "1. Check model provider health\n"
                "2. Review error logs\n"
                "3. Implement circuit breaker\n"
                "4. Notify engineering team"
            ),
            "quality_degradation": (
                "1. Review model outputs\n"
                "2. Check temperature settings\n"
                "3. Review system prompt\n"
                "4. Consider model fallback"
            ),
        }
        return remediations.get(anomaly_type, "Review the anomaly and investigate root cause")
    
    async def send_to_datadog(self, alert: Alert) -> bool:
        """
        Send alert to Datadog as an event.
        
        Args:
            alert: Alert to send
        
        Returns:
            True if sent successfully
        """
        if not self.datadog_api_key:
            logger.warning("No Datadog API key configured, skipping alert send")
            return False
        
        try:
            from datadog_api_client import Configuration, ApiClient
            from datadog_api_client.v1.api.events_api import EventsApi
            from datadog_api_client.v1.model.event_create_request import EventCreateRequest
            
            configuration = Configuration()
            configuration.api_key["apiKeyAuth"] = self.datadog_api_key
            
            if self.datadog_app_key:
                configuration.api_key["appKeyAuth"] = self.datadog_app_key
            
            async with ApiClient(configuration) as api_client:
                api = EventsApi(api_client)
                
                event_data = alert.to_datadog_event()
                request = EventCreateRequest(**event_data)
                
                response = await api.create_event(body=request)
                logger.info(f"Alert {alert.alert_id} sent to Datadog")
                return True
                
        except ImportError:
            logger.warning("datadog-api-client not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to send alert to Datadog: {e}")
            return False
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id].status = AlertStatus.RESOLVED
            return True
        return False
    
    def get_active_alerts(self) -> list[Alert]:
        """Get all active (non-resolved) alerts."""
        return [
            alert for alert in self._active_alerts.values()
            if alert.status not in (AlertStatus.RESOLVED, AlertStatus.SUPPRESSED)
        ]
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        return self._active_alerts.get(alert_id)
