"""
Property-based tests for GuardianAI SDK Datadog Tracer.

Tests Requirements 3.1 and 3.2 for trace ID uniqueness and tags.
"""

import pytest
from hypothesis import given, strategies as st, settings

from guardianai.tracer import DatadogTracer, SpanContext, SpanData, get_required_tags


# =============================================================================
# Property 3: Every trace has a unique trace_id (Requirement 3.1)
# =============================================================================

@given(
    num_traces=st.integers(min_value=10, max_value=100),
)
@settings(max_examples=20)
def test_property_3_unique_trace_ids(num_traces: int):
    """
    Property 3: Every request gets a unique trace_id.
    
    Requirement 3.1: Each request must have a unique trace identifier.
    """
    tracer = DatadogTracer(service_name="test-service")
    
    trace_ids = set()
    
    for _ in range(num_traces):
        trace_id = tracer.generate_trace_id()
        assert trace_id not in trace_ids, f"Duplicate trace_id: {trace_id}"
        trace_ids.add(trace_id)
    
    assert len(trace_ids) == num_traces, "All trace IDs must be unique"


@given(
    num_spans=st.integers(min_value=10, max_value=100),
)
@settings(max_examples=20)
def test_unique_span_ids(num_spans: int):
    """Every span gets a unique span_id."""
    tracer = DatadogTracer(service_name="test-service")
    
    span_ids = set()
    
    for _ in range(num_spans):
        span_id = tracer.generate_span_id()
        assert span_id not in span_ids, f"Duplicate span_id: {span_id}"
        span_ids.add(span_id)
    
    assert len(span_ids) == num_spans


# =============================================================================
# Property 21: Traces include required tags (Requirement 3.2)
# =============================================================================

@given(
    service_name=st.text(min_size=1, max_size=64).filter(lambda x: x.strip()),
    environment=st.sampled_from(["development", "staging", "production"]),
    model=st.sampled_from(["gemini-pro", "gpt-4", "gpt-3.5-turbo"]),
    prompt=st.text(min_size=1, max_size=1000),
    temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
)
@settings(max_examples=50)
def test_property_21_trace_tags(
    service_name: str,
    environment: str,
    model: str,
    prompt: str,
    temperature: float,
):
    """
    Property 21: Traces must include required tags.
    
    Requirement 3.2: Tags must include:
    - service name
    - environment
    - model
    - operation type
    """
    tracer = DatadogTracer(
        service_name=service_name,
        environment=environment
    )
    
    with tracer.trace_llm_request(
        prompt=prompt,
        model=model,
        temperature=temperature,
    ) as span_ctx:
        # Required tags per Requirement 3.2
        assert span_ctx.span.tags.get("service") == service_name
        assert span_ctx.span.tags.get("environment") == environment
        assert span_ctx.span.tags.get("model") == model
        assert span_ctx.span.tags.get("operation.type") == "llm"
        
        # Additional tags should be present
        assert "temperature" in span_ctx.span.tags
        assert "prompt_length" in span_ctx.span.tags


@given(
    service_name=st.text(min_size=1, max_size=32).filter(lambda x: x.strip()),
    environment=st.sampled_from(["development", "staging", "production"]),
    model=st.sampled_from(["gemini-pro", "gpt-4"]),
)
@settings(max_examples=50)
def test_get_required_tags(service_name: str, environment: str, model: str):
    """get_required_tags returns all required tags per 3.2."""
    tags = get_required_tags(service_name, environment, model)
    
    assert tags["service"] == service_name
    assert tags["environment"] == environment
    assert tags["model"] == model
    assert tags["operation.type"] == "llm"


# =============================================================================
# Property: Span context operations work correctly
# =============================================================================

@given(
    tag_key=st.text(min_size=1, max_size=32).filter(lambda x: x.strip() and x.isidentifier()),
    tag_value=st.text(min_size=1, max_size=100),
    metric_key=st.text(min_size=1, max_size=32).filter(lambda x: x.strip() and x.isidentifier()),
    metric_value=st.floats(min_value=-1e10, max_value=1e10, allow_nan=False),
)
@settings(max_examples=50)
def test_span_context_tags_and_metrics(
    tag_key: str,
    tag_value: str,
    metric_key: str,
    metric_value: float,
):
    """SpanContext correctly stores tags and metrics."""
    tracer = DatadogTracer(service_name="test-service")
    
    with tracer.start_trace(operation_name="test.op") as span_ctx:
        span_ctx.set_tag(tag_key, tag_value)
        span_ctx.set_metric(metric_key, metric_value)
        
        assert span_ctx.span.tags[tag_key] == tag_value
        assert span_ctx.span.metrics[metric_key] == metric_value


# =============================================================================
# Property: LLM metadata is recorded correctly
# =============================================================================

@given(
    input_tokens=st.integers(min_value=0, max_value=1000000),
    output_tokens=st.integers(min_value=0, max_value=1000000),
    latency_ms=st.floats(min_value=0.0, max_value=300000.0, allow_nan=False),
    cost_usd=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False),
)
@settings(max_examples=50)
def test_llm_metadata(
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    cost_usd: float,
):
    """LLM metadata is correctly added to spans."""
    tracer = DatadogTracer(service_name="test-service")
    
    with tracer.start_trace(operation_name="llm.generate") as span_ctx:
        span_ctx.add_llm_metadata(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )
        
        assert span_ctx.span.metrics["llm.input_tokens"] == float(input_tokens)
        assert span_ctx.span.metrics["llm.output_tokens"] == float(output_tokens)
        assert span_ctx.span.metrics["llm.total_tokens"] == float(input_tokens + output_tokens)
        assert span_ctx.span.metrics["llm.latency_ms"] == latency_ms
        assert span_ctx.span.metrics["llm.cost_usd"] == cost_usd


# =============================================================================
# Property: SpanData serialization is complete
# =============================================================================

@given(
    trace_id=st.text(min_size=8, max_size=32).filter(lambda x: x.strip()),
    span_id=st.text(min_size=4, max_size=16).filter(lambda x: x.strip()),
    operation_name=st.text(min_size=1, max_size=64).filter(lambda x: x.strip()),
    service_name=st.text(min_size=1, max_size=32).filter(lambda x: x.strip()),
)
@settings(max_examples=50)
def test_span_data_serialization(
    trace_id: str,
    span_id: str,
    operation_name: str,
    service_name: str,
):
    """SpanData serializes to dict with all required fields."""
    span = SpanData(
        trace_id=trace_id,
        span_id=span_id,
        parent_id=None,
        operation_name=operation_name,
        service_name=service_name,
        resource_name=operation_name,
        start_time_ns=1000000000,
        duration_ns=500000000,
    )
    
    data = span.to_dict()
    
    assert data["trace_id"] == trace_id
    assert data["span_id"] == span_id
    assert data["name"] == operation_name
    assert data["service"] == service_name
    assert data["start"] == 1000000000
    assert data["duration"] == 500000000


# =============================================================================
# Property: Error handling in traces
# =============================================================================

@given(
    error_message=st.text(min_size=1, max_size=200),
)
@settings(max_examples=30)
def test_trace_error_handling(error_message: str):
    """Traces correctly record errors."""
    tracer = DatadogTracer(service_name="test-service")
    
    with tracer.start_trace(operation_name="test.op") as span_ctx:
        span_ctx.set_error(error_message)
        
        assert span_ctx.span.status == "error"
        assert span_ctx.span.error == error_message
        assert span_ctx.span.tags.get("error.message") == error_message
