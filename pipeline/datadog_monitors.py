"""
GuardianAI Datadog Monitors Setup for Pipeline

Programmatically creates and manages Datadog detection monitors using
pipeline configuration. Integrates with the GuardianAI processing pipeline
to monitor threats, quality, cost, and performance.
"""

import logging
from typing import Dict, Any, List, Optional
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v1.model.monitor import Monitor
from datadog_api_client.v1.model.monitor_type import MonitorType
from datadog_api_client.v1.model.monitor_options import MonitorOptions
from datadog_api_client.v1.model.monitor_thresholds import MonitorThresholds

from config import get_config, PipelineConfig

logger = logging.getLogger(__name__)


class DatadogMonitorSetup:
    """
    Sets up Datadog monitors for GuardianAI using pipeline configuration.
    
    Creates monitors based on configured thresholds:
    1. Cost Anomaly Monitor (threshold from config)
    2. Security Threat Monitor (threshold from config)
    3. Quality Degradation Monitor (threshold from config)
    4. High Latency Monitor (threshold from config)
    5. Error Rate Monitor (threshold from config)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize Datadog Monitor Setup.
        
        Args:
            config: Pipeline configuration (uses get_config() if not provided)
        """
        self.config = config or get_config()
        
        # Validate Datadog configuration
        if not self.config.datadog.api_key or not self.config.datadog.app_key:
            raise ValueError(
                "Datadog API keys not configured. Set DD_API_KEY and DD_APP_KEY environment variables."
            )
        
        # Configure Datadog API client
        self.configuration = Configuration()
        self.configuration.api_key["apiKeyAuth"] = self.config.datadog.api_key
        self.configuration.api_key["appKeyAuth"] = self.config.datadog.app_key
        self.configuration.server_variables["site"] = self.config.datadog.site
        
        # Webhook URL (assumes backend is running)
        self.webhook_url = "http://localhost:8000/api/webhooks/datadog"
        
        logger.info(f"DatadogMonitorSetup initialized with site={self.config.datadog.site}")

    def list_guardianai_monitors(self) -> List[Dict[str, Any]]:
        """Get all existing GuardianAI monitors."""
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                monitors = api_instance.list_monitors(tags="guardianai")
                return [
                    {
                        "id": m.id,
                        "name": m.name,
                        "type": m.type.value if hasattr(m.type, 'value') else str(m.type),
                        "tags": m.tags if m.tags else []
                    }
                    for m in monitors
                ]
        except Exception as e:
            logger.error(f"Failed to list monitors: {e}")
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

    def create_cost_anomaly_monitor(self) -> Optional[int]:
        """
        Monitor 1: Cost Anomaly Detection
        
        Uses config.thresholds.cost_anomaly_threshold_usd
        Triggers when: Daily cost exceeds configured threshold
        """
        threshold_usd = self.config.thresholds.cost_anomaly_threshold_usd
        warning_usd = threshold_usd * 0.75  # Warning at 75% of threshold
        
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                
                monitor = Monitor(
                    name=f"[GuardianAI] Cost Anomaly Alert (>${threshold_usd:,.0f}/day)",
                    type=MonitorType("metric alert"),
                    query=f"sum(last_1d):sum:guardianai.cost.total{{*}} > {threshold_usd}",
                    message=f"""
**GuardianAI Cost Anomaly Detected** 💰

Daily LLM costs have exceeded ${threshold_usd:,.0f}.

**Current Threshold:** ${threshold_usd:,.0f}/day
**Warning Threshold:** ${warning_usd:,.0f}/day

**Action Items:**
1. Review high-cost API calls in dashboard
2. Check for runaway processes or loops
3. Verify cost optimization settings
4. Consider implementing rate limiting

**Configuration:**
- Environment: {self.config.environment.value}
- Metric: `guardianai.cost.total`

**Webhook:** {self.webhook_url}

@webhook-{self.webhook_url}
                    """.strip(),
                    tags=["guardianai", "cost", "anomaly", f"env:{self.config.environment.value}"],
                    options=MonitorOptions(
                        thresholds=MonitorThresholds(
                            critical=float(threshold_usd),
                            warning=float(warning_usd),
                        ),
                        notify_no_data=False,
                        require_full_window=False,
                        notify_audit=True,
                        include_tags=True,
                    ),
                    priority=1,  # Critical
                )
                
                response = api_instance.create_monitor(body=monitor)
                logger.info(f"Created Cost Anomaly Monitor (ID: {response.id}, threshold: ${threshold_usd:,.0f})")
                return response.id
                
        except Exception as e:
            logger.error(f"Failed to create cost anomaly monitor: {e}")
            return None

    def create_threat_detection_monitor(self) -> Optional[int]:
        """
        Monitor 2: Security Threat Detection
        
        Uses config.thresholds.threat_confidence_threshold
        Triggers when: >5 high-confidence threats per minute
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                
                monitor = Monitor(
                    name="[GuardianAI] Security Threat Detection Alert",
                    type=MonitorType("metric alert"),
                    query="sum(last_1m):sum:guardianai.threats.detected{severity:high OR severity:critical}.as_rate() > 5",
                    message=f"""
