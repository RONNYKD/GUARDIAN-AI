"""
GuardianAI Webhooks API

Handles incoming webhooks from:
- Datadog alerts and monitors
- External integrations

Triggers incident creation and auto-remediation.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel, Field

from backend.config import get_settings
from backend.services.firestore_client import get_firestore_client

logger = logging.getLogger(__name__)

router = APIRouter()


class DatadogAlertPayload(BaseModel):
    """Datadog webhook alert payload."""
    alert_id: Optional[str] = None
    alert_title: Optional[str] = None
    alert_type: Optional[str] = None
    alert_query: Optional[str] = None
    alert_status: Optional[str] = None
    alert_transition: Optional[str] = None
    date: Optional[str] = None
    event_type: Optional[str] = None
    hostname: Optional[str] = None
    org: Optional[dict] = None
    priority: Optional[str] = None
    tags: Optional[str] = None
    body: Optional[str] = None
    # Additional fields that may come from Datadog
    id: Optional[str] = None
    title: Optional[str] = None
    last_updated: Optional[str] = None


class WebhookResponse(BaseModel):
    """Webhook processing response."""
    status: str
    message: str
    incident_id: Optional[str] = None


def map_priority_to_severity(priority: Optional[str]) -> str:
    """
    Map Datadog priority to incident severity.
    
    Datadog priorities: P1 (critical) to P5 (low)
    """
    priority_map = {
        "P1": "critical",
        "P2": "high",
        "P3": "medium",
        "P4": "low",
        "P5": "low"
    }
    return priority_map.get(priority or "", "medium")


def extract_threat_type_from_title(title: Optional[str]) -> str:
    """Extract threat type from alert title."""
    if not title:
        return "unknown"
    
    title_lower = title.lower()
    if "cost" in title_lower or "token" in title_lower:
        return "cost_anomaly"
    elif "security" in title_lower or "threat" in title_lower:
        return "security_threat"
    elif "quality" in title_lower:
        return "quality_degradation"
    elif "latency" in title_lower:
        return "latency_spike"
    elif "error" in title_lower:
        return "high_error_rate"
    else:
        return "generic"


@router.post("/datadog/alert", response_model=WebhookResponse)
async def handle_datadog_alert(
    request: Request,
    x_datadog_signature: Optional[str] = Header(default=None)
) -> WebhookResponse:
    """
    Handle incoming Datadog alert webhooks.
    
    Creates incidents and triggers auto-remediation based on alert type.
    
    Expected within 30 seconds of Datadog alert trigger per Requirements 8.1.
    
    Args:
        request: FastAPI request with webhook payload
        x_datadog_signature: Optional signature for verification
    
    Returns:
        WebhookResponse with processing result
    """
    settings = get_settings()
    db = get_firestore_client()
    
    # Parse payload
    try:
        body = await request.body()
        payload_data = json.loads(body)
        payload = DatadogAlertPayload(**payload_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload format")
    
    logger.info(f"Received Datadog alert: {payload.alert_title or payload.title}")
    
    # Determine alert details
    alert_title = payload.alert_title or payload.title or "Unknown Alert"
    alert_id = payload.alert_id or payload.id or "unknown"
    severity = map_priority_to_severity(payload.priority)
    threat_type = extract_threat_type_from_title(alert_title)
    
    # Create incident record (Requirement 8.2)
    now = datetime.now(timezone.utc).isoformat()
    incident_data = {
        "created_at": now,
        "updated_at": now,
        "triggered_at": payload.date or now,
        "status": "open",
        "severity": severity,
        "rule_name": threat_type,
        "title": alert_title,
        "description": payload.body,
        "datadog_alert_id": alert_id,
        "datadog_alert_query": payload.alert_query,
        "tags": payload.tags,
        "remediation_actions": []
    }
    
    incident_id = db.create_incident(incident_data)
    logger.info(f"Created incident: {incident_id}")
    
    # Query recent telemetry for context (Requirement 8.3)
    try:
        recent_telemetry = db.get_recent_telemetry(limit=10)
        
        # Update incident with context
        db.update_incident(incident_id, {
            "context": {
                "recent_telemetry_count": len(recent_telemetry),
                "trace_ids": [t.get("trace_id") for t in recent_telemetry[:10]]
            }
        })
    except Exception as e:
        logger.warning(f"Failed to fetch telemetry context: {e}")
    
    # Trigger auto-remediation based on threat type
    remediation_result = await trigger_auto_remediation(
        incident_id=incident_id,
        threat_type=threat_type,
        severity=severity,
        context=payload_data
    )
    
    return WebhookResponse(
        status="processed",
        message=f"Incident created: {incident_id}. {remediation_result}",
        incident_id=incident_id
    )


async def trigger_auto_remediation(
    incident_id: str,
    threat_type: str,
    severity: str,
    context: dict[str, Any]
) -> str:
    """
    Trigger automatic remediation based on threat type.
    
    Implements Requirements 9.1-9.5 for auto-remediation.
    """
    db = get_firestore_client()
    settings = get_settings()
    
    remediation_message = "No auto-remediation triggered."
    
    if threat_type == "cost_anomaly":
        # Requirement 9.1: Apply rate limiting
        # Try to extract user_id from context
        user_id = context.get("user_id") or "unknown_user"
        
        db.set_rate_limit(
            user_id=user_id,
            limit=10,
            window_seconds=60,
            reason=f"Cost anomaly incident {incident_id}"
        )
        
        remediation_message = f"Rate limit applied to user {user_id}: 10 req/min"
        
        # Record remediation action
        db.update_incident(incident_id, {
            "remediation_actions": [{
                "action_type": "rate_limit",
                "target": user_id,
                "parameters": {"limit": 10, "window_seconds": 60},
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "result": remediation_message
            }]
        })
    
    elif threat_type == "security_threat" and severity == "critical":
        # For critical security threats, log recommendation
        remediation_message = "Critical security threat - manual review required"
        
        db.update_incident(incident_id, {
            "requires_manual_review": True,
            "recommended_actions": [
                "Review affected request traces",
                "Verify PII redaction complete",
                "Consider temporary user suspension"
            ]
        })
    
    elif threat_type == "quality_degradation":
        # Requirement 9.5: Log recommendation to switch model
        remediation_message = "Quality degradation detected - backup model recommended"
        
        db.update_incident(incident_id, {
            "recommended_actions": [
                "Switch to backup model configuration",
                "Review recent prompt patterns",
                "Check Gemini API status"
            ]
        })
    
    logger.info(f"Auto-remediation for {incident_id}: {remediation_message}")
    return remediation_message


@router.post("/test", response_model=WebhookResponse)
async def test_webhook() -> WebhookResponse:
    """
    Test endpoint to verify webhook connectivity.
    
    Returns:
        Simple success response
    """
    return WebhookResponse(
        status="ok",
        message="Webhook endpoint is operational"
    )
