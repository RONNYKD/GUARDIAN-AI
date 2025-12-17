"""
GuardianAI Telemetry Processor

Main Cloud Function entry point for processing telemetry.
Orchestrates threat detection, anomaly detection, and alerting.
"""

import json
import logging
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from pipeline.threat_detector import ThreatDetector, DetectedThreat
from pipeline.anomaly_detector import AnomalyDetector, DetectedAnomaly
from pipeline.quality_analyzer import QualityAnalyzer, QualityAnalysis
from pipeline.alert_manager import AlertManager

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of telemetry processing."""
    trace_id: str
    threats: list[dict[str, Any]]
    anomalies: list[dict[str, Any]]
    quality_analysis: Optional[dict[str, Any]]
    alerts_generated: int
    processing_time_ms: float
    timestamp: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "threats": self.threats,
            "anomalies": self.anomalies,
            "quality_analysis": self.quality_analysis,
            "alerts_generated": self.alerts_generated,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp,
        }


class TelemetryProcessor:
    """
    Main processor for LLM telemetry.
    
    Orchestrates:
    - Threat detection
    - Anomaly detection
    - Quality analysis
    - Alert generation
    
    Example:
        >>> processor = TelemetryProcessor()
        >>> result = await processor.process(telemetry_record)
    """
    
    def __init__(
        self,
        datadog_api_key: Optional[str] = None,
        datadog_app_key: Optional[str] = None,
        quality_threshold: float = 0.7,
        enable_alerts: bool = True,
    ) -> None:
        """
        Initialize processor.
        
        Args:
            datadog_api_key: Datadog API key for alerting
            datadog_app_key: Datadog App key
            quality_threshold: Minimum quality score
            enable_alerts: Whether to generate alerts
        """
        self.threat_detector = ThreatDetector()
        self.anomaly_detector = AnomalyDetector()
        self.quality_analyzer = QualityAnalyzer(quality_threshold=quality_threshold)
        self.alert_manager = AlertManager(
            datadog_api_key=datadog_api_key,
            datadog_app_key=datadog_app_key,
        )
        self.enable_alerts = enable_alerts
    
    async def process(self, telemetry: dict[str, Any]) -> ProcessingResult:
        """
        Process a telemetry record.
        
        Args:
            telemetry: Telemetry record dictionary
        
        Returns:
            ProcessingResult with analysis
        """
        import time
        start_time = time.perf_counter()
        
        trace_id = telemetry.get("trace_id", "unknown")
        prompt = telemetry.get("prompt", "")
        response = telemetry.get("response_text", "")
        user_id = telemetry.get("user_id")
        
        threats = []
        anomalies = []
        quality_result = None
        alerts_generated = 0
        
        # 1. Threat Detection
        detected_threats = self.threat_detector.analyze(
            prompt=prompt,
            response=response,
            trace_id=trace_id,
            user_id=user_id,
        )
        threats = [t.to_dict() for t in detected_threats]
        
        # Generate alerts for threats
        if self.enable_alerts and detected_threats:
            for threat in detected_threats:
                alert = self.alert_manager.create_threat_alert(
                    threat_type=threat.threat_type.value,
                    severity=threat.severity.value,
                    description=threat.description,
                    evidence=threat.evidence,
                    trace_id=trace_id,
                    user_id=user_id,
                )
                await self.alert_manager.send_to_datadog(alert)
                alerts_generated += 1
        
        # 2. Anomaly Detection
        # Update baselines and check for anomalies
        latency_ms = telemetry.get("latency_ms", 0)
        input_tokens = telemetry.get("input_tokens", 0)
        output_tokens = telemetry.get("output_tokens", 0)
        cost_usd = telemetry.get("cost_usd", 0)
        
        # Add samples to rolling windows
        self.anomaly_detector.add_sample("latency_ms", latency_ms)
        self.anomaly_detector.add_sample("input_tokens", input_tokens)
        self.anomaly_detector.add_sample("output_tokens", output_tokens)
        self.anomaly_detector.add_sample("cost_usd", cost_usd)
        
        # Check for anomalies
        latency_anomalies = self.anomaly_detector.check_value(
            "latency_ms", latency_ms, trace_id
        )
        token_anomalies = self.anomaly_detector.check_value(
            "input_tokens", input_tokens, trace_id
        )
        cost_anomalies = self.anomaly_detector.check_value(
            "cost_usd", cost_usd, trace_id
        )
        
        all_anomalies = latency_anomalies + token_anomalies + cost_anomalies
        anomalies = [a.to_dict() for a in all_anomalies]
        
        # Generate alerts for critical anomalies
        if self.enable_alerts:
            for anomaly in all_anomalies:
                if anomaly.severity in ("critical", "high"):
                    alert = self.alert_manager.create_anomaly_alert(
                        anomaly_type=anomaly.anomaly_type.value,
                        severity=anomaly.severity,
                        current_value=anomaly.current_value,
                        expected_value=anomaly.expected_value,
                        description=anomaly.description,
                        trace_id=trace_id,
                    )
                    await self.alert_manager.send_to_datadog(alert)
                    alerts_generated += 1
        
        # 3. Quality Analysis
        if response:
            quality = self.quality_analyzer.analyze(
                prompt=prompt,
                response=response,
                trace_id=trace_id,
            )
            quality_result = quality.to_dict()
            
            # Update quality baseline
            self.anomaly_detector.add_sample(
                "quality_score",
                quality.metrics.overall_score
            )
            
            # Alert on quality degradation
            if self.enable_alerts and not quality.passed:
                alert = self.alert_manager.create_quality_alert(
                    quality_score=quality.metrics.overall_score,
                    threshold=quality.threshold,
                    issues=quality.issues,
                    trace_id=trace_id,
                )
                await self.alert_manager.send_to_datadog(alert)
                alerts_generated += 1
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return ProcessingResult(
            trace_id=trace_id,
            threats=threats,
            anomalies=anomalies,
            quality_analysis=quality_result,
            alerts_generated=alerts_generated,
            processing_time_ms=processing_time,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    def process_sync(self, telemetry: dict[str, Any]) -> ProcessingResult:
        """Synchronous wrapper for process."""
        return asyncio.run(self.process(telemetry))


# Global processor instance for Cloud Function
_processor: Optional[TelemetryProcessor] = None


def get_processor() -> TelemetryProcessor:
    """Get or create global processor instance."""
    global _processor
    if _processor is None:
        import os
        _processor = TelemetryProcessor(
            datadog_api_key=os.environ.get("DD_API_KEY"),
            datadog_app_key=os.environ.get("DD_APP_KEY"),
            quality_threshold=float(os.environ.get("QUALITY_THRESHOLD", "0.7")),
            enable_alerts=os.environ.get("ENABLE_ALERTS", "true").lower() == "true",
        )
    return _processor


def process_telemetry(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """
    Cloud Function entry point.
    
    Triggered by Pub/Sub messages containing telemetry data.
    
    Args:
        event: Cloud Function event (Pub/Sub message)
        context: Cloud Function context
    
    Returns:
        Processing result dictionary
    """
    import base64
    
    try:
        # Parse Pub/Sub message
        if "data" in event:
            data = base64.b64decode(event["data"]).decode("utf-8")
            telemetry = json.loads(data)
        else:
            telemetry = event
        
        processor = get_processor()
        result = processor.process_sync(telemetry)
        
        logger.info(
            f"Processed telemetry {result.trace_id}: "
            f"{len(result.threats)} threats, "
            f"{len(result.anomalies)} anomalies, "
            f"{result.alerts_generated} alerts"
        )
        
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"Error processing telemetry: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def process_http(request) -> tuple[dict[str, Any], int]:
    """
    HTTP endpoint for direct telemetry processing.
    
    Alternative to Pub/Sub for synchronous processing.
    
    Args:
        request: Flask request object
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    try:
        telemetry = request.get_json(force=True)
        
        processor = get_processor()
        result = processor.process_sync(telemetry)
        
        return result.to_dict(), 200
        
    except Exception as e:
        logger.error(f"Error processing HTTP request: {e}")
        return {"error": str(e)}, 500