**GuardianAI Security Threat Alert** 🔒

High rate of security threats detected (>5 high-severity threats/minute).

**Threat Types:**
- Prompt injection attacks
- Jailbreak attempts  
- Toxic content
- PII leaks

**Confidence Threshold:** {self.config.thresholds.threat_confidence_threshold}

**Action Items:**
1. Enable rate limiting for suspicious IPs
2. Review recent requests in dashboard
3. Block malicious user accounts
4. Notify security team

**Configuration:**
- Environment: {self.config.environment.value}
- Metric: `guardianai.threats.detected`

**Webhook:** {self.webhook_url}

@webhook-{self.webhook_url}
                    """.strip(),
                    tags=["guardianai", "security", "threat", f"env:{self.config.environment.value}"],
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
                    priority=1,  # Critical
                )
                
                response = api_instance.create_monitor(body=monitor)
                logger.info(f"Created Threat Detection Monitor (ID: {response.id})")
                return response.id
                
        except Exception as e:
            logger.error(f"Failed to create threat detection monitor: {e}")
            return None

    def create_quality_degradation_monitor(self) -> Optional[int]:
        """
        Monitor 3: Quality Score Degradation
        
        Uses config.thresholds.quality_degradation_threshold
        Triggers when: Average quality score falls below threshold
        """
        threshold = self.config.thresholds.quality_degradation_threshold
        warning = threshold + 0.1  # Warning slightly above threshold
        
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                
                monitor = Monitor(
                    name=f"[GuardianAI] Quality Degradation Alert (<{threshold})",
                    type=MonitorType("metric alert"),
                    query=f"avg(last_5m):avg:guardianai.quality.overall_score{{*}} < {threshold}",
                    message=f"""
**GuardianAI Quality Degradation Alert** 📉

LLM response quality has fallen below acceptable threshold.

**Current Threshold:** {threshold} (0-1 scale)
**Warning Threshold:** {warning}

**Possible Causes:**
- Model configuration issues
- Prompt engineering problems
- Context window overflow
- Model API degradation
- Insufficient system prompts

**Action Items:**
1. Review recent low-quality responses
2. Check model configuration and temperature
3. Verify prompt templates
4. Test with sample prompts

**Configuration:**
- Environment: {self.config.environment.value}
- Metric: `guardianai.quality.overall_score`
- Minimum Coherence: {self.config.thresholds.coherence_min}
- Minimum Relevance: {self.config.thresholds.relevance_min}

**Webhook:** {self.webhook_url}

@webhook-{self.webhook_url}
                    """.strip(),
                    tags=["guardianai", "quality", f"env:{self.config.environment.value}"],
                    options=MonitorOptions(
                        thresholds=MonitorThresholds(
                            critical=float(threshold),
                            warning=float(warning),
                        ),
                        notify_no_data=False,
                        require_full_window=True,
                        notify_audit=True,
                        include_tags=True,
                    ),
                    priority=2,  # High
                )
                
                response = api_instance.create_monitor(body=monitor)
                logger.info(f"Created Quality Degradation Monitor (ID: {response.id}, threshold: {threshold})")
                return response.id
                
        except Exception as e:
            logger.error(f"Failed to create quality degradation monitor: {e}")
            return None

    def create_latency_spike_monitor(self) -> Optional[int]:
        """
        Monitor 4: High Latency Alert
        
        Uses config.thresholds.latency_spike_threshold_ms
        Triggers when: P95 latency exceeds threshold
        """
        threshold_ms = self.config.thresholds.latency_spike_threshold_ms
        warning_ms = int(threshold_ms * 0.8)  # Warning at 80% of threshold
        
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                
                monitor = Monitor(
                    name=f"[GuardianAI] High Latency Alert (>{threshold_ms}ms)",
                    type=MonitorType("metric alert"),
                    query=f"avg(last_5m):p95:guardianai.latency.response_time{{*}} > {threshold_ms}",
                    message=f"""
