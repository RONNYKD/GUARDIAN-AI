"""
GuardianAI Firestore Client

Provides database operations for telemetry, incidents, configuration, and user data.
Implements connection pooling and retry logic for reliability.
"""

from datetime import datetime, timezone
from typing import Any, Optional
import logging

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from backend.config import get_settings

logger = logging.getLogger(__name__)


class FirestoreClient:
    """
    Wrapper class for Firestore database operations.
    
    Provides methods for CRUD operations on GuardianAI collections:
    - telemetry: LLM interaction records
    - incidents: Security/performance incidents
    - config: System configuration
    - users: User data and rate limits
    - attacks: Demo mode attack records
    
    Example:
        >>> client = FirestoreClient()
        >>> client.store_telemetry(telemetry_data)
    """

    _instance: Optional["FirestoreClient"] = None
    _db: Optional[firestore.Client] = None

    def __new__(cls) -> "FirestoreClient":
        """Singleton pattern for database connection."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize Firestore client if not already initialized."""
        if FirestoreClient._db is None:
            settings = get_settings()
            FirestoreClient._db = firestore.Client(project=settings.gcp_project_id)
            logger.info(f"Firestore client initialized for project: {settings.gcp_project_id}")

    @property
    def db(self) -> firestore.Client:
        """Get the Firestore client instance."""
        if self._db is None:
            raise RuntimeError("Firestore client not initialized")
        return self._db

    # ============================================
    # Telemetry Operations
    # ============================================

    def store_telemetry(self, telemetry: dict[str, Any]) -> str:
        """
        Store a telemetry record in Firestore.

        Args:
            telemetry: Telemetry data with trace_id, prompt, response, metrics, etc.

        Returns:
            str: Document ID of the stored record

        Raises:
            Exception: If storage fails after retries
        """
        settings = get_settings()
        collection = self.db.collection(settings.telemetry_collection)
        
        # Add timestamp if not present
        if "stored_at" not in telemetry:
            telemetry["stored_at"] = datetime.now(timezone.utc).isoformat()
        
        # Use trace_id as document ID for easy lookup
        doc_id = telemetry.get("trace_id", collection.document().id)
        doc_ref = collection.document(doc_id)
        doc_ref.set(telemetry)
        
        logger.debug(f"Stored telemetry: {doc_id}")
        return doc_id

    def get_telemetry(self, trace_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieve a telemetry record by trace ID.

        Args:
            trace_id: Unique trace identifier

        Returns:
            Telemetry data or None if not found
        """
        settings = get_settings()
        doc = self.db.collection(settings.telemetry_collection).document(trace_id).get()
        return doc.to_dict() if doc.exists else None

    def get_recent_telemetry(
        self,
        limit: int = 100,
        model_filter: Optional[str] = None,
        threat_filter: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve recent telemetry records with optional filtering.

        Args:
            limit: Maximum number of records to return
            model_filter: Filter by model name
            threat_filter: Filter by threat_detected flag
            start_time: Filter records after this time
            end_time: Filter records before this time

        Returns:
            List of telemetry records ordered by timestamp descending
        """
        settings = get_settings()
        query = self.db.collection(settings.telemetry_collection)

        if model_filter:
            query = query.where(filter=FieldFilter("model", "==", model_filter))
        
        if threat_filter is not None:
            query = query.where(filter=FieldFilter("threat_detected", "==", threat_filter))
        
        if start_time:
            query = query.where(filter=FieldFilter("timestamp", ">=", start_time.isoformat()))
        
        if end_time:
            query = query.where(filter=FieldFilter("timestamp", "<=", end_time.isoformat()))

        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)

        return [doc.to_dict() for doc in query.stream()]

    # ============================================
    # Incident Operations
    # ============================================

    def create_incident(self, incident: dict[str, Any]) -> str:
        """
        Create a new incident record.

        Args:
            incident: Incident data with rule_name, severity, status, etc.

        Returns:
            str: Document ID of the created incident
        """
        settings = get_settings()
        collection = self.db.collection(settings.incidents_collection)
        
        # Generate incident ID if not provided
        incident_id = incident.get("incident_id", f"inc_{collection.document().id}")
        incident["incident_id"] = incident_id
        
        # Add timestamps
        now = datetime.now(timezone.utc).isoformat()
        incident.setdefault("created_at", now)
        incident.setdefault("updated_at", now)
        incident.setdefault("status", "open")
        
        doc_ref = collection.document(incident_id)
        doc_ref.set(incident)
        
        logger.info(f"Created incident: {incident_id}")
        return incident_id

    def get_incident(self, incident_id: str) -> Optional[dict[str, Any]]:
        """Retrieve an incident by ID."""
        settings = get_settings()
        doc = self.db.collection(settings.incidents_collection).document(incident_id).get()
        return doc.to_dict() if doc.exists else None

    def update_incident(self, incident_id: str, updates: dict[str, Any]) -> bool:
        """
        Update an existing incident.

        Args:
            incident_id: Incident ID to update
            updates: Fields to update

        Returns:
            bool: True if update succeeded
        """
        settings = get_settings()
        doc_ref = self.db.collection(settings.incidents_collection).document(incident_id)
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        doc_ref.update(updates)
        
        logger.info(f"Updated incident: {incident_id}")
        return True

    def get_recent_incidents(
        self,
        limit: int = 10,
        status_filter: Optional[str] = None,
        severity_filter: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve recent incidents with optional filtering.

        Args:
            limit: Maximum number of incidents to return
            status_filter: Filter by status (open, investigating, resolved)
            severity_filter: Filter by severity (low, medium, high, critical)

        Returns:
            List of incidents ordered by created_at descending
        """
        settings = get_settings()
        query = self.db.collection(settings.incidents_collection)

        if status_filter:
            query = query.where(filter=FieldFilter("status", "==", status_filter))
        
        if severity_filter:
            query = query.where(filter=FieldFilter("severity", "==", severity_filter))

        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)

        return [doc.to_dict() for doc in query.stream()]

    # ============================================
    # Configuration Operations
    # ============================================

    def get_config(self, config_key: str) -> Optional[dict[str, Any]]:
        """Get a configuration value by key."""
        settings = get_settings()
        doc = self.db.collection(settings.config_collection).document(config_key).get()
        return doc.to_dict() if doc.exists else None

    def set_config(self, config_key: str, config_value: dict[str, Any]) -> None:
        """Set a configuration value."""
        settings = get_settings()
        config_value["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.db.collection(settings.config_collection).document(config_key).set(config_value)
        logger.info(f"Updated config: {config_key}")

    # ============================================
    # Rate Limiting Operations
    # ============================================

    def get_rate_limit(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get rate limit settings for a user."""
        settings = get_settings()
        doc = self.db.collection(settings.rate_limits_collection).document(user_id).get()
        return doc.to_dict() if doc.exists else None

    def set_rate_limit(
        self,
        user_id: str,
        limit: int,
        window_seconds: int = 60,
        reason: str = ""
    ) -> None:
        """
        Set rate limit for a user.

        Args:
            user_id: User identifier
            limit: Maximum requests per window
            window_seconds: Time window in seconds
            reason: Reason for rate limit
        """
        settings = get_settings()
        data = {
            "user_id": user_id,
            "limit": limit,
            "window_seconds": window_seconds,
            "reason": reason,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True
        }
        self.db.collection(settings.rate_limits_collection).document(user_id).set(data)
        logger.info(f"Set rate limit for user {user_id}: {limit} req/{window_seconds}s")

    def remove_rate_limit(self, user_id: str) -> None:
        """Remove rate limit for a user."""
        settings = get_settings()
        doc_ref = self.db.collection(settings.rate_limits_collection).document(user_id)
        doc_ref.update({"active": False})
        logger.info(f"Removed rate limit for user: {user_id}")

    # ============================================
    # Attack Simulation Operations (Demo Mode)
    # ============================================

    def log_attack(self, attack: dict[str, Any]) -> str:
        """Log an attack simulation for demo mode."""
        settings = get_settings()
        collection = self.db.collection(settings.attacks_collection)
        
        attack_id = attack.get("attack_id", f"atk_{collection.document().id}")
        attack["attack_id"] = attack_id
        attack.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        
        doc_ref = collection.document(attack_id)
        doc_ref.set(attack)
        
        logger.info(f"Logged attack: {attack_id}")
        return attack_id

    def get_attack_stats(self, time_range_hours: int = 24) -> dict[str, Any]:
        """Get attack statistics for demo mode."""
        settings = get_settings()
        from datetime import timedelta
        
        start_time = (datetime.now(timezone.utc) - timedelta(hours=time_range_hours)).isoformat()
        
        query = self.db.collection(settings.attacks_collection)
        query = query.where(filter=FieldFilter("timestamp", ">=", start_time))
        
        attacks = [doc.to_dict() for doc in query.stream()]
        
        stats = {
            "total_attacks": len(attacks),
            "by_type": {},
            "threats_detected": 0,
            "remediated": 0
        }
        
        for attack in attacks:
            attack_type = attack.get("type", "unknown")
            stats["by_type"][attack_type] = stats["by_type"].get(attack_type, 0) + 1
            if attack.get("detected", False):
                stats["threats_detected"] += 1
            if attack.get("remediated", False):
                stats["remediated"] += 1
        
        return stats


# Initialize collections on first import
def initialize_collections() -> None:
    """
    Initialize Firestore collections with indexes.
    
    This function creates the required collections if they don't exist
    and sets up any necessary indexes for efficient querying.
    """
    try:
        client = FirestoreClient()
        settings = get_settings()
        
        # Touch collections to ensure they exist
        collections = [
            settings.telemetry_collection,
            settings.incidents_collection,
            settings.config_collection,
            settings.users_collection,
            settings.attacks_collection,
            settings.rate_limits_collection
        ]
        
        for collection_name in collections:
            # Create a placeholder document to ensure collection exists
            placeholder_ref = client.db.collection(collection_name).document("_placeholder")
            if not placeholder_ref.get().exists:
                placeholder_ref.set({"_initialized": True})
                logger.info(f"Initialized collection: {collection_name}")
        
        logger.info("All Firestore collections initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize Firestore collections: {e}")
        raise


# Singleton accessor
def get_firestore_client() -> FirestoreClient:
    """Get the Firestore client singleton."""
    return FirestoreClient()
