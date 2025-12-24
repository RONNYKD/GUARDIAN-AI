"""
GuardianAI Datadog Monitors Manager

Programmatically creates and manages Datadog detection monitors for:
1. High Token Cost (>$100/hour)
2. Security Threats (>5 threats/minute)
3. Quality Degradation (score <0.6)
4. High Latency (>2 seconds)
5. Anomalous Request Patterns

These monitors trigger webhooks to the backend for incident creation and auto-remediation.
"""

import logging
from typing import Dict, Any, List, Optional
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v1.model.monitor import Monitor
from datadog_api_client.v1.model.monitor_type import MonitorType
from datadog_api_client.v1.model.monitor_options import MonitorOptions
from datadog_api_client.v1.model.monitor_thresholds import MonitorThresholds

from config import get_settings

logger = logging.getLogger(__name__)


class DatadogMonitorManager:
    """
    Manages Datadog monitors for GuardianAI detection rules.
    
    Creates 5 essential monitors:
    1. High Token Cost Alert
    2. Security Threat Detection
    3. Quality Score Degradation
    4. High Latency Alert
    5. Anomalous Request Pattern
    """

    def __init__(self):
        """Initialize Datadog Monitor Manager."""
        self.settings = get_settings()
        self.webhook_url = f"{self.settings.backend_url}/api/webhooks/datadog/alert"
        
        # Configure Datadog API client
        self.configuration = Configuration()
        self.configuration.api_key["apiKeyAuth"] = self.settings.dd_api_key
        self.configuration.api_key["appKeyAuth"] = self.settings.dd_app_key
        self.configuration.server_variables["site"] = self.settings.dd_site
        
        logger.info("DatadogMonitorManager initialized")

    def get_all_guardianai_monitors(self) -> List[Dict[str, Any]]:
        """Get all existing GuardianAI monitors."""
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                monitors = api_instance.list_monitors(tags="guardianai")
                return [monitor.to_dict() for monitor in monitors]
        except Exception as e:
            logger.error(f"Failed to get monitors: {e}")
            return []

    def delete_monitor(self, monitor_id: int) -> bool:
        """Delete a monitor by ID."""
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                api_instance.delete_monitor(monitor_id)
                logger.info(f"Deleted monitor {monitor_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete monitor {monitor_id}: {e}")
            return False

    def create_high_cost_monitor(self) -> Optional[int]:
        """
        Monitor 1: High Token Cost Alert
        
        Triggers when: Token cost exceeds $100/hour
        Priority: P1 (Critical)
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                
                monitor = Monitor(
                    name="[GuardianAI] High Token Cost Alert",
                    type=MonitorType("metric alert"),
                    query="sum(last_1h):sum:guardianai.cost.total{*} > 100",
                    message=f"""
**GuardianAI High Cost Alert** 🚨

Token costs have exceeded $100 in the last hour.

**Action Items:**
- Review high-cost LLM requests
- Check for runaway processes
- Verify cost optimization settings

**Priority:** P1 (Critical)
**Webhook:** {self.webhook_url}

@webhook-{self.webhook_url}
                    """.strip(),
                    tags=["guardianai", "cost", "priority:P1"],
                    options=MonitorOptions(
                        thresholds=MonitorThresholds(
                            critical=100.0,
                            warning=75.0,
                        ),
                        notify_no_data=False,
                        require_full_window=False,
                        notify_audit=True,
                        include_tags=True,
                    ),
                    priority=1,
                )
                
                response = api_instance.create_monitor(body=monitor)
                monitor_id = response.id
                logger.info(f"Created High Cost Monitor (ID: {monitor_id})")
                return monitor_id
                
        except Exception as e:
            logger.error(f"Failed to create high cost monitor: {e}")
            return None

    def create_security_threat_monitor(self) -> Optional[int]:
        """
        Monitor 2: Security Threat Detection
        
        Triggers when: More than 5 security threats detected per minute
        Priority: P1 (Critical)
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                
                monitor = Monitor(
                    name="[GuardianAI] Security Threat Detection",
                    type=MonitorType("metric alert"),
                    query="sum(last_1m):sum:guardianai.threats.detected{*}.as_rate() > 5",
                    message=f"""
**GuardianAI Security Alert** 🔒

High rate of security threats detected (>5/minute).

**Possible Threats:**
- Prompt injection attacks
- Jailbreak attempts
- Toxic content
- Data exfiltration attempts

**Action Items:**
- Enable rate limiting
- Review recent requests
- Block suspicious IPs

**Priority:** P1 (Critical)
**Webhook:** {self.webhook_url}

@webhook-{self.webhook_url}
                    """.strip(),
                    tags=["guardianai", "security", "priority:P1"],
                    options=MonitorOptions(
                        thresholds=MonitorThresholds(
                            critical=5.0,
                            warning=3.0,
                        ),
                        notify_no_data=False,
                        require_full_window=False,
                        notify_audit=True,
                        include_tags=True,
                    ),
                    priority=1,
                )
                
                response = api_instance.create_monitor(body=monitor)
                monitor_id = response.id
                logger.info(f"Created Security Threat Monitor (ID: {monitor_id})")
                return monitor_id
                
        except Exception as e:
            logger.error(f"Failed to create security threat monitor: {e}")
            return None

    def create_quality_degradation_monitor(self) -> Optional[int]:
        """
        Monitor 3: Quality Score Degradation
        
        Triggers when: Average quality score falls below 0.6
        Priority: P2 (High)
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                
                monitor = Monitor(
                    name="[GuardianAI] Quality Score Degradation",
                    type=MonitorType("metric alert"),
                    query="avg(last_5m):avg:guardianai.quality.score{*} < 0.6",
                    message=f"""
