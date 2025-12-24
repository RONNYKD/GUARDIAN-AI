# Datadog Monitors Setup Guide

## Phase 3: Datadog Monitors for GuardianAI

This guide explains how to set up automated monitoring and alerting using Datadog.

## Prerequisites

1. **Datadog Account** - Sign up at https://www.datadoghq.com/
2. **API Credentials** - Get from https://app.datadoghq.com/organization-settings/api-keys

## Quick Start

### 1. Set Up Datadog Credentials

```bash
# On Windows PowerShell
$env:DD_API_KEY="your-datadog-api-key-here"
$env:DD_APP_KEY="your-datadog-application-key-here"
$env:DD_SITE="datadoghq.com"  # Optional, default is datadoghq.com

# On Linux/Mac
export DD_API_KEY="your-datadog-api-key-here"
export DD_APP_KEY="your-datadog-application-key-here"
export DD_SITE="datadoghq.com"
```

### 2. Create All Monitors

```bash
cd pipeline
python datadog_monitors.py
# Choose option 1 to create all monitors
```

### 3. Verify in Datadog UI

Visit https://app.datadoghq.com/monitors/manage and look for:
- `[GuardianAI] Cost Anomaly Alert`
- `[GuardianAI] Security Threat Detection Alert`
- `[GuardianAI] Quality Degradation Alert`
- `[GuardianAI] High Latency Alert`
- `[GuardianAI] High Error Rate Alert`

## Monitor Details

### 1. Cost Anomaly Monitor

- **Threshold:** $400,000/day (configurable in `config.py`)
- **Warning:** 75% of threshold
- **Priority:** P1 Critical
- **Metric:** `guardianai.cost.total`
- **Query:** `sum(last_1d):sum:guardianai.cost.total{*} > 400000`

**What it detects:**
- Runaway LLM costs
- Cost spikes from unexpected traffic
- Budget overruns

**Action Items:**
- Review high-cost API calls
- Check for loops or automated abuse
- Implement rate limiting

### 2. Security Threat Detection Monitor

- **Threshold:** 5 threats/minute
- **Priority:** P1 Critical
- **Metric:** `guardianai.threats.detected`
- **Query:** `sum(last_1m):sum:guardianai.threats.detected{severity:high OR severity:critical}.as_rate() > 5`

**What it detects:**
- Prompt injection attacks
- Jailbreak attempts
- Toxic content generation
- PII leaks

**Action Items:**
- Enable rate limiting
- Block malicious users
- Review security logs
- Notify security team

### 3. Quality Degradation Monitor

- **Threshold:** Quality score < 0.7 (configurable)
- **Warning:** Quality score < 0.8
- **Priority:** P2 High
- **Metric:** `guardianai.quality.overall_score`
- **Query:** `avg(last_5m):avg:guardianai.quality.overall_score{*} < 0.7`

**What it detects:**
- Poor LLM response quality
- Model configuration issues
- Prompt engineering problems

**Action Items:**
- Review recent responses
- Check model configuration
- Verify prompt templates
- Test with sample prompts

### 4. High Latency Monitor

- **Threshold:** 5000ms (P95 latency)
- **Warning:** 4000ms
- **Priority:** P2 High
- **Metric:** `guardianai.latency.response_time`
- **Query:** `avg(last_5m):p95:guardianai.latency.response_time{*} > 5000`

**What it detects:**
- Slow LLM responses
- API performance issues
- Network problems
- Queue buildup

**Action Items:**
- Check model provider status
- Optimize prompt lengths
- Implement caching
- Use faster models

### 5. Error Rate Monitor

- **Threshold:** 5% error rate
- **Warning:** 3.75% error rate
- **Priority:** P2 High
- **Metric:** `guardianai.requests.errors`
- **Query:** `avg(last_5m):(sum:guardianai.requests.errors{*}.as_count() / sum:guardianai.requests.total{*}.as_count()) * 100 > 5`

**What it detects:**
- Model API failures
- Authentication issues
- Rate limiting
- Invalid requests

**Action Items:**
- Check error logs
- Verify API credentials
- Review request validation
- Implement retry logic

## Configuration

All monitor thresholds are configurable in `pipeline/config.py`:

```python
@dataclass
class ThresholdConfig:
    """Detection thresholds for pipeline."""
    
    # Cost anomaly detection
    cost_anomaly_threshold_usd: float = 400_000
    
    # Quality thresholds
    quality_degradation_threshold: float = 0.7
    coherence_min: float = 0.6
    relevance_min: float = 0.6
    completeness_min: float = 0.5
    
    # Performance thresholds
    latency_spike_threshold_ms: int = 5_000
    latency_p95_threshold_ms: int = 2_000
    
    # Error rate threshold
    error_rate_threshold: float = 0.05  # 5%
    
    # Threat detection
    threat_confidence_threshold: float = 0.75
```

To modify thresholds:

1. Edit `pipeline/config.py`
2. Set environment variables (overrides config):
   ```bash
   export COST_ANOMALY_THRESHOLD_USD=500000
   export QUALITY_DEGRADATION_THRESHOLD=0.8
   export LATENCY_SPIKE_THRESHOLD_MS=3000
   ```
3. Delete and recreate monitors with new thresholds

## Managing Monitors

### List Existing Monitors

```bash
cd pipeline
python datadog_monitors.py
# Choose option 3 for summary
```

### Delete All Monitors

```bash
cd pipeline
python datadog_monitors.py
# Choose option 2, then confirm with 'yes'
```

### Update Monitor Thresholds

1. Delete existing monitors
2. Update `config.py` or environment variables
3. Recreate monitors

## Testing Monitors

### 1. Send Test Metrics

