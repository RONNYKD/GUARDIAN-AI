# GuardianAI Deployment Script for Windows (PowerShell)

$PROJECT_ID = "lovable-clone-e08db"
$REGION = "us-central1"
$SERVICE_ACCOUNT = "guraina-ai@lovable-clone-e08db.iam.gserviceaccount.com"

Write-Host "🚀 Deploying GuardianAI to Google Cloud Platform" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Set project
Write-Host "📋 Setting project to $PROJECT_ID..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Host "🔧 Enabling required APIs..." -ForegroundColor Yellow
$apis = @(
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com",
    "pubsub.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com"
)

foreach ($api in $apis) {
    gcloud services enable $api --project=$PROJECT_ID
}

Write-Host "✅ APIs enabled" -ForegroundColor Green

# Create Pub/Sub topic
Write-Host "📨 Creating Pub/Sub topic..." -ForegroundColor Yellow
gcloud pubsub topics create guardianai-telemetry --project=$PROJECT_ID 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Topic already exists" -ForegroundColor Gray
}

Write-Host "✅ Pub/Sub topic ready" -ForegroundColor Green

# Create Secret Manager secrets
Write-Host "🔐 Creating secrets in Secret Manager..." -ForegroundColor Yellow

# Datadog API Key
"45c934d165bf8d9c475f9503e64c3f3b" | gcloud secrets create guardianai-dd-api-key --data-file=- --replication-policy="automatic" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   guardianai-dd-api-key already exists" -ForegroundColor Gray
}

# Datadog App Key
"fc1b6125b152190eff1f33cc32787fa73ef2b1e7" | gcloud secrets create guardianai-dd-app-key --data-file=- --replication-policy="automatic" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   guardianai-dd-app-key already exists" -ForegroundColor Gray
}

# GCP Service Account
$credPath = "..\lovable-clone-e08db-56b9ffba4711.json"
if (Test-Path $credPath) {
    gcloud secrets create guardianai-gcp-credentials --data-file=$credPath --replication-policy="automatic" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   guardianai-gcp-credentials already exists" -ForegroundColor Gray
    }
} else {
    Write-Host "   ⚠️  Warning: Credentials file not found at $credPath" -ForegroundColor Yellow
}

Write-Host "✅ Secrets created" -ForegroundColor Green

# Grant Secret Manager permissions
Write-Host "🔑 Granting secret access permissions..." -ForegroundColor Yellow

gcloud secrets add-iam-policy-binding guardianai-dd-api-key --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor" 2>$null
gcloud secrets add-iam-policy-binding guardianai-dd-app-key --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor" 2>$null
gcloud secrets add-iam-policy-binding guardianai-gcp-credentials --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor" 2>$null

Write-Host "✅ Permissions granted" -ForegroundColor Green

# Deploy Cloud Function
Write-Host "☁️  Deploying Cloud Function..." -ForegroundColor Yellow
Push-Location pipeline

gcloud functions deploy guardianai-processor `
    --gen2 `
    --runtime=python311 `
    --region=$REGION `
    --source=. `
    --entry-point=process_telemetry `
    --trigger-topic=guardianai-telemetry `
    --service-account=$SERVICE_ACCOUNT `
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID" `
    --set-secrets="DD_API_KEY=guardianai-dd-api-key:latest,DD_APP_KEY=guardianai-dd-app-key:latest" `
    --memory=512MB `
    --timeout=540s `
    --max-instances=10

Pop-Location
Write-Host "✅ Cloud Function deployed" -ForegroundColor Green

# Deploy Backend to Cloud Run
Write-Host "🏃 Deploying Backend to Cloud Run..." -ForegroundColor Yellow

$commitSha = git rev-parse --short HEAD

gcloud builds submit --config=cloudbuild.yaml --substitutions="COMMIT_SHA=$commitSha"

Write-Host "✅ Backend deployed to Cloud Run" -ForegroundColor Green

# Get Cloud Run URL
$BACKEND_URL = gcloud run services describe guardianai-backend --region=$REGION --format='value(status.url)'

Write-Host ""
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Backend URL: $BACKEND_URL" -ForegroundColor Cyan
Write-Host "📍 Cloud Function: guardianai-processor" -ForegroundColor Cyan
Write-Host "📍 Pub/Sub Topic: guardianai-telemetry" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update frontend/.env: VITE_API_URL=$BACKEND_URL"
Write-Host "2. Build frontend: cd frontend && npm run build"
Write-Host "3. Deploy frontend to Cloud Storage or Cloud Run"
Write-Host "4. Update demo-app/.env: BACKEND_URL=$BACKEND_URL"
Write-Host ""
Write-Host "✅ GuardianAI is now running on Google Cloud!" -ForegroundColor Green