**GuardianAI Latency Spike Alert** ⏱️

LLM response latency (P95) has exceeded acceptable threshold.

**Current Threshold:** {threshold_ms}ms
**Warning Threshold:** {warning_ms}ms
**P95 Target:** {self.config.thresholds.latency_p95_threshold_ms}ms

**Possible Causes:**
- Model API slowdown or outage
- Network connectivity issues
- High request volume / queuing
- Oversized context windows
- Rate limiting from provider

**Action Items:**
1. Check model provider status page
2. Review request patterns and volumes
3. Consider implementing caching
4. Optimize prompt lengths
5. Use faster models for simple queries

**Configuration:**
- Environment: {self.config.environment.value}
- Metric: `guardianai.latency.response_time`
- Model: {self.config.gemini.model_name}

**Webhook:** {self.webhook_url}

@webhook-{self.webhook_url}
                    """.strip(),
                    tags=["guardianai", "performance", "latency", f"env:{self.config.environment.value}"],
                    options=MonitorOptions(
                        thresholds=MonitorThresholds(
                            critical=float(threshold_ms),
                            warning=float(warning_ms),
                        ),
                        notify_no_data=False,
                        require_full_window=True,
                        notify_audit=True,
                        include_tags=True,
                    ),
                    priority=2,  # High
                )
                
                response = api_instance.create_monitor(body=monitor)
                logger.info(f"Created Latency Spike Monitor (ID: {response.id}, threshold: {threshold_ms}ms)")
                return response.id
                
        except Exception as e:
            logger.error(f"Failed to create latency spike monitor: {e}")
            return None

    def create_error_rate_monitor(self) -> Optional[int]:
        """
        Monitor 5: Error Rate Alert
        
        Uses config.thresholds.error_rate_threshold
        Triggers when: Error rate exceeds threshold
        """
        threshold_pct = self.config.thresholds.error_rate_threshold * 100
        warning_pct = threshold_pct * 0.75
        
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                
                monitor = Monitor(
                    name=f"[GuardianAI] High Error Rate Alert (>{threshold_pct}%)",
                    type=MonitorType("metric alert"),
                    query=f"avg(last_5m):(sum:guardianai.requests.errors{{*}}.as_count() / sum:guardianai.requests.total{{*}}.as_count()) * 100 > {threshold_pct}",
                    message=f"""
**GuardianAI Error Rate Alert** ⚠️

Request error rate has exceeded acceptable threshold.

**Current Threshold:** {threshold_pct}%
**Warning Threshold:** {warning_pct}%

**Possible Causes:**
- Model API errors or timeouts
- Invalid request formats
- Authentication failures
- Rate limiting
- Network issues

**Action Items:**
1. Check error logs for patterns
2. Verify API credentials
3. Review request validation
4. Check model provider status
5. Implement retry logic

**Configuration:**
- Environment: {self.config.environment.value}
- Metric: `guardianai.requests.errors`

**Webhook:** {self.webhook_url}

