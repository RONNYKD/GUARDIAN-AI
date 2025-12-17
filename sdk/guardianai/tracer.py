"""
GuardianAI SDK Datadog Tracer

Integrates with Datadog APM for distributed tracing.
Implements Requirements 3.1 and 3.2 for trace management.
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Dict, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class SpanData:
    """
    Represents a Datadog APM span.
    
    Implements Requirement 3.2:
    - Tags must include service name, environment, model, operation type
    """
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    operation_name: str
    service_name: str
    resource_name: str
    start_time_ns: int
    duration_ns: int = 0
    status: str = "ok"
    tags: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for Datadog submission."""
        span_dict = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.operation_name,
            "service": self.service_name,
            "resource": self.resource_name,
            "start": self.start_time_ns,
            "duration": self.duration_ns,
            "meta": self.tags,
            "metrics": self.metrics,
        }
        
        if self.parent_id:
            span_dict["parent_id"] = self.parent_id
        
        if self.error:
            span_dict["error"] = 1
            span_dict["meta"]["error.message"] = self.error
        
        return span_dict


class DatadogTracer:
    """
    Datadog APM tracer for LLM operations.
    
    Creates and manages traces for LLM requests with proper
    parent-child span relationships.
    
    Implements Requirement 3.1: Every request gets unique trace_id.
    Implements Requirement 3.2: Traces include required tags.
    
    Example:
        >>> tracer = DatadogTracer(service_name="my-llm-app")
        >>> with tracer.start_span("llm.generate") as span:
        ...     response = llm.generate(prompt)
        ...     span.set_tag("model", "gemini-pro")
    """
    
    def __init__(
        self,
        service_name: str = "guardianai-monitored-app",
        environment: str = "development",
        dd_agent_host: str = "localhost",
        dd_agent_port: int = 8126,
        enabled: bool = True
    ) -> None:
        """
        Initialize Datadog tracer.
        
        Args:
            service_name: Name of the service
            environment: Environment (dev, staging, prod)
            dd_agent_host: Datadog agent hostname
            dd_agent_port: Datadog agent port
            enabled: Whether tracing is enabled
        """
        self.service_name = service_name
        self.environment = environment
        self.dd_agent_host = dd_agent_host
        self.dd_agent_port = dd_agent_port
        self.enabled = enabled
        
        self._active_traces: Dict[str, List[SpanData]] = {}
        self._trace_counter = 0
        self._span_counter = 0
        
        # Try to initialize Datadog tracer if available
        self._dd_tracer = None
        try:
            from ddtrace import tracer
            self._dd_tracer = tracer
            logger.info("Datadog tracer initialized")
        except ImportError:
            logger.warning("ddtrace not installed, using mock tracing")
    
    def generate_trace_id(self) -> str:
        """
        Generate a unique trace ID.
        
        Implements Requirement 3.1: Every request gets unique trace_id.
        
        Returns:
            Unique trace ID string
        """
        self._trace_counter += 1
        unique_part = uuid.uuid4().hex[:16]
        return f"trace_{unique_part}_{self._trace_counter}"
    
    def generate_span_id(self) -> str:
        """
        Generate a unique span ID.
        
        Returns:
            Unique span ID string
        """
        self._span_counter += 1
        unique_part = uuid.uuid4().hex[:8]
        return f"span_{unique_part}_{self._span_counter}"
    
    def _get_current_time_ns(self) -> int:
        """Get current time in nanoseconds."""
        return int(time.time() * 1e9)
    
    @contextmanager
    def start_trace(
        self,
        operation_name: str = "llm.request",
        resource_name: str = "generate",
        model: Optional[str] = None,
        **tags: str
    ):
        """
        Start a new trace with root span.
        
        Args:
            operation_name: Name of the operation
            resource_name: Resource being accessed
            model: LLM model name
            **tags: Additional tags
        
        Yields:
            SpanContext for managing the trace
        """
        trace_id = self.generate_trace_id()
        span_id = self.generate_span_id()
        
        # Build required tags per Requirement 3.2
        span_tags = {
            "service": self.service_name,
            "environment": self.environment,
            "operation.type": "llm",
        }
        
        if model:
            span_tags["model"] = model
        
        span_tags.update(tags)
        
        span = SpanData(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=None,
            operation_name=operation_name,
            service_name=self.service_name,
            resource_name=resource_name,
            start_time_ns=self._get_current_time_ns(),
            tags=span_tags
        )
        
        self._active_traces[trace_id] = [span]
        
        context = SpanContext(self, span)
        
        try:
            yield context
        except Exception as e:
            span.error = str(e)
            span.status = "error"
            raise
        finally:
            span.duration_ns = self._get_current_time_ns() - span.start_time_ns
            self._submit_trace(trace_id)
    
    @contextmanager
    def start_span(
        self,
        operation_name: str,
        resource_name: Optional[str] = None,
        parent_trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        **tags: str
    ):
        """
        Start a new span, optionally as child of existing span.
        
        Args:
            operation_name: Name of the operation
            resource_name: Resource name
            parent_trace_id: Parent trace ID for child spans
            parent_span_id: Parent span ID
            **tags: Additional tags
        
        Yields:
            SpanContext for managing the span
        """
        if parent_trace_id and parent_trace_id in self._active_traces:
            trace_id = parent_trace_id
        else:
            trace_id = self.generate_trace_id()
            self._active_traces[trace_id] = []
        
        span_id = self.generate_span_id()
        
        span_tags = {
            "service": self.service_name,
            "environment": self.environment,
        }
        span_tags.update(tags)
        
        span = SpanData(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=parent_span_id,
            operation_name=operation_name,
            service_name=self.service_name,
            resource_name=resource_name or operation_name,
            start_time_ns=self._get_current_time_ns(),
            tags=span_tags
        )
        
        self._active_traces[trace_id].append(span)
        
        context = SpanContext(self, span)
        
        try:
            yield context
        except Exception as e:
            span.error = str(e)
            span.status = "error"
            raise
        finally:
            span.duration_ns = self._get_current_time_ns() - span.start_time_ns
    
    def _submit_trace(self, trace_id: str) -> None:
        """Submit trace to Datadog agent."""
        if not self.enabled:
            return
        
        spans = self._active_traces.pop(trace_id, [])
        
        if not spans:
            return
        
        if self._dd_tracer:
            # Real Datadog submission would go here
            logger.debug(f"Submitting trace {trace_id} with {len(spans)} spans")
        else:
            # Mock submission for testing
            logger.debug(f"Mock: Would submit trace {trace_id}")
    
    def trace_llm_request(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """
        Create a trace for an LLM request.
        
        Convenience method that sets up common LLM tags.
        
        Args:
            prompt: The prompt text
            model: Model name
            temperature: Temperature setting
            max_tokens: Max tokens
            **kwargs: Additional tags
        
        Returns:
            Context manager for the trace
        """
        tags = {
            "model": model,
            "temperature": str(temperature),
            "prompt_length": str(len(prompt)),
        }
        
        if max_tokens:
            tags["max_tokens"] = str(max_tokens)
        
        tags.update({k: str(v) for k, v in kwargs.items()})
        
        return self.start_trace(
            operation_name="llm.generate",
            resource_name=f"{model}.generate",
            **tags
        )
    
    def create_span_link(
        self,
        source_trace_id: str,
        source_span_id: str,
        target_trace_id: str,
        target_span_id: str,
        link_type: str = "follows_from"
    ) -> Dict[str, str]:
        """
        Create a link between spans for distributed tracing.
        
        Args:
            source_trace_id: Source trace ID
            source_span_id: Source span ID
            target_trace_id: Target trace ID
            target_span_id: Target span ID
            link_type: Type of relationship
        
        Returns:
            Link metadata
        """
        return {
            "source_trace_id": source_trace_id,
            "source_span_id": source_span_id,
            "target_trace_id": target_trace_id,
            "target_span_id": target_span_id,
            "link_type": link_type
        }


class SpanContext:
    """
    Context for managing an active span.
    
    Provides methods to add tags, metrics, and mark errors.
    """
    
    def __init__(self, tracer: DatadogTracer, span: SpanData) -> None:
        """Initialize with tracer and span."""
        self.tracer = tracer
        self.span = span
    
    @property
    def trace_id(self) -> str:
        """Get the trace ID."""
        return self.span.trace_id
    
    @property
    def span_id(self) -> str:
        """Get the span ID."""
        return self.span.span_id
    
    def set_tag(self, key: str, value: str) -> None:
        """Add a tag to the span."""
        self.span.tags[key] = str(value)
    
    def set_tags(self, tags: Dict[str, str]) -> None:
        """Add multiple tags to the span."""
        for key, value in tags.items():
            self.set_tag(key, value)
    
    def set_metric(self, key: str, value: float) -> None:
        """Add a metric to the span."""
        self.span.metrics[key] = value
    
    def set_metrics(self, metrics: Dict[str, float]) -> None:
        """Add multiple metrics to the span."""
        for key, value in metrics.items():
            self.set_metric(key, value)
    
    def set_error(self, error: str) -> None:
        """Mark the span as errored."""
        self.span.error = error
        self.span.status = "error"
        self.span.tags["error.message"] = error
    
    def set_resource(self, resource: str) -> None:
        """Set the resource name."""
        self.span.resource_name = resource
    
    def add_llm_metadata(
        self,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        cost_usd: float
    ) -> None:
        """
        Add common LLM metrics to the span.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Latency in milliseconds
            cost_usd: Cost in USD
        """
        self.set_metrics({
            "llm.input_tokens": float(input_tokens),
            "llm.output_tokens": float(output_tokens),
            "llm.total_tokens": float(input_tokens + output_tokens),
            "llm.latency_ms": latency_ms,
            "llm.cost_usd": cost_usd,
        })
    
    def finish(self) -> None:
        """Finish the span, calculating duration."""
        self.span.duration_ns = (
            self.tracer._get_current_time_ns() - self.span.start_time_ns
        )


def get_required_tags(
    service_name: str,
    environment: str,
    model: str,
    operation_type: str = "llm"
) -> Dict[str, str]:
    """
    Get required tags per Requirement 3.2.
    
    Args:
        service_name: Name of the service
        environment: Environment name
        model: Model identifier
        operation_type: Type of operation
    
    Returns:
        Dict with required tags
    """
    return {
        "service": service_name,
        "environment": environment,
        "model": model,
        "operation.type": operation_type,
    }
