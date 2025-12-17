"""
Property-based tests for GuardianAI SDK Telemetry Transmitter.

Tests Requirements 4.1 and 4.2 for transmission timing and batching.
"""

import pytest
import time
from hypothesis import given, strategies as st, settings

from guardianai.transmitter import (
    TelemetryTransmitter,
    TransmissionConfig,
    TransmissionResult,
)


# =============================================================================
# Property 4: Transmission within 1 second (Requirement 4.1)
# =============================================================================

@given(
    num_items=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=20)
def test_property_4_transmission_timing(num_items: int):
    """
    Property 4: Telemetry must be transmitted within 1 second.
    
    Requirement 4.1: Telemetry must be transmitted to backend 
    within 1 second of generation.
    """
    transmission_times = []
    
    def on_send(batch):
        transmission_times.append(time.time())
    
    transmitter = TelemetryTransmitter(
        backend_url="http://localhost:8000",
        batch_size=10,
        flush_interval_seconds=0.5,  # Fast flush for testing
        on_send=on_send
    )
    
    start_time = time.time()
    
    # Enqueue items
    for i in range(num_items):
        transmitter.enqueue({"id": i, "data": f"test_{i}"})
    
    # Flush immediately
    transmitter.flush_all()
    
    # Verify timing
    for tx_time in transmission_times:
        elapsed = tx_time - start_time
        assert elapsed < 1.0, f"Transmission took {elapsed:.2f}s, exceeds 1s limit"


# =============================================================================
# Property 24: Batch size max 10 (Requirement 4.2)
# =============================================================================

@given(
    num_items=st.integers(min_value=1, max_value=50),
)
@settings(max_examples=30)
def test_property_24_batch_size_limit(num_items: int):
    """
    Property 24: Batches must not exceed 10 items.
    
    Requirement 4.2: Batch transmission with max 10 items per batch.
    """
    batch_sizes = []
    
    def on_send(batch):
        batch_sizes.append(len(batch))
    
    transmitter = TelemetryTransmitter(
        backend_url="http://localhost:8000",
        batch_size=10,  # Max per Requirement 4.2
        on_send=on_send
    )
    
    # Enqueue items
    for i in range(num_items):
        transmitter.enqueue({"id": i, "data": f"test_{i}"})
    
    # Flush all
    transmitter.flush_all()
    
    # Verify all batches <= 10
    for size in batch_sizes:
        assert size <= 10, f"Batch size {size} exceeds limit of 10"
    
    # Verify total items sent
    assert sum(batch_sizes) == num_items


@given(
    batch_size_config=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=20)
def test_batch_size_config_capped_at_10(batch_size_config: int):
    """Batch size configuration is capped at 10."""
    transmitter = TelemetryTransmitter(
        backend_url="http://localhost:8000",
        batch_size=batch_size_config,  # Should be capped
    )
    
    assert transmitter.config.batch_size <= 10


# =============================================================================
# Property: All enqueued items are eventually transmitted
# =============================================================================

@given(
    num_items=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=30)
def test_all_items_transmitted(num_items: int):
    """All enqueued items must be transmitted."""
    received_items = []
    
    def on_send(batch):
        received_items.extend(batch)
    
    transmitter = TelemetryTransmitter(
        backend_url="http://localhost:8000",
        batch_size=10,
        on_send=on_send
    )
    
    # Enqueue items
    for i in range(num_items):
        success = transmitter.enqueue({"id": i})
        assert success, f"Failed to enqueue item {i}"
    
    # Flush all
    transmitter.flush_all()
    
    # Verify all items received
    assert len(received_items) == num_items
    
    # Verify order preserved within batches
    received_ids = [item["id"] for item in received_items]
    assert received_ids == list(range(num_items))


# =============================================================================
# Property: Queue overflow protection
# =============================================================================

def test_queue_overflow_protection():
    """Queue overflow is handled gracefully."""
    transmitter = TelemetryTransmitter(
        backend_url="http://localhost:8000",
        max_queue_size=10,
    )
    
    # Fill queue
    for i in range(10):
        assert transmitter.enqueue({"id": i}) is True
    
    # Overflow should be handled
    overflow_result = transmitter.enqueue({"id": 100})
    assert overflow_result is False
    
    stats = transmitter.get_stats()
    assert stats["dropped"] == 1


