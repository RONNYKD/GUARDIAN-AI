"""
GuardianAI Demo Mode API Endpoints

Provides demo functionality for showcasing the system without real LLM costs:
- Launch individual attack scenarios
- Run preset multi-step demonstrations
- Track scenario progress
- Get real-time metrics
- Reset demo data
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timezone
import asyncio
import uuid
from enum import Enum

# Import demo data generator
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from services.demo_data_generator import DemoDataGenerator
from config import get_settings
from services.firestore_client import get_firestore_client


router = APIRouter(tags=["demo"])

# Global state for tracking running scenarios
_running_scenarios: Dict[str, Dict[str, Any]] = {}
_demo_generator = DemoDataGenerator()


class AttackType(str, Enum):
    """Available attack types for demo."""
    NORMAL = "normal"
    PROMPT_INJECTION = "prompt_injection"
    PII_LEAK = "pii_leak"
    JAILBREAK = "jailbreak"
    TOXIC_CONTENT = "toxic_content"
    COST_SPIKE = "cost_spike"
    QUALITY_DEGRADATION = "quality_degradation"
    LATENCY_SPIKE = "latency_spike"
    ERROR_BURST = "error_burst"


class ScenarioType(str, Enum):
    """Preset scenario types."""
    SECURITY_BREACH = "security_breach"
    COST_CRISIS = "cost_crisis"
    QUALITY_DECLINE = "quality_decline"
    SYSTEM_STRESS = "system_stress"
    COMPREHENSIVE = "comprehensive"


class LaunchAttackRequest(BaseModel):
    """Request to launch a single attack."""
    attack_type: AttackType
    count: int = Field(default=1, ge=1, le=100, description="Number of requests to generate")


class LaunchAttackResponse(BaseModel):
    """Response from launching an attack."""
    success: bool
    attack_type: str
    records_generated: int
    message: str
    trace_ids: List[str]


class RunScenarioRequest(BaseModel):
    """Request to run a preset scenario."""
    scenario_type: ScenarioType
    speed: Literal["fast", "normal", "slow"] = Field(default="normal", description="Execution speed")


class RunScenarioResponse(BaseModel):
    """Response from starting a scenario."""
    success: bool
    scenario_id: str
    scenario_type: str
    estimated_duration_seconds: int
    message: str


class ScenarioStatus(BaseModel):
    """Status of a running scenario."""
    scenario_id: str
    scenario_type: str
    status: Literal["running", "completed", "failed"]
    progress_percent: int
    current_step: str
    steps_completed: int
    total_steps: int
    records_generated: int
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class DemoStats(BaseModel):
    """Real-time demo statistics."""
    total_requests: int
    threat_count: int
    threat_breakdown: Dict[str, int]
    avg_quality_score: float
    total_cost_usd: float
    avg_latency_ms: int
    error_count: int
    error_rate_percent: float
    last_updated: str


class ResetResponse(BaseModel):
    """Response from reset operation."""
    success: bool
    records_deleted: int
    message: str


@router.post("/launch-attack", response_model=LaunchAttackResponse)
async def launch_attack(request: LaunchAttackRequest):
    """
    Launch a single attack scenario.
    
    Generates synthetic telemetry for the specified attack type and stores
    it in Firestore. Data is tagged with demo_mode=true for easy cleanup.
    """
    try:
        records = []
        trace_ids = []
        
        # Generate records based on attack type
        if request.attack_type == AttackType.NORMAL:
            for _ in range(request.count):
                record = _demo_generator.generate_normal_request()
                records.append(record)
                trace_ids.append(record["trace_id"])
        
        elif request.attack_type == AttackType.PROMPT_INJECTION:
            for _ in range(request.count):
                record = _demo_generator.generate_prompt_injection_attack()
                records.append(record)
                trace_ids.append(record["trace_id"])
        
        elif request.attack_type == AttackType.PII_LEAK:
            for _ in range(request.count):
                record = _demo_generator.generate_pii_leak()
                records.append(record)
                trace_ids.append(record["trace_id"])
        
        elif request.attack_type == AttackType.JAILBREAK:
            for _ in range(request.count):
                record = _demo_generator.generate_jailbreak_attempt()
                records.append(record)
                trace_ids.append(record["trace_id"])
        
        elif request.attack_type == AttackType.TOXIC_CONTENT:
            for _ in range(request.count):
                record = _demo_generator.generate_toxic_content()
                records.append(record)
                trace_ids.append(record["trace_id"])
        
        elif request.attack_type == AttackType.COST_SPIKE:
            records = _demo_generator.generate_cost_spike(count=request.count)
            trace_ids = [r["trace_id"] for r in records]
        
        elif request.attack_type == AttackType.QUALITY_DEGRADATION:
            records = _demo_generator.generate_quality_degradation(count=request.count)
            trace_ids = [r["trace_id"] for r in records]
        
        elif request.attack_type == AttackType.LATENCY_SPIKE:
            for _ in range(request.count):
                record = _demo_generator.generate_latency_spike()
                records.append(record)
                trace_ids.append(record["trace_id"])
        
        elif request.attack_type == AttackType.ERROR_BURST:
            records = _demo_generator.generate_error_burst(total=request.count)
            trace_ids = [r["trace_id"] for r in records]
        
        # Store in Firestore
        await _store_demo_records(records)
        
        return LaunchAttackResponse(
            success=True,
            attack_type=request.attack_type.value,
            records_generated=len(records),
            message=f"Successfully generated {len(records)} {request.attack_type.value} records",
            trace_ids=trace_ids
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch attack: {str(e)}")


@router.post("/run-scenario", response_model=RunScenarioResponse)
async def run_scenario(request: RunScenarioRequest, background_tasks: BackgroundTasks):
    """
    Run a preset multi-step demonstration scenario.
    
    Scenarios run in background and can be tracked via /status endpoint.
    """
    scenario_id = str(uuid.uuid4())
    
    # Define scenario steps
    scenarios = {
        ScenarioType.SECURITY_BREACH: {
            "steps": [
                ("normal", 5),
                ("prompt_injection", 3),
                ("jailbreak", 2),
                ("pii_leak", 2),
                ("toxic_content", 2)
            ],
            "description": "Simulates a security breach with multiple attack vectors"
        },
        ScenarioType.COST_CRISIS: {
            "steps": [
                ("normal", 10),
                ("cost_spike", 50)
            ],
            "description": "Simulates sudden cost spike from token usage"
        },
        ScenarioType.QUALITY_DECLINE: {
            "steps": [
                ("normal", 5),
                ("quality_degradation", 15)
            ],
            "description": "Simulates gradual quality degradation"
        },
        ScenarioType.SYSTEM_STRESS: {
            "steps": [
                ("latency_spike", 10),
                ("error_burst", 20),
                ("normal", 5)
            ],
            "description": "Simulates system under stress with latency and errors"
        },
        ScenarioType.COMPREHENSIVE: {
            "steps": [
                ("normal", 10),
                ("prompt_injection", 3),
                ("pii_leak", 2),
                ("cost_spike", 20),
                ("quality_degradation", 10),
                ("latency_spike", 5),
                ("error_burst", 15)
            ],
            "description": "Comprehensive demo of all attack types"
        }
    }
    
    scenario_config = scenarios[request.scenario_type]
    total_steps = len(scenario_config["steps"])
    
    # Calculate estimated duration based on speed
    speed_multipliers = {"fast": 0.5, "normal": 1.0, "slow": 2.0}
    base_duration = sum(count for _, count in scenario_config["steps"]) * 2  # 2 seconds per record
    estimated_duration = int(base_duration * speed_multipliers[request.speed])
    
    # Initialize scenario tracking
    _running_scenarios[scenario_id] = {
        "scenario_type": request.scenario_type.value,
        "status": "running",
        "progress_percent": 0,
        "current_step": scenario_config["steps"][0][0],
        "steps_completed": 0,
        "total_steps": total_steps,
        "records_generated": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "error": None,
        "speed": request.speed
    }
    
    # Run scenario in background
    background_tasks.add_task(
        _execute_scenario,
        scenario_id,
        scenario_config["steps"],
        request.speed
    )
    
    return RunScenarioResponse(
        success=True,
        scenario_id=scenario_id,
        scenario_type=request.scenario_type.value,
        estimated_duration_seconds=estimated_duration,
        message=f"Scenario '{request.scenario_type.value}' started: {scenario_config['description']}"
    )


@router.get("/status/{scenario_id}", response_model=ScenarioStatus)
async def get_scenario_status(scenario_id: str):
    """
    Get the status of a running scenario.
    
    Poll this endpoint to track scenario progress.
    """
    if scenario_id not in _running_scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    
    scenario = _running_scenarios[scenario_id]
    
    return ScenarioStatus(
        scenario_id=scenario_id,
        scenario_type=scenario["scenario_type"],
        status=scenario["status"],
        progress_percent=scenario["progress_percent"],
        current_step=scenario["current_step"],
        steps_completed=scenario["steps_completed"],
        total_steps=scenario["total_steps"],
        records_generated=scenario["records_generated"],
        started_at=scenario["started_at"],
        completed_at=scenario["completed_at"],
        error=scenario["error"]
    )


@router.get("/stats", response_model=DemoStats)
async def get_demo_stats():
    """
    Get real-time statistics for demo mode data.
    
    Returns aggregated metrics from all demo telemetry records.
    """
    try:
        # Query Firestore for demo records
        stats = await _calculate_demo_stats()
        
        return DemoStats(
            total_requests=stats["total_requests"],
            threat_count=stats["threat_count"],
            threat_breakdown=stats["threat_breakdown"],
            avg_quality_score=stats["avg_quality_score"],
            total_cost_usd=stats["total_cost_usd"],
            avg_latency_ms=stats["avg_latency_ms"],
            error_count=stats["error_count"],
            error_rate_percent=stats["error_rate_percent"],
            last_updated=datetime.now(timezone.utc).isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/reset", response_model=ResetResponse)
async def reset_demo_data():
    """
    Clear all demo mode data from Firestore.
    
    Deletes all records where metadata.demo_mode = true.
    """
    try:
        deleted_count = await _delete_demo_records()
        
        # Clear running scenarios
        _running_scenarios.clear()
        
        return ResetResponse(
            success=True,
            records_deleted=deleted_count,
            message=f"Successfully deleted {deleted_count} demo records"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset demo data: {str(e)}")


# Helper functions

async def _store_demo_records(records: List[Dict[str, Any]]):
    """Store demo records in Firestore."""
    try:
        settings = get_settings()
        db = get_firestore_client()
        
        # Store each record in telemetry collection
        for record in records:
            doc_ref = db.collection(settings.firestore_collection_telemetry).document(record["trace_id"])
            doc_ref.set(record)
    
    except Exception as e:
        print(f"Error storing demo records: {e}")
        raise


async def _execute_scenario(scenario_id: str, steps: List[tuple], speed: str):
    """Execute a scenario in the background."""
    try:
        speed_delays = {"fast": 0.5, "normal": 1.0, "slow": 2.0}
        delay = speed_delays[speed]
        
        total_steps = len(steps)
        total_records = 0
        
        for step_index, (attack_type, count) in enumerate(steps):
            # Update current step
            _running_scenarios[scenario_id]["current_step"] = attack_type
            _running_scenarios[scenario_id]["progress_percent"] = int((step_index / total_steps) * 100)
            
            # Generate records for this step
            records = []
            if attack_type == "normal":
                for _ in range(count):
                    records.append(_demo_generator.generate_normal_request())
            elif attack_type == "prompt_injection":
                for _ in range(count):
                    records.append(_demo_generator.generate_prompt_injection_attack())
            elif attack_type == "pii_leak":
                for _ in range(count):
                    records.append(_demo_generator.generate_pii_leak())
            elif attack_type == "jailbreak":
                for _ in range(count):
                    records.append(_demo_generator.generate_jailbreak_attempt())
            elif attack_type == "toxic_content":
                for _ in range(count):
                    records.append(_demo_generator.generate_toxic_content())
            elif attack_type == "cost_spike":
                records = _demo_generator.generate_cost_spike(count=count)
            elif attack_type == "quality_degradation":
                records = _demo_generator.generate_quality_degradation(count=count)
            elif attack_type == "latency_spike":
                for _ in range(count):
                    records.append(_demo_generator.generate_latency_spike())
            elif attack_type == "error_burst":
                records = _demo_generator.generate_error_burst(total=count)
            
            # Store records
            await _store_demo_records(records)
            total_records += len(records)
            
            _running_scenarios[scenario_id]["records_generated"] = total_records
            _running_scenarios[scenario_id]["steps_completed"] = step_index + 1
            
            # Delay between steps
            await asyncio.sleep(delay)
        
        # Mark as completed
        _running_scenarios[scenario_id]["status"] = "completed"
        _running_scenarios[scenario_id]["progress_percent"] = 100
        _running_scenarios[scenario_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    except Exception as e:
        _running_scenarios[scenario_id]["status"] = "failed"
        _running_scenarios[scenario_id]["error"] = str(e)


async def _calculate_demo_stats() -> Dict[str, Any]:
    """Calculate statistics from demo records in Firestore."""
    try:
        settings = get_settings()
        db = get_firestore_client()
        
        # Query all demo records
        demo_query = db.collection(settings.firestore_collection_telemetry).where(
            "metadata.demo_mode", "==", True
        ).stream()
        
        records = list(demo_query)
        
        if not records:
            return {
                "total_requests": 0,
                "threat_count": 0,
                "threat_breakdown": {},
                "avg_quality_score": 0.0,
                "total_cost_usd": 0.0,
                "avg_latency_ms": 0,
                "error_count": 0,
                "error_rate_percent": 0.0
            }
        
        total_requests = len(records)
        threat_count = 0
        threat_breakdown = {}
        total_quality = 0.0
        total_cost = 0.0
        total_latency = 0
        error_count = 0
        
        for doc in records:
            data = doc.to_dict()
            
            # Count threats
            threats = data.get("threats", [])
            if threats:
                threat_count += len(threats)
                for threat in threats:
                    threat_type = threat.get("type", "unknown")
                    threat_breakdown[threat_type] = threat_breakdown.get(threat_type, 0) + 1
            
            # Sum quality scores
            total_quality += data.get("quality_score", 0.0)
            
            # Sum costs
            total_cost += data.get("cost_usd", 0.0)
            
            # Sum latency
            total_latency += data.get("latency_ms", 0)
            
            # Count errors
            if data.get("metadata", {}).get("error", False):
                error_count += 1
        
        return {
            "total_requests": total_requests,
            "threat_count": threat_count,
            "threat_breakdown": threat_breakdown,
            "avg_quality_score": round(total_quality / total_requests, 2) if total_requests > 0 else 0.0,
            "total_cost_usd": round(total_cost, 2),
            "avg_latency_ms": int(total_latency / total_requests) if total_requests > 0 else 0,
            "error_count": error_count,
            "error_rate_percent": round((error_count / total_requests) * 100, 1) if total_requests > 0 else 0.0
        }
    
    except Exception as e:
        print(f"Error calculating demo stats: {e}")
        # Return empty stats on error
        return {
            "total_requests": 0,
            "threat_count": 0,
            "threat_breakdown": {},
            "avg_quality_score": 0.0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0,
            "error_count": 0,
            "error_rate_percent": 0.0
        }


async def _delete_demo_records() -> int:
    """Delete all demo records from Firestore."""
    try:
        settings = get_settings()
        db = get_firestore_client()
        
        # Query all demo records
        demo_query = db.collection(settings.firestore_collection_telemetry).where(
            "metadata.demo_mode", "==", True
        ).stream()
        
        deleted_count = 0
        for doc in demo_query:
            doc.reference.delete()
            deleted_count += 1
        
        return deleted_count
    
    except Exception as e:
        print(f"Error deleting demo records: {e}")
        raise
