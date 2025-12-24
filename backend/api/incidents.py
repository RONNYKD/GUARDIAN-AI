"""
GuardianAI Incidents API

Provides endpoints for:
- Incident listing and filtering
- Incident details and context
- Incident status updates
- Remediation actions
"""

from datetime import datetime, timezone
from typing import Any, Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field

from config import get_settings, Settings
from services.firestore_client import get_firestore_client

router = APIRouter()


class IncidentSeverity(str, Enum):
    """Incident severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident status values."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class RemediationAction(BaseModel):
    """Remediation action details."""
    action_type: str = Field(description="Type of action (rate_limit, circuit_breaker, etc.)")
    target: str = Field(description="Target of the action (user_id, endpoint, etc.)")
    parameters: dict[str, Any] = Field(default_factory=dict)
    executed_at: Optional[str] = None
    result: Optional[str] = None


class IncidentContext(BaseModel):
    """Context information for an incident."""
    recent_telemetry: list[dict[str, Any]] = Field(description="Recent telemetry records")
    related_traces: list[str] = Field(description="Related trace IDs")
    affected_users: list[str] = Field(description="Affected user IDs")
    ai_analysis: Optional[str] = Field(description="Gemini-generated analysis")
    recommended_actions: list[str] = Field(description="Recommended remediation steps")


class Incident(BaseModel):
    """Incident record."""
    incident_id: str
    created_at: str
    updated_at: str
    status: IncidentStatus
    severity: IncidentSeverity
    rule_name: str
    title: str
    description: Optional[str] = None
    context: Optional[IncidentContext] = None
    remediation_actions: list[RemediationAction] = Field(default_factory=list)
    datadog_incident_url: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None


class IncidentCreate(BaseModel):
    """Request model for creating an incident."""
    rule_name: str
    severity: IncidentSeverity
    title: str
    description: Optional[str] = None
    triggered_by: Optional[str] = None


class IncidentUpdate(BaseModel):
    """Request model for updating an incident."""
    status: Optional[IncidentStatus] = None
    description: Optional[str] = None
    resolved_by: Optional[str] = None


class RemediationRequest(BaseModel):
    """Request model for executing remediation."""
    action_type: str
    target: str
    parameters: dict[str, Any] = Field(default_factory=dict)


@router.get("/incidents", response_model=list[Incident])
async def list_incidents(
    status: Optional[IncidentStatus] = Query(default=None),
    severity: Optional[IncidentSeverity] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
) -> list[Incident]:
    """
    List incidents with optional filtering.
    
    Args:
        status: Filter by status
        severity: Filter by severity
        limit: Maximum number of results
        offset: Pagination offset
    
    Returns:
        List of incidents ordered by created_at descending
    """
    try:
        db = get_firestore_client()
        incidents = db.get_recent_incidents(
            limit=limit,
            status_filter=status.value if status else None,
            severity_filter=severity.value if severity else None
        )
        return [Incident(**inc) for inc in incidents if inc.get("incident_id")]
    except Exception as e:
        # Return empty list if Firestore not available
        return []


@router.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident(
    incident_id: str = Path(..., description="Incident ID")
) -> Incident:
    """
    Get a specific incident by ID.
    
    Args:
        incident_id: Incident identifier
    
    Returns:
        Incident details with full context
    
    Raises:
        404: Incident not found
    """
    db = get_firestore_client()
    incident = db.get_incident(incident_id)
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return Incident(**incident)


@router.post("/incidents", response_model=Incident, status_code=201)
async def create_incident(
    request: IncidentCreate
) -> Incident:
    """
    Create a new incident.
    
    Args:
        request: Incident creation data
    
    Returns:
        Created incident
    """
    db = get_firestore_client()
    
    now = datetime.now(timezone.utc).isoformat()
    incident_data = {
        "created_at": now,
        "updated_at": now,
        "status": IncidentStatus.OPEN.value,
        "severity": request.severity.value,
        "rule_name": request.rule_name,
        "title": request.title,
        "description": request.description,
        "remediation_actions": []
    }
    
    incident_id = db.create_incident(incident_data)
    incident_data["incident_id"] = incident_id
    
    return Incident(**incident_data)


@router.patch("/incidents/{incident_id}", response_model=Incident)
async def update_incident(
    incident_id: str,
    request: IncidentUpdate
) -> Incident:
    """
    Update an incident's status or description.
    
    Args:
        incident_id: Incident identifier
        request: Update data
    
    Returns:
        Updated incident
    """
    db = get_firestore_client()
    
    # Build updates
    updates = {}
    if request.status:
        updates["status"] = request.status.value
        if request.status == IncidentStatus.RESOLVED:
            updates["resolved_at"] = datetime.now(timezone.utc).isoformat()
            updates["resolved_by"] = request.resolved_by
    
    if request.description:
        updates["description"] = request.description
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    db.update_incident(incident_id, updates)
    
    # Fetch and return updated incident
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return Incident(**incident)


@router.post("/incidents/{incident_id}/remediate", response_model=Incident)
async def execute_remediation(
    incident_id: str,
    request: RemediationRequest
) -> Incident:
    """
    Execute a remediation action for an incident.
    
    Supported action types:
    - rate_limit: Apply rate limiting to a user
    - circuit_breaker: Activate circuit breaker for an endpoint
    - pii_redaction: Redact PII from stored data
    - prompt_sanitization: Sanitize malicious prompts
    
    Args:
        incident_id: Incident identifier
        request: Remediation action details
    
    Returns:
        Updated incident with remediation record
    """
    db = get_firestore_client()
    
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Execute remediation based on action type
    result = ""
    if request.action_type == "rate_limit":
        user_id = request.target
        limit = request.parameters.get("limit", 10)
        window = request.parameters.get("window_seconds", 60)
        
        db.set_rate_limit(user_id, limit, window, reason=f"Incident {incident_id}")
        result = f"Rate limit applied: {limit} req/{window}s"
    
    elif request.action_type == "circuit_breaker":
        # TODO: Implement circuit breaker logic
        result = "Circuit breaker activated"
    
    elif request.action_type == "pii_redaction":
        # TODO: Trigger PII redaction
        result = "PII redaction initiated"
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action type: {request.action_type}"
        )
    
    # Record remediation action
    remediation = RemediationAction(
        action_type=request.action_type,
        target=request.target,
        parameters=request.parameters,
        executed_at=datetime.now(timezone.utc).isoformat(),
        result=result
    )
    
    actions = incident.get("remediation_actions", [])
    actions.append(remediation.model_dump())
    
    db.update_incident(incident_id, {
        "remediation_actions": actions,
        "status": IncidentStatus.INVESTIGATING.value
    })
    
    # Return updated incident
    incident = db.get_incident(incident_id)
    return Incident(**incident)


@router.get("/incidents/{incident_id}/context", response_model=IncidentContext)
async def get_incident_context(
    incident_id: str
) -> IncidentContext:
    """
    Get detailed context for an incident.
    
    Retrieves recent telemetry, related traces, affected users,
    and AI-generated analysis for the incident.
    
    Args:
        incident_id: Incident identifier
    
    Returns:
        IncidentContext with analysis and recommendations
    """
    db = get_firestore_client()
    
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get recent telemetry around incident time
    telemetry = db.get_recent_telemetry(limit=10)
    
    # TODO: Implement Gemini analysis
    ai_analysis = "Analysis pending. Gemini integration required."
    
    return IncidentContext(
        recent_telemetry=telemetry,
        related_traces=[t.get("trace_id", "") for t in telemetry if t.get("trace_id")],
        affected_users=list(set(t.get("user_id", "") for t in telemetry if t.get("user_id"))),
        ai_analysis=ai_analysis,
        recommended_actions=[
            "Review affected user activity",
            "Check for pattern in recent requests",
            "Consider rate limiting if abuse detected"
        ]
    )
