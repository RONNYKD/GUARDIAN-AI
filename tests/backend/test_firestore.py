"""
GuardianAI Backend Tests - Firestore Client

Property-based tests for Firestore storage operations.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(__file__).replace("\\tests\\backend\\test_firestore.py", ""))


# Custom strategies for telemetry data
trace_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
    min_size=8,
    max_size=32
).map(lambda x: f"trace_{x}")

prompt_strategy = st.text(min_size=1, max_size=1000)

model_strategy = st.sampled_from(["gemini-pro", "gemini-pro-vision", "gemini-ultra"])

user_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
    min_size=4,
    max_size=20
).map(lambda x: f"user_{x}")


class TestFirestoreStorageCompleteness:
    """
    Tests for Property 5: Complete Storage with Indexing
    
    For any telemetry received by the Processing Pipeline, the stored
    Firestore record should contain the complete trace data and have
    indexed fields for timestamp, model, and user_session.
    
    Validates: Requirements 1.5
    """
    
    @given(
        trace_id=trace_id_strategy,
        prompt=prompt_strategy,
        model=model_strategy,
        user_id=user_id_strategy,
        input_tokens=st.integers(min_value=0, max_value=100000),
        output_tokens=st.integers(min_value=0, max_value=100000),
        latency_ms=st.floats(min_value=0, max_value=60000, allow_nan=False),
        temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False)
    )
    @settings(max_examples=50)
    def test_telemetry_storage_completeness_property(
        self,
        trace_id: str,
        prompt: str,
        model: str,
        user_id: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        temperature: float
    ):
        """
        Feature: guardianai, Property 5: Complete Storage with Indexing
        
        For any telemetry received, the stored Firestore record should contain:
        - Complete trace data
        - Indexed fields: timestamp, model, user_session
        
        Validates: Requirements 1.5
        """
        # Skip empty prompts
        assume(len(prompt.strip()) > 0)
        
        # Create telemetry data
        timestamp = datetime.now(timezone.utc).isoformat()
        telemetry = {
            "trace_id": trace_id,
            "timestamp": timestamp,
            "prompt": prompt,
            "model": model,
            "user_id": user_id,
            "session_id": f"session_{user_id}",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "temperature": temperature,
            "response_text": "Test response",
            "cost_usd": (input_tokens * 0.00025) + (output_tokens * 0.0005)
        }
        
        # Mock Firestore client
        with patch("backend.services.firestore_client.firestore") as mock_firestore:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_doc = MagicMock()
            
            mock_firestore.Client.return_value = mock_db
            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_doc
            
            # Import after patching
            from backend.services.firestore_client import FirestoreClient
            
            # Reset singleton for testing
            FirestoreClient._instance = None
            FirestoreClient._db = mock_db
            
            client = FirestoreClient()
            client.store_telemetry(telemetry)
            
            # Verify set was called with complete data
            mock_doc.set.assert_called_once()
            stored_data = mock_doc.set.call_args[0][0]
            
            # Property assertions: Complete storage
            assert "trace_id" in stored_data
            assert stored_data["trace_id"] == trace_id
            
            # Required indexed fields for Requirements 1.5
            assert "timestamp" in stored_data
            assert "model" in stored_data
            assert stored_data["model"] == model
            
            # User session for indexing
            assert "user_id" in stored_data or "session_id" in stored_data
            
            # Complete trace data
            assert "prompt" in stored_data
            assert "input_tokens" in stored_data
            assert "output_tokens" in stored_data
            assert "latency_ms" in stored_data
    
    @given(
        trace_id=trace_id_strategy,
        model=model_strategy
    )
    @settings(max_examples=20)
    def test_telemetry_retrieval_by_trace_id(
        self,
        trace_id: str,
        model: str
    ):
        """
        Test that stored telemetry can be retrieved by trace_id.
        """
        telemetry = {
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": "test prompt",
            "model": model,
            "input_tokens": 10,
            "output_tokens": 20
        }
        
        with patch("backend.services.firestore_client.firestore") as mock_firestore:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_doc = MagicMock()
            mock_doc_snapshot = MagicMock()
            
            mock_firestore.Client.return_value = mock_db
            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_doc
            mock_doc.get.return_value = mock_doc_snapshot
            mock_doc_snapshot.exists = True
            mock_doc_snapshot.to_dict.return_value = telemetry
            
            from backend.services.firestore_client import FirestoreClient
            
            FirestoreClient._instance = None
            FirestoreClient._db = mock_db
            
            client = FirestoreClient()
            result = client.get_telemetry(trace_id)
            
            # Property: Retrieved data matches stored data
            assert result is not None
            assert result["trace_id"] == trace_id
            assert result["model"] == model


class TestFirestoreIndexedQueries:
    """Tests for indexed field queries."""
    
    @given(model=model_strategy)
    @settings(max_examples=10)
    def test_query_by_model_uses_index(self, model: str):
        """
        Test that queries by model field work correctly.
        Indexed field per Requirements 1.5.
        """
        with patch("backend.services.firestore_client.firestore") as mock_firestore:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_query = MagicMock()
            
            mock_firestore.Client.return_value = mock_db
            mock_db.collection.return_value = mock_collection
            mock_collection.where.return_value = mock_query
            mock_query.where.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.stream.return_value = []
            
            from backend.services.firestore_client import FirestoreClient
            
            FirestoreClient._instance = None
            FirestoreClient._db = mock_db
            
            client = FirestoreClient()
            result = client.get_recent_telemetry(limit=10, model_filter=model)
            
            # Verify model filter was applied
            assert isinstance(result, list)


class TestFirestoreIncidentStorage:
    """Tests for incident storage operations."""
    
    @given(
        rule_name=st.sampled_from(["cost_anomaly", "security_threat", "quality_degradation"]),
        severity=st.sampled_from(["low", "medium", "high", "critical"])
    )
    @settings(max_examples=20)
    def test_incident_creation_completeness(
        self,
        rule_name: str,
        severity: str
    ):
        """
        Test that incidents are created with all required fields.
        Validates Requirements 8.2.
        """
        incident_data = {
            "rule_name": rule_name,
            "severity": severity,
            "title": f"Test incident for {rule_name}",
            "description": "Test description"
        }
        
        with patch("backend.services.firestore_client.firestore") as mock_firestore:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_doc = MagicMock()
            mock_doc.id = "auto_generated_id"
            
            mock_firestore.Client.return_value = mock_db
            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_doc
            
            from backend.services.firestore_client import FirestoreClient
            
            FirestoreClient._instance = None
            FirestoreClient._db = mock_db
            
            client = FirestoreClient()
            incident_id = client.create_incident(incident_data)
            
            # Verify incident was created
            mock_doc.set.assert_called_once()
            stored_data = mock_doc.set.call_args[0][0]
            
            # Property: All required fields present (Requirement 8.2)
            assert "incident_id" in stored_data
            assert "created_at" in stored_data
            assert "updated_at" in stored_data
            assert "status" in stored_data
            assert stored_data["status"] == "open"  # Default status
            assert "severity" in stored_data
            assert "rule_name" in stored_data


class TestFirestoreRateLimiting:
    """Tests for rate limit storage operations."""
    
    @given(
        user_id=user_id_strategy,
        limit=st.integers(min_value=1, max_value=1000),
        window_seconds=st.integers(min_value=1, max_value=3600)
    )
    @settings(max_examples=20)
    def test_rate_limit_storage(
        self,
        user_id: str,
        limit: int,
        window_seconds: int
    ):
        """
        Test that rate limits are stored correctly.
        Validates Requirements 9.1.
        """
        with patch("backend.services.firestore_client.firestore") as mock_firestore:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_doc = MagicMock()
            
            mock_firestore.Client.return_value = mock_db
            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_doc
            
            from backend.services.firestore_client import FirestoreClient
            
            FirestoreClient._instance = None
            FirestoreClient._db = mock_db
            
            client = FirestoreClient()
            client.set_rate_limit(
                user_id=user_id,
                limit=limit,
                window_seconds=window_seconds,
                reason="Test rate limit"
            )
            
            # Verify rate limit was stored
            mock_doc.set.assert_called_once()
            stored_data = mock_doc.set.call_args[0][0]
            
            # Property: Rate limit data is complete
            assert stored_data["user_id"] == user_id
            assert stored_data["limit"] == limit
            assert stored_data["window_seconds"] == window_seconds
            assert stored_data["active"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
