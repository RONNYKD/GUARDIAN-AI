# GuardianAI SDK

Zero-friction LLM monitoring and observability for Python applications.

## Features

- **Simple Decorator**: Add `@monitor_llm` to any LLM function
- **Automatic Telemetry**: Captures prompts, responses, tokens, latency, cost
- **Datadog Integration**: APM tracing with proper service tags
- **Async Support**: Works with both sync and async functions
- **Cost Tracking**: Accurate cost calculation based on model pricing

## Installation

```bash
pip install guardianai-sdk
```

## Quick Start

```python
from guardianai import monitor_llm

@monitor_llm(service_name="my-chatbot", model="gemini-pro")
def generate_response(prompt: str, temperature: float = 0.7) -> str:
    # Your LLM call here
    response = vertex_ai.generate(prompt, temperature=temperature)
    return response.text

# Use as normal - telemetry is captured automatically
response = generate_response("Hello, how can I help?")
```

## Configuration

```python
@monitor_llm(
    service_name="my-app",           # Service name for tracing
    environment="production",         # Environment tag
    model="gemini-pro",              # Model for cost calculation
    backend_url="https://api.guardianai.example.com",  # Backend URL
    api_key="your-api-key",          # API key for auth
    enable_tracing=True,             # Enable Datadog APM
    enable_transmission=True,        # Enable telemetry transmission
)
def my_llm_function(prompt: str) -> str:
    ...
```

## Captured Data

### Request (Requirement 1.1)
- Prompt text
- Model identifier
- Temperature parameter
- Max tokens parameter
- Request timestamp

### Response (Requirement 1.2)
- Complete response text
- Input token count
- Output token count
- Total latency (ms)
- Calculated cost (USD)

### Traces (Requirements 3.1, 3.2)
- Unique trace ID per request
- Tags: service, environment, model, operation type

## Cost Calculation

```python
from guardianai import calculate_cost

# Calculate cost for Gemini Pro
cost = calculate_cost(
    input_tokens=1000,
    output_tokens=500,
    model="gemini-pro"
)
print(f"Cost: ${cost:.4f}")  # $0.5000
```

## Async Support

```python
@monitor_llm(service_name="my-async-app")
async def generate_async(prompt: str) -> str:
    response = await async_llm.generate(prompt)
    return response.text
```

## Shutdown

```python
from guardianai import shutdown

# Call at application exit to flush remaining telemetry
shutdown()
```

## License

MIT License
