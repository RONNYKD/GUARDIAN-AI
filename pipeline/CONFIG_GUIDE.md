# Pipeline Configuration Guide

## Overview

The pipeline configuration module (`config.py`) centralizes all settings for the GuardianAI processing pipeline. It supports environment-based configuration, validation, and easy integration across all pipeline components.

## Quick Start

### Basic Usage

```python
from config import get_config

# Load configuration from environment
config = get_config()

# Access settings
print(f"Model: {config.gemini.model_name}")
print(f"Quality Threshold: {config.thresholds.quality_degradation_threshold}")
```

### Custom Configuration

```python
from config import PipelineConfig, GeminiConfig, ThresholdConfig

# Create custom configuration
config = PipelineConfig(
    gemini=GeminiConfig(
        model_name="gemini-2.0-flash",
        temperature=0.5,
        max_output_tokens=4096
    ),
    thresholds=ThresholdConfig(
        quality_degradation_threshold=0.8,
        cost_anomaly_threshold_usd=500000.0
    )
)

# Validate configuration
config.validate()
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI Studio API key | `AIzaSy...` |
| `GCP_PROJECT_ID` | Google Cloud project ID | `lovable-clone-e08db` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DD_API_KEY` | Datadog API key | (empty) |
| `DD_APP_KEY` | Datadog app key | (empty) |
| `DD_SITE` | Datadog site | `datadoghq.com` |

## Configuration Sections

### 1. Gemini Configuration

Controls Google AI Studio Gemini model settings.

```python
config.gemini.model_name          # "gemini-2.0-flash"
config.gemini.temperature         # 0.3 (0.0 = deterministic, 1.0 = creative)
config.gemini.top_p              # 0.95 (nucleus sampling)
config.gemini.top_k              # 40 (top-k sampling)
config.gemini.max_output_tokens  # 2048
config.gemini.max_retries        # 3
config.gemini.timeout_seconds    # 30
```

**When to Adjust:**
- **Temperature**: Lower (0.1-0.3) for factual analysis, higher (0.7-0.9) for creative tasks
- **Max Tokens**: Increase for longer responses, decrease for faster processing
- **Retries**: Increase for unreliable networks

### 2. Threshold Configuration

Detection and alerting thresholds.

```python
# Cost Monitoring
config.thresholds.cost_anomaly_threshold_usd  # $400,000/day
config.thresholds.cost_z_score_threshold      # 3.0 std deviations

# Latency Monitoring
config.thresholds.latency_spike_threshold_ms  # 5000ms
config.thresholds.latency_p95_threshold_ms    # 3000ms

# Quality Monitoring
config.thresholds.quality_degradation_threshold  # 0.7 (0.0-1.0)
config.thresholds.coherence_min                  # 0.6
config.thresholds.relevance_min                  # 0.6
config.thresholds.completeness_min               # 0.5

# Error Monitoring
config.thresholds.error_rate_threshold  # 0.05 (5%)

# Threat Detection
config.thresholds.threat_confidence_threshold  # 0.75
config.thresholds.toxicity_threshold          # 0.7
```

**Tuning Guidelines:**
- **Cost Threshold**: Set to 2-3x your normal daily spend
- **Quality Threshold**: Start at 0.7, adjust based on false positives
- **Threat Confidence**: Higher = fewer false positives, may miss threats

### 3. Pub/Sub Configuration

Google Cloud Pub/Sub settings.

```python
config.pubsub.telemetry_topic      # "guardianai-telemetry"
config.pubsub.incident_topic       # "guardianai-incidents"
config.pubsub.max_messages         # 100
config.pubsub.ack_deadline_seconds # 60
```

### 4. Firestore Configuration

Firestore database settings.

```python
config.firestore.telemetry_collection     # "telemetry"
config.firestore.incidents_collection     # "incidents"
config.firestore.telemetry_retention_days # 30
config.firestore.incident_retention_days  # 90
```

### 5. Datadog Configuration

Datadog integration settings.

```python
config.datadog.api_key        # From DD_API_KEY env
config.datadog.app_key        # From DD_APP_KEY env
config.datadog.metric_prefix  # "guardianai"
config.datadog.enable_alerts  # True
```

### 6. Processing Configuration

Pipeline processing behavior.

