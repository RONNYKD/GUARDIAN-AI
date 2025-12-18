# GuardianAI Deployment Guide

Complete guide for deploying GuardianAI to Google Cloud Platform.

## Prerequisites

1. **Google Cloud SDK installed**
   ```bash
   # Download from: https://cloud.google.com/sdk/docs/install
   gcloud --version
   ```

2. **Authenticated with GCP**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Docker installed** (for local testing)
   ```bash
   docker --version
   ```

4. **Git configured**
   ```bash
   git config user.name "Your Name"
   git config user.email "your@email.com"
   ```

## Architecture

```
┌─────────────┐
│   Users     │
└──────┬──────┘
       │
       ├─────────────► Frontend (Cloud Storage + CDN)
       │
       ├─────────────► Backend (Cloud Run)
       │                    │
       │                    ├──► Firestore (Database)
       │                    ├──► Vertex AI (LLM)
       │                    └──► Pub/Sub (Events)
       │                              │
       └─────────────► Demo App       └──► Cloud Function (Pipeline)
                      (Cloud Run)              │
                                              ├──► Threat Detection
                                              ├──► Anomaly Detection
                                              ├──► Quality Analysis
                                              └──► Datadog Alerts
```

## Deployment Steps

### 1. Automated Deployment (Recommended)

**Windows (PowerShell):**
```powershell
cd "d:\SENTINEL (for the google accelerator hackerthon)\guardianai-project"
.\deploy.ps1
```

**Linux/Mac (Bash):**
```bash
cd guardianai-project
chmod +x deploy.sh
./deploy.sh
```

**What it does:**
- ✅ Enables all required GCP APIs
- ✅ Creates Pub/Sub topic for telemetry
- ✅ Stores secrets in Secret Manager
- ✅ Deploys Cloud Function (pipeline)
- ✅ Builds and deploys Backend (Cloud Run)
- ✅ Configures IAM permissions

**Time:** ~10-15 minutes

### 2. Manual Deployment

#### Step 2.1: Enable APIs
```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudfunctions.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    pubsub.googleapis.com \
    secretmanager.googleapis.com
```

#### Step 2.2: Create Secrets
```bash
# Datadog API Key
echo -n "45c934d165bf8d9c475f9503e64c3f3b" | \
    gcloud secrets create guardianai-dd-api-key --data-file=-

# Datadog App Key
echo -n "fc1b6125b152190eff1f33cc32787fa73ef2b1e7" | \
    gcloud secrets create guardianai-dd-app-key --data-file=-

# GCP Credentials
gcloud secrets create guardianai-gcp-credentials \
    --data-file=lovable-clone-e08db-56b9ffba4711.json
```

#### Step 2.3: Deploy Backend
```bash
cd backend
gcloud builds submit --tag gcr.io/lovable-clone-e08db/guardianai-backend

gcloud run deploy guardianai-backend \
    --image gcr.io/lovable-clone-e08db/guardianai-backend \
    --region us-central1 \
    --allow-unauthenticated \
    --set-secrets=DD_API_KEY=guardianai-dd-api-key:latest \
    --set-secrets=DD_APP_KEY=guardianai-dd-app-key:latest
```

#### Step 2.4: Deploy Cloud Function
```bash
cd pipeline
gcloud functions deploy guardianai-processor \
    --gen2 \
    --runtime python311 \
    --region us-central1 \
    --source . \
    --entry-point process_telemetry \
    --trigger-topic guardianai-telemetry \
    --set-secrets DD_API_KEY=guardianai-dd-api-key:latest
```

#### Step 2.5: Deploy Frontend
```bash
cd frontend
npm run build

# Option A: Cloud Storage (Static hosting)
gsutil mb gs://guardianai-frontend
gsutil web set -m index.html gs://guardianai-frontend
gsutil -m cp -r dist/* gs://guardianai-frontend
gsutil iam ch allUsers:objectViewer gs://guardianai-frontend

# Option B: Cloud Run (Dynamic hosting)
gcloud run deploy guardianai-frontend \
    --source . \
    --region us-central1 \
    --allow-unauthenticated
```

## Configuration

### Update Environment Variables

After deployment, get your Cloud Run URLs:

```bash
# Get backend URL
BACKEND_URL=$(gcloud run services describe guardianai-backend \
    --region us-central1 \
    --format 'value(status.url)')

echo "Backend URL: $BACKEND_URL"
```

**Update `frontend/.env`:**
```bash
VITE_API_URL=https://your-backend-url.run.app
VITE_WS_URL=wss://your-backend-url.run.app/ws
```

**Update `demo-app/.env`:**
```bash
BACKEND_URL=https://your-backend-url.run.app
```

## Testing Deployment

### 1. Test Backend Health
```bash
curl https://your-backend-url.run.app/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2025-12-19T..."}
```