@webhook-{self.webhook_url}
                    """.strip(),
                    tags=["guardianai", "errors", f"env:{self.config.environment.value}"],
                    options=MonitorOptions(
                        thresholds=MonitorThresholds(
                            critical=float(threshold_pct),
                            warning=float(warning_pct),
                        ),
                        notify_no_data=False,
                        require_full_window=True,
                        notify_audit=True,
                        include_tags=True,
                    ),
                    priority=2,  # High
                )
                
                response = api_instance.create_monitor(body=monitor)
                logger.info(f"Created Error Rate Monitor (ID: {response.id}, threshold: {threshold_pct}%)")
                return response.id
                
        except Exception as e:
            logger.error(f"Failed to create error rate monitor: {e}")
            return None

    def setup_all_monitors(self) -> Dict[str, Optional[int]]:
        """
        Set up all GuardianAI monitors using pipeline configuration.
        
        Returns:
            Dictionary mapping monitor name to monitor ID
        """
        logger.info("Setting up GuardianAI Datadog monitors...")
        logger.info(f"Using thresholds from config: env={self.config.environment.value}")
        
        monitors = {
            "cost_anomaly": self.create_cost_anomaly_monitor(),
            "threat_detection": self.create_threat_detection_monitor(),
            "quality_degradation": self.create_quality_degradation_monitor(),
            "latency_spike": self.create_latency_spike_monitor(),
            "error_rate": self.create_error_rate_monitor(),
        }
        
        success_count = sum(1 for mid in monitors.values() if mid is not None)
        logger.info(f"Successfully created {success_count}/5 monitors")
        
        if success_count < 5:
            failed = [name for name, mid in monitors.items() if mid is None]
            logger.warning(f"Failed to create monitors: {failed}")
        
        return monitors

    def cleanup_all_monitors(self) -> int:
        """
        Delete all existing GuardianAI monitors.
        
        Returns:
            Number of monitors deleted
        """
        logger.info("Cleaning up existing GuardianAI monitors...")
        
        monitors = self.list_guardianai_monitors()
        deleted_count = 0
        
        for monitor in monitors:
            if self.delete_monitor(monitor["id"]):
                deleted_count += 1
        
        logger.info(f"Deleted {deleted_count} monitors")
        return deleted_count

    def get_monitor_summary(self) -> Dict[str, Any]:
        """
        Get summary of current monitor configuration.
        
        Returns:
            Summary dict with thresholds and monitor counts
        """
        monitors = self.list_guardianai_monitors()
        
        return {
            "total_monitors": len(monitors),
            "environment": self.config.environment.value,
            "thresholds": {
                "cost_anomaly_usd": self.config.thresholds.cost_anomaly_threshold_usd,
                "quality_min": self.config.thresholds.quality_degradation_threshold,
                "latency_max_ms": self.config.thresholds.latency_spike_threshold_ms,
                "error_rate_max": self.config.thresholds.error_rate_threshold,
                "threat_confidence_min": self.config.thresholds.threat_confidence_threshold,
            },
            "monitors": monitors,
        }


# For testing
if __name__ == "__main__":
    import os
    import json
    
    print("GuardianAI Datadog Monitor Setup")
    print("=" * 60)
    
    # Check environment
    if not os.getenv("DD_API_KEY") or not os.getenv("DD_APP_KEY"):
        print("⚠️  Datadog API keys not set!")
        print("\nTo set up monitors, you need:")
        print("  DD_API_KEY=your-api-key")
        print("  DD_APP_KEY=your-app-key")
        print("  DD_SITE=datadoghq.com (optional)")
        print("\nThis is optional for development. Monitors can be created later.")
        exit(0)
    
    try:
        # Initialize
        setup = DatadogMonitorSetup()
        
        # Show current configuration
        print("\nCurrent Configuration:")
        print(f"  Environment: {setup.config.environment.value}")
        print(f"  Cost Threshold: ${setup.config.thresholds.cost_anomaly_threshold_usd:,.0f}/day")
        print(f"  Quality Threshold: {setup.config.thresholds.quality_degradation_threshold}")
        print(f"  Latency Threshold: {setup.config.thresholds.latency_spike_threshold_ms}ms")
        print(f"  Error Rate Threshold: {setup.config.thresholds.error_rate_threshold * 100}%")
        
        # List existing monitors
        existing = setup.list_guardianai_monitors()
        print(f"\nExisting Monitors: {len(existing)}")
        for monitor in existing:
            print(f"  - {monitor['name']} (ID: {monitor['id']})")
        
        # Ask to proceed
        print("\nOptions:")
        print("  1. Create all monitors")
        print("  2. Delete all monitors")
        print("  3. Show summary")
        print("  4. Exit")
        
        choice = input("\nChoice (1-4): ").strip()
        
        if choice == "1":
            print("\n Creating monitors...")
            monitors = setup.setup_all_monitors()
            print("\n✅ Monitor Creation Results:")
            for name, mid in monitors.items():
                status = f"✅ ID: {mid}" if mid else "❌ Failed"
                print(f"  {name}: {status}")
        
        elif choice == "2":
            confirm = input("Delete all GuardianAI monitors? (yes/no): ").strip().lower()
            if confirm == "yes":
                deleted = setup.cleanup_all_monitors()
                print(f"\n✅ Deleted {deleted} monitors")
        
        elif choice == "3":
            summary = setup.get_monitor_summary()
            print("\n📊 Monitor Summary:")
            print(json.dumps(summary, indent=2))
        
        else:
            print("\nExiting...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
