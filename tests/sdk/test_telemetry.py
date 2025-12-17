"""
Property-based tests for GuardianAI SDK Telemetry Capture.

Tests Requirements 1.1 and 1.2 for complete request/response capture.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timezone

from guardianai.telemetry import (
    TelemetryCapture,
    RequestCapture,
    ResponseCapture,
    TelemetryData,
    CaptureContext,
)
from guardianai.cost import calculate_cost


# =============================================================================
# Property 1: Every request captures complete data (Requirement 1.1)
# =============================================================================

@given(
    prompt=st.text(min_size=1, max_size=10000),
    model=st.sampled_from(["gemini-pro", "gpt-4", "gpt-3.5-turbo", "gemini-ultra"]),
    temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
    max_tokens=st.one_of(st.none(), st.integers(min_value=1, max_value=8192)),
    user_id=st.one_of(st.none(), st.text(min_size=1, max_size=64).filter(lambda x: x.strip())),
    session_id=st.one_of(st.none(), st.text(min_size=1, max_size=64).filter(lambda x: x.strip())),
)
@settings(max_examples=100)
def test_property_1_complete_request_capture(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int | None,
    user_id: str | None,
    session_id: str | None,
):
    """
    Property 1: Request capture must include ALL required fields.
    
    Requirement 1.1: Capture must include:
    - prompt text
    - model identifier
    - temperature parameter
    - max_tokens parameter
    - request timestamp
    """
    capture = TelemetryCapture(service_name="test-service")
    
    request = capture.capture_request(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        user_id=user_id,
        session_id=session_id,
    )
    
    # All required fields must be present
    assert request.prompt == prompt, "Prompt must be captured exactly"
    assert request.model == model, "Model must be captured exactly"
    assert request.temperature == temperature, "Temperature must be captured"
    assert request.max_tokens == max_tokens, "Max tokens must be captured"
    assert request.timestamp is not None, "Timestamp must be present"
    
    # Timestamp must be valid ISO format
    timestamp = datetime.fromisoformat(request.timestamp.replace("Z", "+00:00"))
    assert timestamp <= datetime.now(timezone.utc), "Timestamp must not be in future"
    
    # Optional fields captured if provided
    assert request.user_id == user_id
    assert request.session_id == session_id


# =============================================================================
# Property 2: Every response captures complete data (Requirement 1.2)
# =============================================================================

@given(
    response_text=st.text(max_size=10000),
    input_tokens=st.integers(min_value=0, max_value=1000000),
    output_tokens=st.integers(min_value=0, max_value=1000000),
    latency_ms=st.floats(min_value=0.0, max_value=300000.0, allow_nan=False),
    model=st.sampled_from(["gemini-pro", "gpt-4", "gemini-ultra"]),
    finish_reason=st.one_of(st.none(), st.sampled_from(["stop", "length", "content_filter"])),
)
@settings(max_examples=100)
def test_property_2_complete_response_capture(
    response_text: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    model: str,
    finish_reason: str | None,
):
    """
    Property 2: Response capture must include ALL required fields.
    
    Requirement 1.2: Capture must include:
    - complete response text
    - input token count
    - output token count
    - total latency in milliseconds
    - calculated cost
    """
    capture = TelemetryCapture(service_name="test-service")
    
    response = capture.capture_response(
        response_text=response_text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        model=model,
        finish_reason=finish_reason,
    )
    
    # All required fields must be present per Requirement 1.2
    assert response.response_text == response_text, "Response text must be captured exactly"
    assert response.input_tokens == input_tokens, "Input tokens must be captured"
    assert response.output_tokens == output_tokens, "Output tokens must be captured"
    assert response.latency_ms == latency_ms, "Latency must be captured"
    
    # Cost must be calculated correctly
    expected_cost = calculate_cost(input_tokens, output_tokens, model)
    assert response.cost_usd == expected_cost, "Cost must be calculated correctly"
    
    # Cost must be non-negative
    assert response.cost_usd >= 0, "Cost cannot be negative"
    
    # Optional fields
    assert response.finish_reason == finish_reason


# =============================================================================
# Property: Capture context tracks timing correctly
# =============================================================================

@given(
    prompt=st.text(min_size=1, max_size=1000),
    model=st.sampled_from(["gemini-pro", "gpt-4"]),
)
@settings(max_examples=50)
def test_capture_context_timing(prompt: str, model: str):
    """Capture context must track timing and generate IDs."""
    capture = TelemetryCapture(service_name="test-service")
    
    with capture.start_capture(prompt=prompt, model=model) as ctx:
        # IDs must be unique
        assert ctx.trace_id is not None
        assert ctx.span_id is not None
        assert ctx.trace_id.startswith("trace_")
        assert ctx.span_id.startswith("span_")
        
        # Context must be active
        assert ctx.start_time > 0
    
    # After exit, timing complete
    latency = ctx.get_latency_ms()
    assert latency >= 0, "Latency must be non-negative"


# =============================================================================
# Property: TelemetryData serializes correctly
# =============================================================================

@given(
    prompt=st.text(min_size=1, max_size=500),
    response_text=st.text(max_size=500),
    input_tokens=st.integers(min_value=0, max_value=10000),
    output_tokens=st.integers(min_value=0, max_value=10000),
)
@settings(max_examples=50)
def test_telemetry_data_serialization(
    prompt: str,
    response_text: str,
    input_tokens: int,
    output_tokens: int,
):
    """TelemetryData must serialize to dict with all fields."""
    capture = TelemetryCapture(service_name="test-service")
    
    with capture.start_capture(prompt=prompt, model="gemini-pro") as ctx:
        ctx.record_response(
            response_text=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    
    data = ctx.to_dict()
    
    # Must contain all required fields
    assert "trace_id" in data
    assert "span_id" in data
    assert "timestamp" in data
    assert "prompt" in data
    assert "model" in data
    assert "response_text" in data
    assert "input_tokens" in data
    assert "output_tokens" in data
    assert "latency_ms" in data
    assert "cost_usd" in data
    assert "service_name" in data
    assert "environment" in data
    
    # Values must match
    assert data["prompt"] == prompt
    assert data["response_text"] == response_text
    assert data["input_tokens"] == input_tokens
    assert data["output_tokens"] == output_tokens


# =============================================================================
# Property: Error capture works correctly
# =============================================================================

@given(
    prompt=st.text(min_size=1, max_size=500),
    error_msg=st.text(min_size=1, max_size=200),
)
@settings(max_examples=50)
def test_error_capture(prompt: str, error_msg: str):
    """Errors must be captured in telemetry."""
    capture = TelemetryCapture(service_name="test-service")
    
    with capture.start_capture(prompt=prompt, model="gemini-pro") as ctx:
        ctx.record_error(error_msg)
    
    telemetry = ctx.get_telemetry()
    
    assert telemetry.status == "error"
    assert telemetry.response is not None
    assert telemetry.response.error == error_msg
