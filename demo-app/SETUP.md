# GuardianAI Demo App - Setup Instructions

## 🚨 MANUAL STEPS REQUIRED

### Step 1: Google Cloud Platform Setup (15 minutes)

#### A. Create/Select GCP Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing one
3. Note your PROJECT_ID (e.g., `guardianai-demo-2024`)

#### B. Enable Required APIs
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativeai.googleapis.com
gcloud services enable firestore.googleapis.com
```

#### C. Create Service Account
```bash
# Create service account
gcloud iam service-accounts create guardianai-demo \
    --display-name="GuardianAI Demo Service Account"

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:guardianai-demo@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Grant Firestore User role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:guardianai-demo@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

# Download credentials JSON
gcloud iam service-accounts keys create credentials.json \
    --iam-account=guardianai-demo@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**Save `credentials.json` to `demo-app/` directory**

#### D. Enable Firestore
1. Go to [Firestore Console](https://console.cloud.google.com/firestore)
2. Click "Select Native Mode"
3. Choose region (e.g., `us-central1`)
4. Click "Create Database"

### Step 2: Get Google AI API Key (5 minutes)

#### Option 1: Google AI Studio (Easier)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Select your GCP project
4. Copy the API key

#### Option 2: Cloud Console
1. Go to APIs & Services → Credentials
2. Create Credentials → API Key
3. Restrict key to Generative Language API
4. Copy the API key

### Step 3: Datadog Setup (10 minutes)

1. **Sign up at [Datadog](https://www.datadoghq.com/)** (14-day free trial)
2. **Get API Keys:**
   - Go to Organization Settings → API Keys
   - Copy API Key
   - Go to Organization Settings → Application Keys
   - Create new Application Key
   - Copy Application Key

### Step 4: Configure Environment Variables

Create `demo-app/.env`:

```bash
# Google Cloud
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
GOOGLE_API_KEY=your-google-api-key-from-step-2
VERTEX_AI_LOCATION=us-central1

# Backend
BACKEND_URL=http://localhost:8000

# Flask
FLASK_ENV=development
FLASK_DEBUG=1
```

Create `backend/.env`:

```bash
# Google Cloud
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Datadog
DD_API_KEY=your-datadog-api-key
DD_APP_KEY=your-datadog-app-key
DD_SITE=datadoghq.com
DD_SERVICE=guardianai
DD_ENV=development

# Backend
HOST=0.0.0.0
PORT=8000
```

### Step 5: Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# SDK
cd ../sdk
pip install -e .

# Demo App
cd ../demo-app
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### Step 6: Start Services (3 terminals)

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Demo App:**
```bash
cd demo-app
python app.py
```

### Step 7: Verify Setup

1. **Backend health:** http://localhost:8000/health
   - Should return `{"status": "healthy"}`

2. **Frontend:** http://localhost:3000
   - Should show dashboard

3. **Demo app:** http://localhost:5000
   - Should show chat interface

4. **Test attack simulation:**
   - Click "Prompt Injection" in demo app
   - Check dashboard for threat detection
   - Verify incident created

## ✅ Verification Checklist

- [ ] GCP Project created
- [ ] Vertex AI API enabled
- [ ] Firestore database created
- [ ] Service account created with JSON key
- [ ] Google AI API key obtained
- [ ] Datadog account created
- [ ] All `.env` files configured
- [ ] Dependencies installed
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Demo app running on port 5000
- [ ] Can send chat messages
- [ ] Attack detection working
- [ ] Dashboard showing metrics

## 🔧 Troubleshooting

### "Permission denied" errors
- Check service account has correct roles
- Verify `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Ensure JSON key file exists

### "API not enabled"
- Run: `gcloud services enable aiplatform.googleapis.com`
- Wait 1-2 minutes for propagation

### "Connection refused" errors
- Check all services are running
- Verify port numbers match `.env` configuration
- Check firewall rules

### "No threats detected"
- Verify backend logs for errors
- Check Firestore connection
- Ensure telemetry transmission is working

## 📊 Expected Costs (Free Tier)

- **Vertex AI:** ~$0.03 per demo session (100 requests)
- **Firestore:** Free tier (1GB storage, 50K reads/day)
- **Datadog:** Free 14-day trial
- **Cloud Run:** Pay only when deployed (Phase 7)

**Total development cost: ~$0-5/day during testing**
