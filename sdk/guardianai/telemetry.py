"""
GuardianAI SDK Telemetry Capture

Captures telemetry data from LLM function calls.
Implements Requirements 1.1 and 1.2 for complete request/response capture.
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Callable
import logging
import inspect

from guardianai.cost import calculate_cost

logger = logging.getLogger(__name__)


@dataclass
class RequestCapture:
    """
    Captured request data.
    
    Implements Requirement 1.1:
    - prompt text
    - model identifier
    - temperature parameter
    - max_tokens parameter
    - request timestamp
    """
    prompt: str
    model: str
    temperature: float
    max_tokens: Optional[int]
    timestamp: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseCapture:
    """
    Captured response data.
    
    Implements Requirement 1.2:
    - complete response text
    - input token count
    - output token count
    - total latency in milliseconds
    - calculated cost
    """
    response_text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    finish_reason: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TelemetryData:
    """Complete telemetry record combining request and response."""
    trace_id: str
    span_id: str
    request: RequestCapture
    response: Optional[ResponseCapture]
    service_name: str
    environment: str
    status: str = "success"
    tags: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for transmission."""
        data = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "timestamp": self.request.timestamp,
            "prompt": self.request.prompt,
            "model": self.request.model,
            "temperature": self.request.temperature,
            "max_tokens": self.request.max_tokens,
            "user_id": self.request.user_id,
            "session_id": self.request.session_id,
            "service_name": self.service_name,
            "environment": self.environment,
            "status": self.status,
            "tags": self.tags,
        }
        
        if self.response:
            data.update({
                "response_text": self.response.response_text,
                "input_tokens": self.response.input_tokens,
                "output_tokens": self.response.output_tokens,
                "latency_ms": self.response.latency_ms,
                "cost_usd": self.response.cost_usd,
                "finish_reason": self.response.finish_reason,
                "error": self.response.error,
            })
        
        return data


class TelemetryCapture:
    """
    Captures telemetry from LLM function calls.
    
    Intercepts function entry/exit to capture:
    - Request parameters (prompt, model, temperature, etc.)
    - Response data (text, tokens, latency, cost)
    - Execution metadata (timing, errors)
    
    Example:
        >>> capture = TelemetryCapture(service_name="my-app")
        >>> with capture.start_capture(prompt="Hello", model="gemini-pro") as ctx:
        ...     response = llm.generate(prompt)
        ...     ctx.record_response(response)
    """
    
    def __init__(
        self,
        service_name: str = "guardianai-monitored-app",
        environment: str = "development",
        default_model: str = "gemini-pro"
    ) -> None:
        """
        Initialize telemetry capture.
        
        Args:
            service_name: Name of the monitored service
            environment: Environment (development, staging, production)
            default_model: Default model for pricing
        """
        self.service_name = service_name
        self.environment = environment
        self.default_model = default_model
        self._active_captures: dict[str, TelemetryData] = {}
    
    def generate_trace_id(self) -> str:
        """Generate a unique trace ID."""
        return f"trace_{uuid.uuid4().hex[:16]}"
    
    def generate_span_id(self) -> str:
        """Generate a unique span ID."""
        return f"span_{uuid.uuid4().hex[:8]}"
    
    def capture_request(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: Any
    ) -> RequestCapture:
        """
        Capture request data.
        
        Implements Requirement 1.1: Complete request capture.
        
        Args:
            prompt: The prompt text
            model: Model identifier
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            user_id: Optional user identifier
            session_id: Optional session identifier
            **kwargs: Additional parameters
        
        Returns:
            RequestCapture with all request data
        """
        return RequestCapture(
            prompt=prompt,
            model=model or self.default_model,
            temperature=temperature,
            max_tokens=max_tokens,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            session_id=session_id,
            additional_params=kwargs
        )
    
    def capture_response(
        self,
        response_text: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        model: str = "gemini-pro",
        finish_reason: Optional[str] = None,
        error: Optional[str] = None
    ) -> ResponseCapture:
        """
        Capture response data.
        
        Implements Requirement 1.2: Complete response capture.
        
        Args:
            response_text: Complete response text
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Total latency in milliseconds
            model: Model name for cost calculation
            finish_reason: Model's finish reason
            error: Error message if failed
        
        Returns:
            ResponseCapture with all response data
        """
        cost = calculate_cost(input_tokens, output_tokens, model)
        
        return ResponseCapture(
            response_text=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=cost,
            finish_reason=finish_reason,
            error=error
        )
    
    def start_capture(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[dict[str, str]] = None,
        **kwargs: Any
    ) -> "CaptureContext":
        """
        Start a capture context for an LLM call.
        
        Returns a context manager that tracks timing and captures response.
        
        Args:
            prompt: The prompt text
            model: Model identifier
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            user_id: User identifier
            session_id: Session identifier
            tags: Additional tags
            **kwargs: Extra parameters
        
        Returns:
            CaptureContext for use with 'with' statement
        """
        trace_id = self.generate_trace_id()
        span_id = self.generate_span_id()
        
        request = self.capture_request(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            user_id=user_id,
            session_id=session_id,
            **kwargs
        )
        
        telemetry = TelemetryData(
            trace_id=trace_id,
            span_id=span_id,
            request=request,
            response=None,
            service_name=self.service_name,
            environment=self.environment,
            tags=tags or {}
        )
        
        return CaptureContext(self, telemetry)
    
    def extract_params_from_call(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict
    ) -> dict[str, Any]:
        """
        Extract relevant parameters from a function call.
        
        Inspects function signature to map args to parameter names.
        
        Args:
            func: The function being called
            args: Positional arguments
            kwargs: Keyword arguments
        
        Returns:
            Dict with extracted parameters
        """
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        
        params = dict(bound.arguments)
        
        # Map common parameter names
        result = {}
        
        # Look for prompt-like parameters
        for name in ["prompt", "message", "text", "input", "query", "content"]:
            if name in params:
                result["prompt"] = str(params[name])
                break
        
        # Look for model parameter
        for name in ["model", "model_name", "model_id"]:
            if name in params:
                result["model"] = str(params[name])
                break
        
        # Look for temperature
        if "temperature" in params:
            result["temperature"] = float(params["temperature"])
        
        # Look for max_tokens
        for name in ["max_tokens", "max_output_tokens", "max_length"]:
            if name in params:
                result["max_tokens"] = int(params[name])
                break
        
        return result