```python
config.enable_threat_detection   # True
config.enable_anomaly_detection  # True
config.enable_quality_analysis   # True
config.enable_auto_remediation   # True

config.max_concurrent_analyses  # 10 parallel Gemini requests
config.worker_threads          # 4 processing threads
config.batch_size              # 50 events per batch
```

## Configuration Presets

### Development Environment

```bash
export ENVIRONMENT=development
export GOOGLE_API_KEY=your-api-key
export GCP_PROJECT_ID=your-project
# Datadog optional in dev
```

### Staging Environment

```bash
export ENVIRONMENT=staging
export GOOGLE_API_KEY=your-api-key
export GCP_PROJECT_ID=your-project
export DD_API_KEY=your-dd-key
export DD_APP_KEY=your-dd-app-key
```

### Production Environment

```bash
export ENVIRONMENT=production
export GOOGLE_API_KEY=your-api-key
export GCP_PROJECT_ID=your-project
export DD_API_KEY=your-dd-key
export DD_APP_KEY=your-dd-app-key
export LOG_LEVEL=WARNING  # Reduce noise
```

## Validation

The configuration automatically validates on load:

```python
config = get_config()  # Validates automatically

# Manual validation
try:
    config.validate()
    print("✅ Configuration valid")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
```

**Validation Checks:**
- API keys present
- Thresholds are positive numbers
- Quality thresholds between 0 and 1
- Processing limits >= 1
- At least one AI provider configured

## Export Configuration

```python
# Export to dictionary
config_dict = config.to_dict()

# Export to JSON
import json
print(json.dumps(config_dict, indent=2))
```

## Integration Examples

### In Threat Detector

```python
from config import get_config

config = get_config()

if config.enable_threat_detection:
    threat = detect_threat(prompt)
    if threat.confidence >= config.thresholds.threat_confidence_threshold:
        create_incident(threat)
```

### In Anomaly Detector

```python
from config import get_config

config = get_config()

if cost > config.thresholds.cost_anomaly_threshold_usd:
    alert("Cost anomaly detected!")
```

### In Gemini Analyzer

```python
from config import get_config
from gemini_analyzer_aistudio import GeminiAnalyzerAIStudio

config = get_config()
analyzer = GeminiAnalyzerAIStudio()  # Auto-loads from config

# Temperature and retries come from config
result = analyzer.analyze_quality(prompt, response)
```

## Testing Configuration

Run the test script:

```bash
cd pipeline
python config.py
```

Output:
```
GuardianAI Pipeline Configuration
============================================================

Environment: development
Gemini Model: gemini-2.0-flash
Temperature: 0.3
Max Tokens: 2048

Thresholds:
  Cost Anomaly: $400,000
  Quality Min: 0.7
  Latency Max: 5000ms
  Error Rate Max: 5.0%

Features:
  Threat Detection: ✅
  Anomaly Detection: ✅
  Quality Analysis: ✅
  Auto Remediation: ✅

✅ Configuration loaded successfully!
```

## Troubleshooting

### Error: "GOOGLE_API_KEY environment variable must be set"

**Solution**: Set the API key:
```bash
export GOOGLE_API_KEY=your-key-here
```

### Error: "DD_API_KEY and DD_APP_KEY must be set"

**Solution**: Either:
1. Set Datadog keys (production)
2. Set `ENVIRONMENT=development` (dev/staging)

### Error: "quality_degradation_threshold must be between 0 and 1"

**Solution**: Fix threshold value:
```python
config.thresholds.quality_degradation_threshold = 0.7  # Not 70
```

## Advanced: Custom Config Classes

Create environment-specific configurations:

```python
from config import PipelineConfig, Environment

class ProductionConfig(PipelineConfig):
    def __init__(self):
        super().__init__()
        self.environment = Environment.PRODUCTION
        self.gemini.temperature = 0.1  # More deterministic
        self.thresholds.quality_degradation_threshold = 0.8  # Stricter
        self.enable_auto_remediation = True
        
class DevelopmentConfig(PipelineConfig):
    def __init__(self):
        super().__init__()
        self.environment = Environment.DEVELOPMENT
        self.gemini.temperature = 0.5  # More experimental
        self.enable_auto_remediation = False  # Manual review in dev
```

## Next Steps

1. **Phase 2, Task 6**: Integrate configuration into main pipeline
2. **Phase 3**: Set up Datadog monitors using threshold values
3. **Phase 6**: Add demo mode configuration
