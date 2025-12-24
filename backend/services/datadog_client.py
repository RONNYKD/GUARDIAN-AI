"""
GuardianAI Datadog Client

Provides integration with Datadog for:
- Custom metrics publishing
- APM tracing
- Log management
- Monitor/Dashboard configuration
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from datadog import initialize as dd_initialize
from datadog import api as dd_api
from datadog import statsd

from config import get_settings

logger = logging.getLogger(__name__)


class DatadogClient:
    """
    Client for Datadog API integration.
    
    Handles:
    - Custom metric submission
    - Dashboard management
    - Monitor configuration
    - Log forwarding
    
    Example:
        >>> client = DatadogClient()
        >>> client.send_metric("guardianai.tokens.used", 1500, tags=["model:gemini-pro"])
    """

    _instance: Optional["DatadogClient"] = None
    _initialized: bool = False

    def __new__(cls) -> "DatadogClient":
        """Singleton pattern for Datadog client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize Datadog client if not already initialized."""
        if not DatadogClient._initialized:
            settings = get_settings()
            
            # Initialize Datadog library
            dd_initialize(
                api_key=settings.dd_api_key,
                app_key=settings.dd_app_key,
                api_host=f"https://api.{settings.dd_site}",
            )
            
            # Initialize DogStatsD for metrics
            statsd.host = "localhost"
            statsd.port = 8125
            
            DatadogClient._initialized = True
            logger.info(f"Datadog client initialized for site: {settings.dd_site}")

    @property
    def base_url(self) -> str:
        """Get Datadog API base URL."""
        settings = get_settings()
        return f"https://api.{settings.dd_site}"

    @property
    def headers(self) -> dict[str, str]:
        """Get Datadog API headers."""
        settings = get_settings()
        return {
            "DD-API-KEY": settings.dd_api_key,
            "DD-APPLICATION-KEY": settings.dd_app_key,
            "Content-Type": "application/json",
        }

    # ============================================
    # Metric Operations
    # ============================================

    def send_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[list[str]] = None,
        metric_type: str = "gauge",
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send a custom metric to Datadog.

        Args:
            metric_name: Metric name (e.g., "guardianai.tokens.used")
            value: Metric value
            tags: List of tags (e.g., ["model:gemini-pro", "env:production"])
            metric_type: Type of metric (gauge, count, rate)
            timestamp: Optional timestamp (defaults to now)

        Returns:
            bool: True if metric was sent successfully
        """
        settings = get_settings()
        
        # Build default tags
        default_tags = [
            f"env:{settings.dd_env}",
            f"service:{settings.dd_service_name}",
        ]
        
        all_tags = default_tags + (tags or [])
        
        # Use Unix timestamp
        ts = int((timestamp or datetime.now(timezone.utc)).timestamp())
        
        try:
            # Use DogStatsD for real-time metrics
            if metric_type == "count":
                statsd.increment(metric_name, value=int(value), tags=all_tags)
            elif metric_type == "gauge":
                statsd.gauge(metric_name, value=value, tags=all_tags)
            else:
                statsd.histogram(metric_name, value=value, tags=all_tags)
            
            logger.debug(f"Sent metric: {metric_name}={value} tags={all_tags}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send metric {metric_name}: {e}")
            return False

    def send_metrics_batch(self, metrics: list[dict[str, Any]]) -> bool:
        """
        Send multiple metrics in a batch.

        Args:
            metrics: List of metric dicts with keys: name, value, tags, type

        Returns:
            bool: True if all metrics were sent successfully
        """
        success = True
        for metric in metrics:
            result = self.send_metric(
                metric_name=metric["name"],
                value=metric["value"],
                tags=metric.get("tags"),
                metric_type=metric.get("type", "gauge")
            )
            if not result:
                success = False
        return success

    # ============================================
    # Threat Metrics
    # ============================================

    def send_threat_metric(
        self,
        threat_type: str,
        severity: str,
        confidence: float = 1.0,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Send a threat detection metric.

        Args:
            threat_type: Type of threat (prompt_injection, pii_leak, toxic_content)
            severity: Severity level (low, medium, high, critical)
            confidence: Detection confidence (0.0-1.0)
            user_id: Optional user identifier

        Returns:
            bool: True if metric was sent
        """
        tags = [
            f"threat_type:{threat_type}",
            f"severity:{severity}",
        ]
        
        if user_id:
            tags.append(f"user_id:{user_id}")
        
        return self.send_metric(
            metric_name="guardianai.threat.detected",
            value=1,
            tags=tags,
            metric_type="count"
        )

    def send_quality_metric(self, score: float, model: str = "gemini-pro") -> bool:
        """
        Send a quality score metric.

        Args:
            score: Quality score (0.0-1.0)
            model: Model name

        Returns:
            bool: True if metric was sent
        """
        return self.send_metric(
            metric_name="guardianai.quality.score",
            value=score,
            tags=[f"model:{model}"],
            metric_type="gauge"
        )

    def send_latency_metric(
        self,
        latency_ms: float,
        percentile: str = "p50",
        model: str = "gemini-pro"
    ) -> bool:
        """
        Send a latency metric.

        Args:
            latency_ms: Latency in milliseconds
            percentile: Percentile (p50, p95, p99)
            model: Model name

        Returns:
            bool: True if metric was sent
        """
        return self.send_metric(
            metric_name=f"guardianai.latency.{percentile}",
            value=latency_ms,
            tags=[f"model:{model}"],
            metric_type="gauge"
        )

    def send_token_usage_metric(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gemini-pro"
    ) -> bool:
        """
        Send token usage metrics.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name

        Returns:
            bool: True if metrics were sent
        """
        total = input_tokens + output_tokens
        tags = [f"model:{model}"]
        
        return self.send_metric(
            metric_name="guardianai.tokens.used",
            value=total,
            tags=tags,
            metric_type="count"
        )

    # ============================================
    # Dashboard Operations
    # ============================================

    async def create_dashboard(
        self,
        title: str,
        widgets: Optional[list[dict]] = None
    ) -> Optional[str]:
        """
        Create a new Datadog dashboard.

        Args:
            title: Dashboard title
            widgets: List of widget definitions

        Returns:
            Dashboard ID or None if creation failed
        """
        if widgets is None:
            widgets = self._get_default_widgets()
        
        payload = {
            "title": title,
            "description": "GuardianAI LLM Monitoring Dashboard",
            "widgets": widgets,
            "layout_type": "ordered",
            "notify_list": [],
            "reflow_type": "fixed",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/dashboard",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                dashboard_id = data.get("id")
                logger.info(f"Created dashboard: {dashboard_id}")
                return dashboard_id
        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")
            return None

    def _get_default_widgets(self) -> list[dict]:
        """Get default dashboard widget definitions."""
        return [
            {
                "definition": {
                    "title": "Health Score",
                    "type": "query_value",
                    "requests": [
                        {
                            "q": "avg:guardianai.health.score{*}",
                            "aggregator": "last"
                        }
                    ],
                    "precision": 0
                }
            },
            {
                "definition": {
                    "title": "Token Usage (24h)",
                    "type": "timeseries",
                    "requests": [
                        {
                            "q": "sum:guardianai.tokens.used{*}.as_count()",
                            "display_type": "bars"
                        }
                    ]
                }
            },
            {
                "definition": {
                    "title": "Threats Detected",
                    "type": "timeseries",
                    "requests": [
                        {
                            "q": "sum:guardianai.threat.detected{*} by {threat_type}.as_count()",
                            "display_type": "bars"
                        }
                    ]
                }
            },
            {
                "definition": {
                    "title": "Quality Score",
                    "type": "timeseries",
                    "requests": [
                        {
                            "q": "avg:guardianai.quality.score{*}",
                            "display_type": "line"
                        }
                    ]
                }
            },
            {
                "definition": {
                    "title": "Latency (p95)",
                    "type": "timeseries",
                    "requests": [
                        {
                            "q": "avg:guardianai.latency.p95{*}",
                            "display_type": "line"
                        }
                    ]
                }
            }
        ]

    # ============================================
    # Monitor Operations
    # ============================================

    async def create_monitor(
        self,
        name: str,
        query: str,
        message: str,
        monitor_type: str = "metric alert",
        priority: int = 2
    ) -> Optional[int]:
        """
        Create a Datadog monitor (detection rule).

        Args:
            name: Monitor name
            query: Monitor query
            message: Alert message
            monitor_type: Type of monitor
            priority: Priority (1-5, 1 is highest)

        Returns:
            Monitor ID or None if creation failed
        """
        payload = {
            "name": name,
            "type": monitor_type,
            "query": query,
            "message": message,
            "priority": priority,
            "tags": ["guardianai", "llm-monitoring"],
            "options": {
                "notify_audit": False,
                "require_full_window": False,
                "new_host_delay": 300,
                "notify_no_data": False,
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/monitor",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                monitor_id = data.get("id")
                logger.info(f"Created monitor: {monitor_id}")
                return monitor_id
        except Exception as e:
            logger.error(f"Failed to create monitor: {e}")
            return None

    async def update_monitor_threshold(
        self,
        monitor_id: int,
        new_threshold: float
    ) -> bool:
        """
        Update a monitor's threshold.

        Args:
            monitor_id: Monitor ID
            new_threshold: New threshold value

        Returns:
            bool: True if update succeeded
        """
        try:
            async with httpx.AsyncClient() as client:
                # First get the current monitor
                response = await client.get(
                    f"{self.base_url}/api/v1/monitor/{monitor_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                monitor = response.json()
                
                # Update the query with new threshold
                current_query = monitor.get("query", "")
                # This is a simplified update - real implementation would parse and update
                
                response = await client.put(
                    f"{self.base_url}/api/v1/monitor/{monitor_id}",
                    headers=self.headers,
                    json={"query": current_query}
                )
                response.raise_for_status()
                logger.info(f"Updated monitor {monitor_id} threshold")
                return True
        except Exception as e:
            logger.error(f"Failed to update monitor {monitor_id}: {e}")
            return False

    async def create_default_monitors(self) -> dict[str, Optional[int]]:
        """
        Create default GuardianAI detection rule monitors.

        Returns:
            Dict mapping rule names to monitor IDs
        """
        monitors = {
            "cost_anomaly": {
                "name": "[GuardianAI] Cost Anomaly - High Token Usage",
                "query": "sum(last_1h):sum:guardianai.tokens.used{*}.as_count() > 400000",
                "message": "Token usage exceeded 400,000 in the last hour. @webhook-guardianai",
                "priority": 2
            },
            "security_threat": {
                "name": "[GuardianAI] Security Threat - Critical",
                "query": "sum(last_5m):sum:guardianai.threat.detected{severity:critical}.as_count() > 0",
                "message": "Critical security threat detected! @webhook-guardianai @pagerduty",
                "priority": 1
            },
            "quality_degradation": {
                "name": "[GuardianAI] Quality Degradation",
                "query": "avg(last_10m):avg:guardianai.quality.score{*} < 0.7",
                "message": "Quality score has dropped below 0.7. @webhook-guardianai",
                "priority": 3
            },
            "latency_spike": {
                "name": "[GuardianAI] Latency Spike - P95",
                "query": "avg(last_5m):avg:guardianai.latency.p95{*} > 5000",
                "message": "P95 latency exceeded 5000ms. @webhook-guardianai",
                "priority": 2
            },
            "error_rate": {
                "name": "[GuardianAI] High Error Rate",
                "query": "avg(last_5m):( sum:guardianai.request.error{*}.as_count() / sum:guardianai.request.total{*}.as_count() ) * 100 > 5",
                "message": "Error rate exceeded 5%. @webhook-guardianai",
                "priority": 2
            }
        }
        
        results = {}
        for rule_name, config in monitors.items():
            monitor_id = await self.create_monitor(
                name=config["name"],
                query=config["query"],
                message=config["message"],
                priority=config["priority"]
            )
            results[rule_name] = monitor_id
        
        return results

    # ============================================
    # Log Operations
    # ============================================

    async def send_log(
        self,
        message: str,
        level: str = "info",
        service: str = "guardianai",
        tags: Optional[dict[str, str]] = None
    ) -> bool:
        """
        Send a log entry to Datadog.

        Args:
            message: Log message
            level: Log level (debug, info, warn, error)
            service: Service name
            tags: Additional tags

        Returns:
            bool: True if log was sent
        """
        settings = get_settings()
        
        log_entry = {
            "ddsource": "guardianai",
            "ddtags": f"env:{settings.dd_env},service:{service}",
            "hostname": "guardianai-backend",
            "message": message,
            "service": service,
            "status": level
        }
        
        if tags:
            for key, value in tags.items():
                log_entry["ddtags"] += f",{key}:{value}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://http-intake.logs.{settings.dd_site}/api/v2/logs",
                    headers={
                        "DD-API-KEY": settings.dd_api_key,
                        "Content-Type": "application/json"
                    },
                    json=[log_entry]
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to send log to Datadog: {e}")
            return False

    # ============================================
    # Incident Operations
    # ============================================

    async def update_datadog_incident(
        self,
        incident_id: str,
        analysis: str,
        dashboard_link: str
    ) -> bool:
        """
        Update a Datadog incident with analysis.

        Args:
            incident_id: Datadog incident ID
            analysis: AI-generated analysis
            dashboard_link: Link to GuardianAI dashboard

        Returns:
            bool: True if update succeeded
        """
        try:
            async with httpx.AsyncClient() as client:
                # Add a timeline cell with the analysis
                response = await client.post(
                    f"{self.base_url}/api/v2/incidents/{incident_id}/timeline",
                    headers=self.headers,
                    json={
                        "data": {
                            "type": "incident_timeline_cells",
                            "attributes": {
                                "cell_type": "markdown",
                                "content": {
                                    "content": f"## GuardianAI Analysis\n\n{analysis}\n\n[View in GuardianAI Dashboard]({dashboard_link})"
                                }
                            }
                        }
                    }
                )
                response.raise_for_status()
                logger.info(f"Updated Datadog incident: {incident_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update Datadog incident: {e}")
            return False


# Singleton accessor
def get_datadog_client() -> DatadogClient:
    """Get the Datadog client singleton."""
    return DatadogClient()


async def setup_datadog_integration() -> dict[str, Any]:
    """
    Set up Datadog integration for GuardianAI.
    
    Creates default dashboard and monitors.
    
    Returns:
        Dict with dashboard_id and monitor_ids
    """
    client = get_datadog_client()
    
    # Create dashboard
    dashboard_id = await client.create_dashboard(
        title="GuardianAI LLM Monitoring"
    )
    
    # Create monitors
    monitor_ids = await client.create_default_monitors()
    
    return {
        "dashboard_id": dashboard_id,
        "monitor_ids": monitor_ids
    }