class CaptureContext:
    """
    Context manager for capturing a single LLM call.
    
    Tracks start time and provides methods to record response.
    
    Example:
        >>> with capture.start_capture(prompt="Hello") as ctx:
        ...     response = llm.generate(prompt)
        ...     ctx.record_response(response.text, response.usage)
    """
    
    def __init__(
        self,
        capture: TelemetryCapture,
        telemetry: TelemetryData
    ) -> None:
        """Initialize context with capture instance and telemetry."""
        self.capture = capture
        self.telemetry = telemetry
        self.start_time: float = 0
        self.end_time: float = 0
    
    @property
    def trace_id(self) -> str:
        """Get the trace ID for this capture."""
        return self.telemetry.trace_id
    
    @property
    def span_id(self) -> str:
        """Get the span ID for this capture."""
        return self.telemetry.span_id
    
    def __enter__(self) -> "CaptureContext":
        """Start timing when entering context."""
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop timing when exiting context."""
        self.end_time = time.perf_counter()
        
        if exc_type is not None:
            # Record error if exception occurred
            self.telemetry.status = "error"
            if self.telemetry.response is None:
                self.telemetry.response = ResponseCapture(
                    response_text="",
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=self.get_latency_ms(),
                    cost_usd=0,
                    error=str(exc_val)
                )
    
    def get_latency_ms(self) -> float:
        """Calculate elapsed time in milliseconds."""
        if self.end_time == 0:
            self.end_time = time.perf_counter()
        return (self.end_time - self.start_time) * 1000
    
    def record_response(
        self,
        response_text: str,
        input_tokens: int,
        output_tokens: int,
        finish_reason: Optional[str] = None
    ) -> None:
        """
        Record response data.
        
        Args:
            response_text: The complete response text
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            finish_reason: Model's finish reason
        """
        latency_ms = self.get_latency_ms()
        
        self.telemetry.response = self.capture.capture_response(
            response_text=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            model=self.telemetry.request.model,
            finish_reason=finish_reason
        )
    
    def record_error(self, error: str) -> None:
        """Record an error that occurred during the call."""
        self.telemetry.status = "error"
        self.telemetry.response = ResponseCapture(
            response_text="",
            input_tokens=0,
            output_tokens=0,
            latency_ms=self.get_latency_ms(),
            cost_usd=0,
            error=error
        )
    
    def get_telemetry(self) -> TelemetryData:
        """Get the complete telemetry data."""
        return self.telemetry
    
    def to_dict(self) -> dict[str, Any]:
        """Get telemetry as dictionary."""
        return self.telemetry.to_dict()
