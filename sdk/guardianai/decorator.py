"""
GuardianAI SDK @monitor_llm Decorator

Main entry point for instrumenting LLM functions.
Implements Requirements 1.1, 1.2, 3.1, 3.2, 4.1, 4.2.
"""

import functools
import time
import asyncio
import logging
from typing import Any, Callable, Optional, TypeVar, Union, Dict
from dataclasses import dataclass

from guardianai.telemetry import TelemetryCapture, TelemetryData
from guardianai.tracer import DatadogTracer
from guardianai.transmitter import TelemetryTransmitter
from guardianai.cost import calculate_cost

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class MonitorConfig:
    """Configuration for the @monitor_llm decorator."""
    service_name: str = "guardianai-monitored-app"
    environment: str = "development"
    model: str = "gemini-pro"
    backend_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    enable_tracing: bool = True
    enable_transmission: bool = True
    auto_extract_tokens: bool = True
    prompt_param: str = "prompt"
    response_attr: Optional[str] = None
    input_tokens_attr: str = "input_tokens"
    output_tokens_attr: str = "output_tokens"


# Global instances for shared state
_global_tracer: Optional[DatadogTracer] = None
_global_transmitter: Optional[TelemetryTransmitter] = None


def get_global_tracer(config: MonitorConfig) -> DatadogTracer:
    """Get or create global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = DatadogTracer(
            service_name=config.service_name,
            environment=config.environment
        )
    return _global_tracer


def get_global_transmitter(config: MonitorConfig) -> TelemetryTransmitter:
    """Get or create global transmitter instance."""
    global _global_transmitter
    if _global_transmitter is None:
        _global_transmitter = TelemetryTransmitter(
            backend_url=config.backend_url,
            api_key=config.api_key
        )
        _global_transmitter.start()
    return _global_transmitter


def monitor_llm(
    service_name: str = "guardianai-monitored-app",
    environment: str = "development",
    model: str = "gemini-pro",
    backend_url: str = "http://localhost:8000",
    api_key: Optional[str] = None,
    enable_tracing: bool = True,
    enable_transmission: bool = True,
    prompt_param: str = "prompt",
    response_attr: Optional[str] = None,
    input_tokens_attr: str = "input_tokens",
    output_tokens_attr: str = "output_tokens",
    temperature_param: str = "temperature",
    max_tokens_param: str = "max_tokens",
    user_id_param: Optional[str] = None,
    session_id_param: Optional[str] = None,
    extra_tags: Optional[Dict[str, str]] = None,
) -> Callable[[F], F]:
    """
    Decorator to monitor LLM function calls.
    
    Automatically captures:
    - Request data (prompt, model, temperature, max_tokens, timestamp)
    - Response data (text, input tokens, output tokens, latency, cost)
    - Datadog APM traces with proper tags
    
    Implements:
    - Requirement 1.1: Complete request capture
    - Requirement 1.2: Complete response capture
    - Requirement 3.1: Unique trace IDs
    - Requirement 3.2: Trace tags
    - Requirement 4.1: Transmission within 1 second
    - Requirement 4.2: Batch transmission (max 10)
    
    Example:
        @monitor_llm(service_name="my-chatbot", model="gemini-pro")
        def generate_response(prompt: str, temperature: float = 0.7) -> str:
            response = vertex_ai.generate(prompt)
            return response
    
    Args:
        service_name: Name of the service
        environment: Environment (development, staging, production)
        model: LLM model name for cost calculation
        backend_url: GuardianAI backend URL
        api_key: API key for authentication
        enable_tracing: Enable Datadog APM tracing
        enable_transmission: Enable telemetry transmission
        prompt_param: Name of the prompt parameter
        response_attr: Attribute to extract response text (if object)
        input_tokens_attr: Attribute for input token count
        output_tokens_attr: Attribute for output token count
        temperature_param: Name of temperature parameter
        max_tokens_param: Name of max_tokens parameter
        user_id_param: Parameter name for user ID
        session_id_param: Parameter name for session ID
        extra_tags: Additional tags for traces
    
    Returns:
        Decorated function
    """
    config = MonitorConfig(
        service_name=service_name,
        environment=environment,
        model=model,
        backend_url=backend_url,
        api_key=api_key,
        enable_tracing=enable_tracing,
        enable_transmission=enable_transmission,
        prompt_param=prompt_param,
        response_attr=response_attr,
        input_tokens_attr=input_tokens_attr,
        output_tokens_attr=output_tokens_attr,
    )
    
    def decorator(func: F) -> F:
        # Check if function is async
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await _monitor_async_call(
                    func, args, kwargs, config,
                    temperature_param, max_tokens_param,
                    user_id_param, session_id_param,
                    extra_tags
                )
            return async_wrapper  # type: ignore
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return _monitor_sync_call(
                    func, args, kwargs, config,
                    temperature_param, max_tokens_param,
                    user_id_param, session_id_param,
                    extra_tags
                )
            return sync_wrapper  # type: ignore
    
    return decorator


def _extract_params(
    args: tuple,
    kwargs: dict,
    func: Callable,
    config: MonitorConfig,
    temperature_param: str,
    max_tokens_param: str,
    user_id_param: Optional[str],
    session_id_param: Optional[str],
) -> Dict[str, Any]:
    """Extract parameters from function call."""
    import inspect
    
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    params = dict(bound.arguments)
    
    # Extract prompt
    prompt = params.get(config.prompt_param, "")
    if not isinstance(prompt, str):
        prompt = str(prompt)
    
    # Extract optional params
    temperature = params.get(temperature_param, 0.7)
    max_tokens = params.get(max_tokens_param)
    user_id = params.get(user_id_param) if user_id_param else None
    session_id = params.get(session_id_param) if session_id_param else None
    
    return {
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "user_id": user_id,
        "session_id": session_id,
    }


def _extract_response_data(
    result: Any,
    config: MonitorConfig
) -> Dict[str, Any]:
    """Extract response data from function result."""
    # Default values
    response_text = ""
    input_tokens = 0
    output_tokens = 0
    finish_reason = None
    
    if result is None:
        return {
            "response_text": "",
            "input_tokens": 0,
            "output_tokens": 0,
            "finish_reason": None,
        }
    
    # Handle string response
    if isinstance(result, str):
        response_text = result
        # Estimate tokens (rough: 4 chars per token)
        output_tokens = len(result) // 4
    
    # Handle dict response
    elif isinstance(result, dict):
        response_text = result.get("text", result.get("content", str(result)))
        input_tokens = result.get(config.input_tokens_attr, 0)
        output_tokens = result.get(config.output_tokens_attr, 0)
        finish_reason = result.get("finish_reason")
    
    # Handle object response
    elif hasattr(result, config.response_attr or "text"):
        attr = config.response_attr or "text"
        response_text = getattr(result, attr, str(result))
        
        if hasattr(result, config.input_tokens_attr):
            input_tokens = getattr(result, config.input_tokens_attr, 0)
        if hasattr(result, config.output_tokens_attr):
            output_tokens = getattr(result, config.output_tokens_attr, 0)
        if hasattr(result, "finish_reason"):
            finish_reason = getattr(result, "finish_reason", None)
    
    # Handle usage wrapper
    if hasattr(result, "usage"):
        usage = result.usage
        if hasattr(usage, "prompt_tokens"):
            input_tokens = usage.prompt_tokens
        if hasattr(usage, "completion_tokens"):
            output_tokens = usage.completion_tokens
    
    return {
        "response_text": str(response_text) if response_text else "",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "finish_reason": finish_reason,
    }


def _monitor_sync_call(
    func: Callable,
    args: tuple,
    kwargs: dict,
    config: MonitorConfig,
    temperature_param: str,
    max_tokens_param: str,
    user_id_param: Optional[str],
    session_id_param: Optional[str],
    extra_tags: Optional[Dict[str, str]],
) -> Any:
    """Monitor a synchronous function call."""
    # Extract parameters
    params = _extract_params(
        args, kwargs, func, config,
        temperature_param, max_tokens_param,
        user_id_param, session_id_param
    )
    
    # Initialize components
    capture = TelemetryCapture(
        service_name=config.service_name,
        environment=config.environment,
        default_model=config.model
    )
    
    tracer = get_global_tracer(config) if config.enable_tracing else None
    transmitter = get_global_transmitter(config) if config.enable_transmission else None
    
    # Start capture
    with capture.start_capture(
        prompt=params["prompt"],
        model=config.model,
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        user_id=params.get("user_id"),
        session_id=params.get("session_id"),
        tags=extra_tags
    ) as ctx:
        # Start trace if enabled
        trace_ctx = None
        if tracer:
            trace_ctx = tracer.trace_llm_request(
                prompt=params["prompt"],
                model=config.model,
                temperature=params["temperature"],
                max_tokens=params["max_tokens"],
                **(extra_tags or {})
            )
            trace_ctx.__enter__()
        
        try:
            # Execute the function
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Extract response data
            response_data = _extract_response_data(result, config)
            
            # Record in capture
            ctx.record_response(
                response_text=response_data["response_text"],
                input_tokens=response_data["input_tokens"],
                output_tokens=response_data["output_tokens"],
                finish_reason=response_data["finish_reason"]
            )
            
            # Add trace metrics
            if trace_ctx:
                cost = calculate_cost(
                    response_data["input_tokens"],
                    response_data["output_tokens"],
                    config.model
                )
                trace_ctx.add_llm_metadata(
                    input_tokens=response_data["input_tokens"],
                    output_tokens=response_data["output_tokens"],
                    latency_ms=latency_ms,
                    cost_usd=cost
                )
            
            # Transmit telemetry
            if transmitter:
                transmitter.enqueue(ctx.to_dict())
            
            return result
            
        except Exception as e:
            ctx.record_error(str(e))
            if trace_ctx:
                trace_ctx.set_error(str(e))
            if transmitter:
                transmitter.enqueue(ctx.to_dict())
            raise
        
        finally:
            if trace_ctx:
                trace_ctx.__exit__(None, None, None)


async def _monitor_async_call(
    func: Callable,
    args: tuple,
    kwargs: dict,
    config: MonitorConfig,
    temperature_param: str,
    max_tokens_param: str,
    user_id_param: Optional[str],
    session_id_param: Optional[str],
    extra_tags: Optional[Dict[str, str]],
) -> Any:
    """Monitor an asynchronous function call."""
    # Extract parameters
    params = _extract_params(
        args, kwargs, func, config,
        temperature_param, max_tokens_param,
        user_id_param, session_id_param
    )
    
    # Initialize components
    capture = TelemetryCapture(
        service_name=config.service_name,
        environment=config.environment,
        default_model=config.model
    )
    
    tracer = get_global_tracer(config) if config.enable_tracing else None
    transmitter = get_global_transmitter(config) if config.enable_transmission else None
    
    # Start capture
    with capture.start_capture(
        prompt=params["prompt"],
        model=config.model,
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        user_id=params.get("user_id"),
        session_id=params.get("session_id"),
        tags=extra_tags
    ) as ctx:
        # Start trace if enabled
        trace_ctx = None
        if tracer:
            trace_ctx = tracer.trace_llm_request(
                prompt=params["prompt"],
                model=config.model,
                temperature=params["temperature"],
                max_tokens=params["max_tokens"],
                **(extra_tags or {})
            )
            trace_ctx.__enter__()
        
        try:
            # Execute the async function
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Extract response data
            response_data = _extract_response_data(result, config)
            
            # Record in capture
            ctx.record_response(
                response_text=response_data["response_text"],
                input_tokens=response_data["input_tokens"],
                output_tokens=response_data["output_tokens"],
                finish_reason=response_data["finish_reason"]
            )
            
            # Add trace metrics
            if trace_ctx:
                cost = calculate_cost(
                    response_data["input_tokens"],
                    response_data["output_tokens"],
                    config.model
                )
                trace_ctx.add_llm_metadata(
                    input_tokens=response_data["input_tokens"],
                    output_tokens=response_data["output_tokens"],
                    latency_ms=latency_ms,
                    cost_usd=cost
                )
            
            # Transmit telemetry
            if transmitter:
                transmitter.enqueue(ctx.to_dict())
            
            return result
            
        except Exception as e:
            ctx.record_error(str(e))
            if trace_ctx:
                trace_ctx.set_error(str(e))
            if transmitter:
                transmitter.enqueue(ctx.to_dict())
            raise
        
        finally:
            if trace_ctx:
                trace_ctx.__exit__(None, None, None)


def shutdown() -> None:
    """Shutdown global instances (call at application exit)."""
    global _global_transmitter, _global_tracer
    
    if _global_transmitter:
        _global_transmitter.stop(flush=True)
        _global_transmitter = None
    
    _global_tracer = None
    
    logger.info("GuardianAI SDK shutdown complete")
