"""
Property-based tests for GuardianAI SDK @monitor_llm decorator.

Tests decorator functionality for complete instrumentation.
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings

from guardianai.decorator import (
    monitor_llm,
    _extract_params,
    _extract_response_data,
    MonitorConfig,
)


# =============================================================================
# Test: Decorator preserves function behavior
# =============================================================================

@given(
    prompt=st.text(min_size=1, max_size=1000),
    suffix=st.text(max_size=100),
)
@settings(max_examples=50)
def test_decorator_preserves_sync_function(prompt: str, suffix: str):
    """Decorator must not alter function return value."""
    @monitor_llm(
        service_name="test-service",
        enable_tracing=False,
        enable_transmission=False,
    )
    def echo_function(prompt: str) -> str:
        return f"Response: {prompt}{suffix}"
    
    result = echo_function(prompt=prompt)
    
    assert result == f"Response: {prompt}{suffix}"


@given(
    prompt=st.text(min_size=1, max_size=500),
    temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
)
@settings(max_examples=30)
def test_decorator_preserves_async_function(prompt: str, temperature: float):
    """Decorator must work with async functions."""
    @monitor_llm(
        service_name="test-service",
        enable_tracing=False,
        enable_transmission=False,
    )
    async def async_echo(prompt: str, temperature: float = 0.7) -> str:
        await asyncio.sleep(0.001)
        return f"Async: {prompt}"
    
    result = asyncio.run(async_echo(prompt=prompt, temperature=temperature))
    
    assert result == f"Async: {prompt}"


# =============================================================================
# Test: Parameter extraction
# =============================================================================

@given(
    prompt=st.text(min_size=1, max_size=500),
    temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
    max_tokens=st.one_of(st.none(), st.integers(min_value=1, max_value=8192)),
)
@settings(max_examples=50)
def test_parameter_extraction(prompt: str, temperature: float, max_tokens: int | None):
    """Parameters are correctly extracted from function calls."""
    def sample_func(prompt: str, temperature: float = 0.7, max_tokens: int = None):
        pass
    
    config = MonitorConfig(prompt_param="prompt")
    
    if max_tokens is not None:
        params = _extract_params(
            args=(),
            kwargs={"prompt": prompt, "temperature": temperature, "max_tokens": max_tokens},
            func=sample_func,
            config=config,
            temperature_param="temperature",
            max_tokens_param="max_tokens",
            user_id_param=None,
            session_id_param=None,
        )
    else:
        params = _extract_params(
            args=(),
            kwargs={"prompt": prompt, "temperature": temperature},
            func=sample_func,
            config=config,
            temperature_param="temperature",
            max_tokens_param="max_tokens",
            user_id_param=None,
            session_id_param=None,
        )
    
    assert params["prompt"] == prompt
    assert params["temperature"] == temperature


# =============================================================================
# Test: Response data extraction - string
# =============================================================================

@given(
    response_text=st.text(max_size=5000),
)
@settings(max_examples=50)
def test_response_extraction_string(response_text: str):
    """String responses are correctly extracted."""
    config = MonitorConfig()
    
    data = _extract_response_data(response_text, config)
    
    assert data["response_text"] == response_text
    # Tokens estimated from length
    assert data["output_tokens"] >= 0


# =============================================================================
# Test: Response data extraction - dict
# =============================================================================

@given(
    text=st.text(max_size=1000),
    input_tokens=st.integers(min_value=0, max_value=100000),
    output_tokens=st.integers(min_value=0, max_value=100000),
)
@settings(max_examples=50)
def test_response_extraction_dict(text: str, input_tokens: int, output_tokens: int):
    """Dict responses are correctly extracted."""
    config = MonitorConfig()
    
    result = {
        "text": text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "finish_reason": "stop",
    }
    
    data = _extract_response_data(result, config)
    
    assert data["response_text"] == text
    assert data["input_tokens"] == input_tokens
    assert data["output_tokens"] == output_tokens
    assert data["finish_reason"] == "stop"


# =============================================================================
# Test: None response handling
# =============================================================================

def test_none_response_handling():
    """None responses are handled gracefully."""
    config = MonitorConfig()
    
    data = _extract_response_data(None, config)
    
    assert data["response_text"] == ""
    assert data["input_tokens"] == 0
    assert data["output_tokens"] == 0


# =============================================================================
# Test: Decorator error handling
# =============================================================================

@given(
    prompt=st.text(min_size=1, max_size=200),
    error_msg=st.text(min_size=1, max_size=100),
)
@settings(max_examples=30)
def test_decorator_error_propagation(prompt: str, error_msg: str):
    """Errors are propagated correctly from decorated functions."""
    @monitor_llm(
        service_name="test-service",
        enable_tracing=False,
        enable_transmission=False,
    )
    def failing_function(prompt: str) -> str:
        raise ValueError(error_msg)
    
    with pytest.raises(ValueError, match=error_msg):
        failing_function(prompt=prompt)


# =============================================================================
# Test: Decorator with custom parameter names
# =============================================================================

@given(
    message=st.text(min_size=1, max_size=500),
    temp=st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
)
@settings(max_examples=30)
def test_decorator_custom_param_names(message: str, temp: float):
    """Decorator works with custom parameter names."""
    @monitor_llm(
        service_name="test-service",
        prompt_param="message",
        temperature_param="temp",
        enable_tracing=False,
        enable_transmission=False,
    )
    def custom_func(message: str, temp: float = 0.7) -> str:
        return f"Echo: {message}"
    
    result = custom_func(message=message, temp=temp)
    
    assert result == f"Echo: {message}"


# =============================================================================
# Test: MonitorConfig defaults
# =============================================================================

def test_monitor_config_defaults():
    """MonitorConfig has sensible defaults."""
    config = MonitorConfig()
    
    assert config.service_name == "guardianai-monitored-app"
    assert config.environment == "development"
    assert config.model == "gemini-pro"
    assert config.enable_tracing is True
    assert config.enable_transmission is True
    assert config.prompt_param == "prompt"


# =============================================================================
# Test: Decorator with extra tags
# =============================================================================

@given(
    prompt=st.text(min_size=1, max_size=200),
)
@settings(max_examples=20)
def test_decorator_with_extra_tags(prompt: str):
    """Decorator accepts and uses extra tags."""
    @monitor_llm(
        service_name="test-service",
        extra_tags={"custom_tag": "custom_value"},
        enable_tracing=False,
        enable_transmission=False,
    )
    def tagged_func(prompt: str) -> str:
        return f"Tagged: {prompt}"
    
    result = tagged_func(prompt=prompt)
    
    assert result == f"Tagged: {prompt}"


# =============================================================================
# Test: Object response with usage
# =============================================================================

def test_response_extraction_with_usage():
    """Responses with usage object are correctly extracted."""
    class MockUsage:
        prompt_tokens = 100
        completion_tokens = 50
    
    class MockResponse:
        text = "Generated text"
        usage = MockUsage()
        finish_reason = "stop"
    
    config = MonitorConfig()
    
    data = _extract_response_data(MockResponse(), config)
    
    assert data["response_text"] == "Generated text"
    assert data["input_tokens"] == 100
    assert data["output_tokens"] == 50