```python
from datadog import initialize, statsd

initialize(
    api_key=os.getenv("DD_API_KEY"),
    app_key=os.getenv("DD_APP_KEY")
)

# Test cost monitor
statsd.gauge("guardianai.cost.total", 500000)

# Test threat monitor
statsd.increment("guardianai.threats.detected", tags=["severity:high"])

# Test quality monitor
statsd.gauge("guardianai.quality.overall_score", 0.5)

# Test latency monitor
statsd.histogram("guardianai.latency.response_time", 6000)

# Test error rate
statsd.increment("guardianai.requests.total")
statsd.increment("guardianai.requests.errors")
```

### 2. Trigger Alerts

The easiest way to test is to send metrics that exceed thresholds:

```bash
# Install datadog library
pip install datadog

# Run test script (create one based on above)
python test_monitors.py
```

### 3. Verify Webhooks

Check that webhook endpoint is accessible:

```bash
curl -X POST http://localhost:8000/api/webhooks/datadog \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Alert",
    "body": "Testing webhook integration",
    "tags": ["guardianai", "test"]
  }'
```

## Integration with Pipeline

The monitors automatically work with the GuardianAI processing pipeline:

1. **Pipeline sends metrics** via `alert_manager.py`:
   ```python
   statsd.gauge("guardianai.quality.overall_score", quality_score)
   statsd.increment("guardianai.threats.detected", tags=[f"severity:{severity}"])
   statsd.histogram("guardianai.latency.response_time", latency_ms)
   statsd.increment("guardianai.cost.total", cost_usd)
   ```

2. **Datadog monitors evaluate queries** every 1-5 minutes

3. **Alerts trigger webhooks** to `/api/webhooks/datadog/alert`

4. **Backend creates incidents** in Firestore and takes action

## Webhook Integration

### Backend Endpoint

The monitors send alerts to:
```
http://your-backend-url/api/webhooks/datadog/alert
```

Update `pipeline/datadog_monitors.py` to set your backend URL:

```python
# In DatadogMonitorSetup.__init__()
self.webhook_url = "https://your-backend.run.app/api/webhooks/datadog"
```

### Webhook Payload

Datadog sends alerts with:

```json
{
  "title": "[GuardianAI] Cost Anomaly Alert",
  "body": "Daily LLM costs have exceeded $400,000",
  "tags": ["guardianai", "cost", "anomaly", "env:production"],
  "alert_type": "error",
  "priority": "normal",
  "monitor": {
    "id": 123456,
    "name": "[GuardianAI] Cost Anomaly Alert",
    "query": "sum(last_1d):sum:guardianai.cost.total{*} > 400000"
  }
}
```

## Production Deployment

### Cloud Functions

If deploying pipeline as Cloud Function:

1. Add Datadog credentials to Secret Manager:
   ```bash
   echo -n "your-dd-api-key" | gcloud secrets create dd-api-key --data-file=-
   echo -n "your-dd-app-key" | gcloud secrets create dd-app-key --data-file=-
   ```

2. Grant access to Cloud Function:
   ```bash
   gcloud secrets add-iam-policy-binding dd-api-key \
     --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"
   
   gcloud secrets add-iam-policy-binding dd-app-key \
     --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. Update Cloud Function environment:
   ```yaml
   env_variables:
     DD_API_KEY: "projects/PROJECT_ID/secrets/dd-api-key/versions/latest"
     DD_APP_KEY: "projects/PROJECT_ID/secrets/dd-app-key/versions/latest"
   ```

### Cloud Run

If deploying as Cloud Run:

```bash
gcloud run deploy guardianai-backend \
  --set-secrets="DD_API_KEY=dd-api-key:latest,DD_APP_KEY=dd-app-key:latest"
```

## Troubleshooting

### Monitors Not Creating

**Error:** `Failed to create monitors: 403 Forbidden`

**Solution:** Check API key permissions:
- API Key must have `monitors_write` permission
- Application Key must have `monitors_write` permission

### No Metrics Showing

**Error:** Monitors created but no data

**Solution:** Verify metrics are being sent:
```python
# Check statsd configuration
from datadog import initialize, statsd
initialize(statsd_host="127.0.0.1", statsd_port=8125)
```

### Webhooks Not Triggering

**Error:** Alerts fire but webhook not called

**Solution:** 
1. Check webhook URL is accessible from Datadog
2. Verify `@webhook-URL` in monitor message
3. Test webhook endpoint manually

### Wrong Thresholds

**Error:** Monitors trigger too often/rarely

**Solution:**
1. Review actual metric values in Datadog
2. Adjust thresholds in `config.py`
3. Delete and recreate monitors

## Next Steps

After setting up monitors:

1. ✅ **Verify monitors created** - Check Datadog UI
2. ✅ **Test with sample data** - Send test metrics
3. ✅ **Configure webhook endpoint** - Set up backend receiver
4. ✅ **Set up alerting channels** - Add email/Slack/PagerDuty
5. ✅ **Document runbooks** - Create incident response procedures

## Human Intervention Required

⚠️ **You need to manually:**

1. **Create Datadog account** at https://www.datadoghq.com/
2. **Generate API credentials**:
   - Go to https://app.datadoghq.com/organization-settings/api-keys
   - Create new API Key (for sending metrics)
   - Create new Application Key (for managing monitors)
3. **Set environment variables** with your credentials
4. **Run setup script**: `python datadog_monitors.py`
5. **Update webhook URL** in code to point to your backend
6. **Test integration** by sending sample metrics
7. **Configure alert channels** (email, Slack, etc.) in Datadog UI

## Resources

- [Datadog Monitors Documentation](https://docs.datadoghq.com/monitors/)
- [Datadog API Reference](https://docs.datadoghq.com/api/latest/monitors/)
- [GuardianAI Configuration Guide](CONFIG_GUIDE.md)
- [Backend API Documentation](../backend/README.md)