**GuardianAI Quality Alert** 📉

LLM response quality has degraded below acceptable threshold (0.6).

**Possible Causes:**
- Model configuration issues
- Context window problems
- Prompt engineering issues
- Model API issues

**Action Items:**
- Review recent responses
- Check model configuration
- Verify prompt templates

**Priority:** P2 (High)
**Webhook:** {self.webhook_url}

@webhook-{self.webhook_url}
                    """.strip(),
                    tags=["guardianai", "quality", "priority:P2"],
                    options=MonitorOptions(
                        thresholds=MonitorThresholds(
                            critical=0.6,
                            warning=0.7,
                        ),
                        notify_no_data=False,
                        require_full_window=True,
                        notify_audit=True,
                        include_tags=True,
                    ),
                    priority=2,
                )
                
                response = api_instance.create_monitor(body=monitor)
                monitor_id = response.id
                logger.info(f"Created Quality Degradation Monitor (ID: {monitor_id})")
                return monitor_id
                
        except Exception as e:
            logger.error(f"Failed to create quality degradation monitor: {e}")
            return None

    def create_high_latency_monitor(self) -> Optional[int]:
        """
        Monitor 4: High Latency Alert
        
        Triggers when: P95 latency exceeds 2 seconds
        Priority: P2 (High)
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                
                monitor = Monitor(
                    name="[GuardianAI] High Latency Alert",
                    type=MonitorType("metric alert"),
                    query="avg(last_5m):p95:guardianai.latency.ms{*} > 2000",
                    message=f"""
**GuardianAI Latency Alert** ⏱️

LLM response latency (P95) has exceeded 2 seconds.

**Possible Causes:**
- Model API slowdown
- Network issues
- High request volume
- Context window too large

**Action Items:**
- Check model status
- Review request patterns
- Consider caching
- Optimize prompts

**Priority:** P2 (High)
**Webhook:** {self.webhook_url}

@webhook-{self.webhook_url}
                    """.strip(),
                    tags=["guardianai", "performance", "priority:P2"],
                    options=MonitorOptions(
                        thresholds=MonitorThresholds(
                            critical=2000.0,
                            warning=1500.0,
                        ),
                        notify_no_data=False,
                        require_full_window=True,
                        notify_audit=True,
                        include_tags=True,
                    ),
                    priority=2,
                )
                
                response = api_instance.create_monitor(body=monitor)
                monitor_id = response.id
                logger.info(f"Created High Latency Monitor (ID: {monitor_id})")
                return monitor_id
                
        except Exception as e:
            logger.error(f"Failed to create high latency monitor: {e}")
            return None

    def create_anomaly_detection_monitor(self) -> Optional[int]:
        """
        Monitor 5: Anomalous Request Pattern
        
        Triggers when: Request rate deviates >3 standard deviations
        Priority: P3 (Medium)
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                
                monitor = Monitor(
                    name="[GuardianAI] Anomalous Request Pattern",
                    type=MonitorType("query alert"),
                    query="avg(last_15m):anomalies(avg:guardianai.requests.count{*}.as_rate(), 'agile', 3) >= 1",
                    message=f"""
**GuardianAI Anomaly Alert** 📊

Unusual request pattern detected (>3 std deviations).

**Possible Causes:**
- Traffic spike
- DDoS attack
- Bot activity
- Integration issues

**Action Items:**
- Review traffic sources
- Check for bot patterns
- Verify API authentication
- Consider rate limiting

**Priority:** P3 (Medium)
**Webhook:** {self.webhook_url}

@webhook-{self.webhook_url}
                    """.strip(),
                    tags=["guardianai", "anomaly", "priority:P3"],
                    options=MonitorOptions(
                        thresholds=MonitorThresholds(
                            critical=1.0,
                        ),
                        notify_no_data=False,
                        require_full_window=False,
                        notify_audit=True,
                        include_tags=True,
                    ),
                    priority=3,
                )
                
                response = api_instance.create_monitor(body=monitor)
                monitor_id = response.id
                logger.info(f"Created Anomaly Detection Monitor (ID: {monitor_id})")
                return monitor_id
                
        except Exception as e:
            logger.error(f"Failed to create anomaly detection monitor: {e}")
            return None

    def setup_all_monitors(self) -> Dict[str, Optional[int]]:
        """
        Set up all 5 GuardianAI monitors.
        
        Returns:
            Dictionary mapping monitor name to monitor ID
        """
        logger.info("Setting up GuardianAI monitors...")
        
        monitors = {
            "high_cost": self.create_high_cost_monitor(),
            "security_threat": self.create_security_threat_monitor(),
            "quality_degradation": self.create_quality_degradation_monitor(),
            "high_latency": self.create_high_latency_monitor(),
            "anomaly_detection": self.create_anomaly_detection_monitor(),
        }
        
        success_count = sum(1 for mid in monitors.values() if mid is not None)
        logger.info(f"Successfully created {success_count}/5 monitors")
        
        return monitors

    def cleanup_all_guardianai_monitors(self) -> int:
        """
        Delete all existing GuardianAI monitors.
        
        Returns:
            Number of monitors deleted
        """
        monitors = self.get_all_guardianai_monitors()
        deleted_count = 0
        
        for monitor in monitors:
            if self.delete_monitor(monitor["id"]):
                deleted_count += 1
        
        logger.info(f"Deleted {deleted_count} GuardianAI monitors")
        return deleted_count


# Singleton instance
_monitor_manager: Optional[DatadogMonitorManager] = None


def get_monitor_manager() -> DatadogMonitorManager:
    """Get or create DatadogMonitorManager singleton."""
    global _monitor_manager
    if _monitor_manager is None:
        _monitor_manager = DatadogMonitorManager()
    return _monitor_manager
