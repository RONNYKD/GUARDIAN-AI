"""
GuardianAI Processing Pipeline

Cloud Functions for real-time telemetry processing and threat detection.

Components:
- telemetry_processor: Main entry point for Cloud Function
- threat_detector: Threat detection logic
- anomaly_detector: Anomaly detection with baselines
- quality_analyzer: Response quality analysis
- alert_manager: Alert generation and routing
"""

from pipeline.telemetry_processor import process_telemetry
from pipeline.threat_detector import ThreatDetector, detect_threats
from pipeline.anomaly_detector import AnomalyDetector
from pipeline.quality_analyzer import QualityAnalyzer, analyze_quality
from pipeline.alert_manager import AlertManager

__all__ = [
    "process_telemetry",
    "ThreatDetector",
    "detect_threats",
    "AnomalyDetector",
    "QualityAnalyzer",
    "analyze_quality",
    "AlertManager",
]
