# GuardianAI Datadog Monitors - Import Instructions

## Quick Import Guide

### Step 1: Go to Monitor Creation Page
Visit: https://app.datadoghq.com/monitors/create/import

### Step 2: Import Each Monitor
Import these files in order:

1. **Cost Anomaly Monitor**
   - File: `1_cost_anomaly_monitor.json`
   - Priority: P1 Critical
   - Monitors: Daily LLM costs

2. **Threat Detection Monitor**
   - File: `2_threat_detection_monitor.json`
   - Priority: P1 Critical
   - Monitors: Security threats

3. **Quality Degradation Monitor**
   - File: `3_quality_degradation_monitor.json`
   - Priority: P2 High
   - Monitors: Response quality

4. **Latency Spike Monitor**
   - File: `4_latency_spike_monitor.json`
   - Priority: P2 High
   - Monitors: Response time

5. **Error Rate Monitor**
   - File: `5_error_rate_monitor.json`
   - Priority: P2 High
   - Monitors: Request failures

### Step 3: Import Process

For each file:
1. Click "Import Monitor JSON"
2. Copy the contents of the JSON file
3. Paste into the import box
4. Click "Import"
5. Review the monitor settings
6. Click "Create"

### Step 4: Verify

After importing all 5 monitors:
1. Go to: https://app.datadoghq.com/monitors/manage
2. Filter by tag: `guardianai`
3. You should see all 5 monitors listed

## Monitor Details

| Monitor | Metric | Threshold | Priority |
|---------|--------|-----------|----------|
| Cost Anomaly | `guardianai.cost.total` | >$400k/day | P1 |
| Security Threats | `guardianai.threats.detected` | >5/min | P1 |
| Quality Degradation | `guardianai.quality.overall_score` | <0.7 | P2 |
| High Latency | `guardianai.latency.response_time` | >5000ms | P2 |
| Error Rate | `guardianai.requests.errors` | >5% | P2 |

## Configuration

All monitors use thresholds from `pipeline/config.py`:
- Can be adjusted after import
- Thresholds are configurable in each JSON file
- Update webhook URLs if needed (currently set to localhost)

## Notes

- **Webhook URLs**: Currently set to `http://localhost:8000/api/webhooks/datadog`
  - Update these after deploying your backend to production
  
- **Tags**: All monitors tagged with:
  - `guardianai` - For filtering
  - `env:development` - Environment indicator
  - Monitor type (cost, security, quality, etc.)

- **No Data**: All monitors set to NOT alert on missing data
  - Prevents false alarms during development

## Troubleshooting

**If import fails:**
1. Make sure you're copying the entire JSON content
2. Check that JSON is valid (use https://jsonlint.com/)
3. Try creating monitor manually using values from JSON

**If webhook doesn't work:**
1. Update webhook URL in monitor message to your backend URL
2. Test webhook endpoint is accessible
3. Check backend logs for webhook requests

## Next Steps

After importing all monitors:
1. ✅ Test with sample metrics
2. ✅ Configure notification channels (email, Slack)
3. ✅ Update webhook URLs for production
4. ✅ Customize thresholds if needed
