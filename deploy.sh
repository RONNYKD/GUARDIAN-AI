#!/bin/bash
# GuardianAI Deployment Script

set -e

PROJECT_ID="lovable-clone-e08db"
REGION="us-central1"
SERVICE_ACCOUNT="guraina-ai@lovable-clone-e08db.iam.gserviceaccount.com"

echo "🚀 Deploying GuardianAI to Google Cloud Platform"
echo "================================================"

# Set project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudfunctions.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    pubsub.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com

echo "✅ APIs enabled"

# Create Pub/Sub topic for telemetry
echo "📨 Creating Pub/Sub topic..."
gcloud pubsub topics create guardianai-telemetry --project=$PROJECT_ID || echo "Topic already exists"

echo "✅ Pub/Sub topic ready"

# Create Secret Manager secrets
echo "🔐 Creating secrets in Secret Manager..."

# Datadog API Key
echo -n "45c934d165bf8d9c475f9503e64c3f3b" | \
    gcloud secrets create guardianai-dd-api-key \
    --data-file=- \
    --replication-policy="automatic" || echo "Secret already exists"

# Datadog App Key
echo -n "fc1b6125b152190eff1f33cc32787fa73ef2b1e7" | \
    gcloud secrets create guardianai-dd-app-key \
    --data-file=- \
    --replication-policy="automatic" || echo "Secret already exists"

# GCP Service Account
gcloud secrets create guardianai-gcp-credentials \
    --data-file=../lovable-clone-e08db-56b9ffba4711.json \
    --replication-policy="automatic" || echo "Secret already exists"

echo "✅ Secrets created"

# Grant Secret Manager permissions to service account
echo "🔑 Granting secret access permissions..."
gcloud secrets add-iam-policy-binding guardianai-dd-api-key \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding guardianai-dd-app-key \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding guardianai-gcp-credentials \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

echo "✅ Permissions granted"

# Deploy Cloud Function (Telemetry Processor)
echo "☁️  Deploying Cloud Function..."
cd pipeline
gcloud functions deploy guardianai-processor \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=process_telemetry \
    --trigger-topic=guardianai-telemetry \
    --service-account=$SERVICE_ACCOUNT \
    --set-env-vars=GCP_PROJECT_ID=$PROJECT_ID \
    --set-secrets=DD_API_KEY=guardianai-dd-api-key:latest \
    --set-secrets=DD_APP_KEY=guardianai-dd-app-key:latest \
    --memory=512MB \
    --timeout=540s \
    --max-instances=10

cd ..
echo "✅ Cloud Function deployed"

# Deploy Backend to Cloud Run
echo "🏃 Deploying Backend to Cloud Run..."
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions=COMMIT_SHA=$(git rev-parse --short HEAD)

echo "✅ Backend deployed to Cloud Run"

# Get Cloud Run URL
BACKEND_URL=$(gcloud run services describe guardianai-backend \
    --region=$REGION \
    --format='value(status.url)')

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "📍 Backend URL: $BACKEND_URL"
echo "📍 Cloud Function: guardianai-processor"
echo "📍 Pub/Sub Topic: guardianai-telemetry"
echo ""
echo "Next steps:"
echo "1. Update frontend/.env with VITE_API_URL=$BACKEND_URL"
echo "2. Deploy frontend: npm run build && gcloud storage cp -r dist/* gs://guardianai-frontend/"
echo "3. Test demo app: Update BACKEND_URL in demo-app/.env"
echo ""
echo "✅ GuardianAI is now running on Google Cloud!"