# =============================================================================
# Property: Stats tracking accuracy
# =============================================================================

@given(
    num_items=st.integers(min_value=1, max_value=50),
)
@settings(max_examples=20)
def test_stats_tracking(num_items: int):
    """Statistics are tracked accurately."""
    def on_send(batch):
        pass  # Just accept the batch
    
    transmitter = TelemetryTransmitter(
        backend_url="http://localhost:8000",
        batch_size=10,
        on_send=on_send
    )
    
    # Enqueue items
    for i in range(num_items):
        transmitter.enqueue({"id": i})
    
    stats_before = transmitter.get_stats()
    assert stats_before["enqueued"] == num_items
    
    # Flush
    transmitter.flush_all()
    
    stats_after = transmitter.get_stats()
    assert stats_after["sent"] == num_items
    assert stats_after["failed"] == 0


# =============================================================================
# Property: TransmissionResult correctness
# =============================================================================

@given(
    num_items=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=20)
def test_transmission_result_correctness(num_items: int):
    """TransmissionResult accurately reflects transmission outcome."""
    def on_send(batch):
        pass
    
    transmitter = TelemetryTransmitter(
        backend_url="http://localhost:8000",
        batch_size=10,
        on_send=on_send
    )
    
    for i in range(num_items):
        transmitter.enqueue({"id": i})
    
    result = transmitter.flush()
    
    assert isinstance(result, TransmissionResult)
    assert result.success is True
    assert result.items_sent == num_items
    assert result.items_failed == 0
    assert result.latency_ms >= 0


# =============================================================================
# Property: Empty flush is no-op
# =============================================================================

def test_empty_flush_is_noop():
    """Flushing empty queue returns success with zero items."""
    transmitter = TelemetryTransmitter(
        backend_url="http://localhost:8000",
    )
    
    result = transmitter.flush()
    
    assert result.success is True
    assert result.items_sent == 0
    assert result.items_failed == 0


# =============================================================================
# Property: Queue size tracking
# =============================================================================

@given(
    num_items=st.integers(min_value=0, max_value=50),
)
@settings(max_examples=20)
def test_queue_size_tracking(num_items: int):
    """Queue size is tracked accurately."""
    transmitter = TelemetryTransmitter(
        backend_url="http://localhost:8000",
        max_queue_size=100,
    )
    
    assert transmitter.get_queue_size() == 0
    
    for i in range(num_items):
        transmitter.enqueue({"id": i})
    
    assert transmitter.get_queue_size() == num_items
    
    transmitter.flush_all()
    
    assert transmitter.get_queue_size() == 0


# =============================================================================
# Property: Start/stop lifecycle
# =============================================================================

def test_transmitter_lifecycle():
    """Transmitter can be started and stopped correctly."""
    transmitter = TelemetryTransmitter(
        backend_url="http://localhost:8000",
    )
    
    assert transmitter.is_running is False
    
    transmitter.start()
    assert transmitter.is_running is True
    
    transmitter.stop(flush=False)
    assert transmitter.is_running is False


# =============================================================================
# Property: TransmissionConfig validation
# =============================================================================

@given(
    batch_size=st.integers(min_value=1, max_value=100),
    flush_interval=st.floats(min_value=0.1, max_value=60.0, allow_nan=False),
    max_queue_size=st.integers(min_value=1, max_value=10000),
)
@settings(max_examples=30)
def test_transmission_config(
    batch_size: int,
    flush_interval: float,
    max_queue_size: int,
):
    """TransmissionConfig handles various configurations."""
    config = TransmissionConfig(
        batch_size=batch_size,
        flush_interval_seconds=flush_interval,
        max_queue_size=max_queue_size,
    )
    
    assert config.batch_size == batch_size
    assert config.flush_interval_seconds == flush_interval
    assert config.max_queue_size == max_queue_size