### 2. Test Cloud Function
```bash
# Send test telemetry
gcloud pubsub topics publish guardianai-telemetry \
    --message '{"trace_id":"test-123","prompt":"Hello","response":"Hi there"}'

# Check logs
gcloud functions logs read guardianai-processor --region us-central1
```

### 3. Test Frontend
Open in browser:
```
https://your-frontend-url/
```

Should show dashboard with real-time metrics.

### 4. Test Demo App
Deploy demo app:
```bash
cd demo-app
gcloud run deploy guardianai-demo \
    --source . \
    --region us-central1 \
    --allow-unauthenticated
```

## Monitoring

### Datadog Dashboard
1. Go to https://app.datadoghq.com/
2. Navigate to Dashboards
3. Search for "guardianai"
4. View metrics:
   - `guardianai.requests.total`
   - `guardianai.threats.detected`
   - `guardianai.latency.p95`
   - `guardianai.cost.total`

### Cloud Logs
```bash
# Backend logs
gcloud run services logs read guardianai-backend --region us-central1

# Function logs
gcloud functions logs read guardianai-processor --region us-central1

# Firestore operations
gcloud logging read "resource.type=firestore_database"
```

### Cloud Monitoring
```bash
# View metrics
gcloud monitoring dashboards list
```

## Costs

### Estimated Monthly Costs (Low Usage)

| Service | Usage | Cost |
|---------|-------|------|
| Cloud Run (Backend) | 100 req/day, 1 min avg | $0 (Free tier) |
| Cloud Functions | 100 executions/day | $0 (Free tier) |
| Firestore | 1GB storage, 50K reads | $0 (Free tier) |
| Vertex AI Gemini | 10K requests/month | ~$2.50 |
| Pub/Sub | 100 messages/day | $0 (Free tier) |
| Datadog | Monitoring | $0 (14-day trial) |
| **Total** | | **~$2.50/month** |

### Estimated Monthly Costs (Production)

| Service | Usage | Cost |
|---------|-------|------|
| Cloud Run (Backend) | 100K req/day | ~$15 |
| Cloud Functions | 100K executions/day | ~$10 |
| Firestore | 10GB storage, 1M reads | ~$20 |
| Vertex AI Gemini | 1M requests/month | ~$250 |
| Pub/Sub | 100K messages/day | ~$5 |
| Datadog | Pro plan | ~$15/host |
| **Total** | | **~$315/month** |

## Rollback

If deployment fails:

```bash
# Rollback Cloud Run
gcloud run services update-traffic guardianai-backend \
    --to-revisions PREVIOUS_REVISION=100

# Delete Cloud Function
gcloud functions delete guardianai-processor --region us-central1

# Delete secrets
gcloud secrets delete guardianai-dd-api-key
gcloud secrets delete guardianai-dd-app-key
```

## Troubleshooting

### Error: "Permission denied"
```bash
# Grant yourself required roles
gcloud projects add-iam-policy-binding lovable-clone-e08db \
    --member="user:your-email@gmail.com" \
    --role="roles/editor"
```

### Error: "API not enabled"
```bash
# Enable missing API
gcloud services enable [API_NAME]
```

### Error: "Secret not found"
```bash
# List secrets
gcloud secrets list

# Recreate secret
echo -n "YOUR_SECRET_VALUE" | \
    gcloud secrets create SECRET_NAME --data-file=-
```

### Backend won't start
```bash
# Check logs
gcloud run services logs read guardianai-backend --limit 50

# Check environment variables
gcloud run services describe guardianai-backend --format json
```

## Security Best Practices

1. **Use Secret Manager** for all sensitive data ✅
2. **Enable Cloud Armor** for DDoS protection
3. **Set up VPC** for private networking
4. **Enable audit logging** for compliance
5. **Rotate secrets** every 90 days
6. **Use least privilege** IAM roles
7. **Enable binary authorization** for containers

## CI/CD Pipeline

### Cloud Build Triggers

```bash
# Create trigger for main branch
gcloud builds triggers create github \
    --repo-name=guardianai \
    --repo-owner=YOUR_GITHUB_USERNAME \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml
```

### GitHub Actions (Alternative)

See `.github/workflows/deploy.yml` for GitHub Actions CI/CD setup.

## Next Steps

1. ✅ Deploy to production
2. 📊 Set up custom Datadog dashboards
3. 🔔 Configure alert policies
4. 📈 Monitor usage and costs
5. 🔒 Implement authentication (OAuth 2.0)
6. 🌍 Add custom domain
7. 📱 Create mobile app integration
8. 🤖 Add more LLM models support

## Support

- **Documentation:** See README.md in each directory
- **Issues:** GitHub Issues
- **Monitoring:** Datadog dashboards
- **Logs:** Cloud Logging console
