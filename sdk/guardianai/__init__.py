"""
GuardianAI SDK

A zero-friction instrumentation library for LLM applications.

Features:
- Automatic telemetry capture via decorators
- Datadog APM tracing integration
- Async telemetry transmission
- Cost calculation for token usage

Example:
    from guardianai import monitor_llm
    
    @monitor_llm(service_name="my-chatbot")
    def generate_response(prompt: str) -> str:
        response = llm.generate(prompt)
        return response
"""

from guardianai.decorator import monitor_llm
from guardianai.telemetry import TelemetryCapture
from guardianai.tracer import DatadogTracer
from guardianai.transmitter import TelemetryTransmitter
from guardianai.cost import CostCalculator, calculate_cost

__version__ = "0.1.0"
__all__ = [
    "monitor_llm",
    "TelemetryCapture",
    "DatadogTracer",
    "TelemetryTransmitter",
    "CostCalculator",
    "calculate_cost",
]
