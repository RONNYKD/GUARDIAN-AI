# GuardianAI - Complete User Guide

**Enterprise LLM Security, Cost Optimization & Quality Monitoring Platform**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Getting Started - Setup Flow](#getting-started---setup-flow)
4. [User Flow - Monitoring Your LLM](#user-flow---monitoring-your-llm)
5. [Frontend UI Guide](#frontend-ui-guide)
6. [Backend API Reference](#backend-api-reference)
7. [Integration Guide](#integration-guide)
8. [Demo Mode](#demo-mode)

---

## 🎯 System Overview

### What is GuardianAI?

GuardianAI is a comprehensive monitoring and security platform for production Large Language Model (LLM) applications. It provides:

- **🛡️ Security Threat Detection** - Identifies prompt injection, jailbreaks, PII leaks, and toxic content in real-time
- **💰 Cost Optimization** - Tracks token usage and spending across all LLM API calls
- **📊 Quality Monitoring** - Measures response quality and detects degradation patterns
- **⚡ Performance Analytics** - Monitors latency, error rates, and system health
- **🤖 AI-Powered Analysis** - Uses Google Gemini 2.0 Flash for intelligent threat detection
- **📈 Datadog Integration** - Advanced monitoring with 5 automated monitors for alerts

### Key Features

✅ **Real-time Monitoring** - Live dashboards update every 3 seconds  
✅ **Threat Detection** - 6 threat types identified automatically  
✅ **Cost Tracking** - Per-request cost calculation with daily/monthly aggregates  
✅ **Quality Scores** - 0-1 scoring system for response quality  
✅ **Demo Mode** - Test with simulated attacks without real API costs  
✅ **Firebase Authentication** - Secure login with Google or Email/Password  
✅ **Cloud Native** - Built on Google Cloud Platform (Firestore, Cloud Functions)  

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Your LLM Application                        │
│            (OpenAI, Anthropic, Google Gemini, etc.)             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Sends telemetry via SDK/API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GuardianAI Backend API                        │
│                      (FastAPI - Cloud Run)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /api/webhooks/telemetry  - Receives LLM request data    │  │
│  │  /api/metrics/summary     - Returns aggregated metrics   │  │
│  │  /api/demo/*              - Demo mode endpoints          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Stores in Firestore
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Cloud Firestore                             │
│              (telemetry_records collection)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - trace_id, timestamp, model, prompt, response          │  │
│  │  - tokens_used, cost, latency, quality_score             │  │
│  │  - threats_detected, error_occurred                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Triggers Cloud Function
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 GuardianAI Pipeline (Cloud Function)             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Anomaly Detection - Statistical analysis             │  │
│  │  2. Threat Detection - Pattern matching + ML             │  │
│  │  3. Quality Analysis - Gemini 2.0 Flash scoring          │  │
│  │  4. Alert Management - Sends to Datadog                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Sends alerts
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Datadog Monitors                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - Cost Spike Monitor (>$100/day threshold)              │  │
│  │  - Threat Detection Monitor (any critical threats)       │  │
│  │  - Quality Degradation Monitor (<0.7 score)              │  │
│  │  - High Latency Monitor (>5s response time)              │  │
│  │  - Error Rate Monitor (>10% errors)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ User views in
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  GuardianAI Frontend Dashboard                   │
│                   (React + TypeScript - Vite)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Dashboard Page  - System overview & health              │  │
│  │  Demo Mode Page  - Test with simulated attacks           │  │
│  │  Threats Page    - Security threat timeline              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend**
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- React Router (navigation)
- Firebase Auth (authentication)
- Lucide Icons (UI icons)

**Backend**
- FastAPI (Python web framework)
- Google Cloud Firestore (NoSQL database)
- Pydantic (data validation)
- CORS middleware (cross-origin requests)

**Pipeline**
- Google Cloud Functions (serverless)
- Google Gemini 2.0 Flash (AI analysis)
- Datadog API (monitoring & alerts)
- Statistical anomaly detection

**Infrastructure**
- Google Cloud Platform (GCP)
- Firebase (Authentication + Hosting)
- Datadog (Monitoring & Alerts)

---

## 🚀 Getting Started - Setup Flow

### Prerequisites

- Google Cloud Project (free tier works!)
- Datadog account (free trial available)
- Node.js 18+ and Python 3.11+
- Firebase account

### Step 1: Clone and Install

```bash
# Clone the repository
git clone <your-repo-url>
cd guardianai-project

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt

# Install pipeline dependencies
cd ../pipeline
pip install -r requirements.txt
```

### Step 2: Firebase Setup

1. **Create Firebase Project** (if not already done)
   - Go to https://console.firebase.google.com/
   - Click "Add project" or use existing: `lovable-clone-e08db`

2. **Enable Authentication**
   - Build → Authentication → Get Started
   - Enable "Email/Password"
   - Enable "Google" provider

3. **Create Web App**
   - Project Settings → Add app → Web
   - Register app, copy config keys

4. **Create Environment File**

Create `frontend/.env`:
```env
VITE_FIREBASE_API_KEY=AIzaSyCNrhnOv2VoMD2TSRdLGdtG8LuBc0kha-8
VITE_FIREBASE_AUTH_DOMAIN=lovable-clone-e08db.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=lovable-clone-e08db
VITE_FIREBASE_STORAGE_BUCKET=lovable-clone-e08db.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=172681729216
VITE_FIREBASE_APP_ID=1:172681729216:web:96eebce8e3eee9cdc4c925
```

### Step 3: Google Cloud Setup

1. **Enable Firestore**
   ```bash
   gcloud firestore databases create --location=nam5 --database=guardianai
   ```

2. **Create Service Account**
   ```bash
   gcloud iam service-accounts create guardianai \
     --display-name="GuardianAI Service Account"
   
   gcloud projects add-iam-policy-binding lovable-clone-e08db \
     --member="serviceAccount:guardianai@lovable-clone-e08db.iam.gserviceaccount.com" \
     --role="roles/datastore.user"
   ```

3. **Get Service Account Key**
   - Cloud Console → IAM & Admin → Service Accounts
   - Click on guardianai account → Keys → Add Key → JSON
   - Save as `lovable-clone-e08db-56b9ffba4711.json`

### Step 4: Datadog Setup

1. **Get API Keys**
   - Datadog → Organization Settings → API Keys
   - Create new API key
   - Create new Application key

2. **Configure Pipeline**

Create `pipeline/.env`:
```env
DATADOG_API_KEY=your_datadog_api_key
DATADOG_APP_KEY=your_datadog_app_key
DATADOG_SITE=datadoghq.com
```

### Step 5: Configure Backend

Create `backend/.env`:
```env
GCP_PROJECT_ID=lovable-clone-e08db
FIRESTORE_DATABASE=guardianai
GOOGLE_APPLICATION_CREDENTIALS=../lovable-clone-e08db-56b9ffba4711.json
GEMINI_API_KEY=your_gemini_api_key
```

### Step 6: Initialize Datadog Monitors

```bash
cd pipeline
python setup_monitors.py
```

This creates 5 automated monitors:
- ✅ Cost Spike Detection
- ✅ Threat Detection Alerts
- ✅ Quality Degradation Warnings
- ✅ High Latency Alerts
- ✅ Error Rate Monitoring

### Step 7: Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the app:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 👤 User Flow - Monitoring Your LLM

### Flow 1: First-Time User Setup

```
1. Visit http://localhost:3000
   ↓
2. Redirected to /login page
   ↓
3. Click "Sign in with Google" OR enter email/password
   ↓
4. Authenticated → Redirected to /dashboard
   ↓
5. See empty dashboard (no data yet)
   ↓
6. Click "Launch Demo Mode" button
   ↓
7. Redirected to /demo page
   ↓
8. Click "Run Comprehensive Test" scenario
   ↓
9. Watch real-time data populate (65 simulated requests)
   ↓
10. Return to /dashboard to see populated metrics
```

### Flow 2: Integrating Your LLM Application

**Option A: Using the SDK (Recommended)**

```python
# Install GuardianAI SDK
pip install guardianai-sdk

# In your LLM application
from guardianai import GuardianAI

# Initialize
guardian = GuardianAI(
    api_url="http://localhost:8000",
    api_key="your_api_key"  # Optional for authentication
)

# Wrap your LLM calls
response = your_llm_api.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# Send telemetry to GuardianAI
guardian.track(
    prompt="Hello",
    response=response.choices[0].message.content,
    model="gpt-4",
    tokens_used=response.usage.total_tokens,
    cost=0.03  # Calculate based on your pricing
)
```

**Option B: Direct API Integration**

```python
import requests
from datetime import datetime

def send_to_guardianai(prompt, response, model, tokens, cost):
    payload = {
        "trace_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "model": model,
        "prompt_text": prompt,
        "response_text": response,
        "tokens_used": tokens,
        "cost": cost,
        "latency_ms": 1500,  # Measure actual latency
        "metadata": {
            "application": "my_chatbot",
            "user_id": "user_123"
        }
    }
    
    requests.post(
        "http://localhost:8000/api/webhooks/telemetry",
        json=payload
    )

# After every LLM call
send_to_guardianai(
    prompt=user_message,
    response=ai_response,
    model="gpt-4",
    tokens=1234,
    cost=0.03
)
```

### Flow 3: Monitoring Live Traffic

```
1. LLM requests flow into GuardianAI backend
   ↓
2. Data stored in Firestore (telemetry_records)
   ↓
3. Cloud Function triggered for analysis
   ↓
4. Threats detected, quality scored, anomalies flagged
   ↓
5. Datadog monitors evaluate conditions
   ↓
6. Alerts sent if thresholds exceeded
   ↓
7. User views real-time dashboard
   ↓
8. Dashboard auto-refreshes every 3 seconds
   ↓
9. User clicks on threat in /threats page
   ↓
10. Detailed threat information displayed
```

### Flow 4: Investigating a Threat

```
1. User sees "Active Threats: 5" on dashboard
   ↓
2. Click "View Threats" quick action
   ↓
3. Redirected to /threats page
   ↓
4. See timeline of all detected threats
   ↓
5. Filter by severity: "Critical" selected
   ↓
6. Click on "Prompt Injection" threat card
   ↓
7. Card expands showing:
   - Threat indicators (malicious patterns found)
   - Confidence score (95%)
   - Blocked status (Yes/No)
   - Timestamp
   ↓
8. User can:
   - Copy threat details
   - View full request in logs
   - Adjust detection sensitivity
   - Add to whitelist/blocklist
```

---

## 🎨 Frontend UI Guide

### Authentication Flow

#### Login Page (`/login`)

**Layout:**
```
┌─────────────────────────────────────────┐
│          [GuardianAI Logo]              │
│   Enterprise LLM Security Platform      │
├─────────────────────────────────────────┤
│  Features:                              │
│  🛡️ Real-time threat detection          │
│  ⚡ Cost optimization & monitoring      │
│  🔒 Quality assurance & compliance      │
├─────────────────────────────────────────┤
│  Sign In                                │
│  ┌───────────────────────────────────┐  │
│  │ 📧 Email Address                   │  │
│  │ [email input field]                │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ 🔒 Password                        │  │
│  │ [password input field]             │  │
│  └───────────────────────────────────┘  │
│  [Sign In Button]                       │
│  ───────── OR ─────────                 │
│  [🔵 Sign in with Google]               │
│  ───────────────────────────────────    │
│  Don't have an account? Sign up         │
└─────────────────────────────────────────┘
```

**Interactive Elements:**

1. **Email Input Field**
   - Placeholder: "you@example.com"
   - Auto-validates email format
   - Shows error if invalid

2. **Password Input Field**
   - Placeholder: "Enter your password"
   - Masked input (•••••)
   - Toggle visibility icon

3. **Sign In Button**
   - Action: Validates form → Calls Firebase `signInWithEmailAndPassword()`
   - Loading state: Shows spinner, disables button
   - Success: Redirects to `/dashboard`
   - Error: Shows error message above form

4. **Sign in with Google Button**
   - Action: Opens Google OAuth popup → `signInWithPopup(googleProvider)`
   - One-click authentication
   - Success: Redirects to `/dashboard`
   - Error: Shows "Failed to sign in with Google"

5. **Sign Up Link**
   - Action: Toggles to registration form
   - Same layout, additional "Confirm Password" field
   - Creates account with `createUserWithEmailAndPassword()`

---

### Main Application Layout

Once authenticated, users see the main layout:

```
┌────────────────────────────────────────────────────────────────┐
│  [GuardianAI Logo]  │  🟢 System Active  👤 User  [Logout]    │ ← Header
├─────────────────────┼────────────────────────────────────────────┤
│                     │                                           │
│  NAVIGATION         │         MAIN CONTENT AREA                 │
│  ┌─────────────┐    │                                           │
│  │ 📊 Dashboard │    │      (Dashboard/Demo/Threats pages)       │
│  ├─────────────┤    │                                           │
│  │ 🎯 Demo Mode│    │                                           │
│  ├─────────────┤    │                                           │
│  │ 🛡️ Threats  │    │                                           │
│  └─────────────┘    │                                           │
│                     │                                           │
│   ← Sidebar         │                                           │
└─────────────────────┴────────────────────────────────────────────┘
```

#### Header Components

**1. GuardianAI Logo**
- Always visible in top-left
- Clicking returns to dashboard

**2. System Status Badge**
- Green: "🟢 System Active" - Backend connected
- Red: "🔴 System Error" - Backend unreachable
- Auto-updates every 3 seconds

**3. User Avatar**
- Shows user initials in circle
- Hover: Shows full name and email
- Desktop only (hidden on mobile)

**4. Logout Button**
- Icon: 🚪 LogOut
- Action: Calls Firebase `signOut()` → Clears session → Redirects to `/login`
- Hover: Turns red

#### Sidebar Navigation

**1. Dashboard Link** (`/dashboard`)
- Icon: 📊 LayoutDashboard
- Active state: Blue background, bold text
- Shows system overview and key metrics

**2. Demo Mode Link** (`/demo`)
- Icon: 🎯 Target
- Test platform with simulated attacks
- No real LLM API costs

**3. Threats Link** (`/threats`)
- Icon: 🛡️ Shield
- Security threat timeline
- Filter and investigate detected threats

---

### Dashboard Page (`/dashboard`)

The main overview page showing system health and metrics.

**Layout Sections:**

```
┌──────────────────────────────────────────────────────────────┐
│  DASHBOARD                                                    │
├──────────────────────────────────────────────────────────────┤
│  PRIMARY METRICS (4 cards in row)                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Health  │ │ Total   │ │ Active  │ │ Total   │           │
│  │ Score   │ │Requests │ │Threats  │ │ Cost    │           │
│  │  95%    │ │  1,234  │ │   3     │ │ $45.67  │           │
│  │  ↑ 2%   │ │  ↑ 12%  │ │  ↓ 1    │ │ ↑ $5.23 │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
├──────────────────────────────────────────────────────────────┤
│  SECONDARY METRICS (4 cards in row)                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Avg     │ │ Avg     │ │ Error   │ │ Uptime  │           │
│  │Latency  │ │Quality  │ │ Rate    │ │         │           │
│  │ 234ms   │ │  0.92   │ │  1.2%   │ │ 99.9%   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
├──────────────────────────────────────────────────────────────┤
│  THREAT BREAKDOWN (if threats > 0)                           │
│  ┌───────────────┐ ┌───────────────┐ ┌──────────────┐      │
│  │ ⚠️ Prompt     │ │ 🔓 PII Leak   │ │ 🚨 Jailbreak │      │
│  │ Injection: 5  │ │     2         │ │     1        │      │
│  └───────────────┘ └───────────────┘ └──────────────┘      │
├──────────────────────────────────────────────────────────────┤
│  SYSTEM HEALTH PANEL                                         │
│  Uptime      ████████████████████░░  95%  (green)           │
│  Quality     ████████████████░░░░░░  80%  (blue)            │
│  Security    ███████████████████░░░  90%  (green)           │
│  Cost Eff.   ████████████░░░░░░░░░░  60%  (yellow)          │
├──────────────────────────────────────────────────────────────┤
│  RECENT ACTIVITY                    │  QUICK ACTIONS        │
│  • New request processed            │  [Launch Demo]        │
│  • Threat detected: Prompt Inj.     │  [View Threats]       │
│  • Quality score: 0.95              │  [Analytics]          │
│  • Cost spike detected              │                       │
└──────────────────────────────────────────────────────────────┘
```

**Interactive Elements:**

**1. Primary Metric Cards**
- **Health Score Card**
  - Shows overall system health (0-100%)
  - Green if >80%, Yellow if 50-80%, Red if <50%
  - Trend arrow (↑ up, ↓ down, → neutral)
  - Click: Opens detailed health dashboard (future feature)

- **Total Requests Card**
  - Count of all LLM requests processed
  - Trend shows change vs. previous period
  - Click: Opens request log (future feature)

- **Active Threats Card**
  - Red if >0, Green if 0
  - Shows count of unresolved threats
  - Click: Navigates to `/threats` page

- **Total Cost Card**
  - Running total of LLM API costs
  - Dollar format ($XX.XX)
  - Trend shows daily change
  - Click: Opens cost breakdown (future feature)

**2. Secondary Metric Cards**
- **Avg Latency**: Response time in milliseconds
- **Avg Quality**: Quality score (0-1 scale)
- **Error Rate**: Percentage of failed requests
- **Uptime**: System availability percentage

**3. Threat Breakdown Cards**
- Only visible when threats detected
- Separate card for each threat type
- Shows icon + count
- Click: Filters threats page to that type

**4. System Health Bars**
- Visual progress bars
- Color-coded: Green (good), Yellow (warning), Red (critical)
- Percentages calculated from metrics

**5. Recent Activity Feed**
- Live stream of latest events
- Auto-refreshes every 3 seconds
- Shows:
  - ✓ Successful requests
  - ⚠️ Detected threats
  - ⭐ Quality scores
  - 💰 Cost alerts
  - ❌ Errors

**6. Quick Actions**
- **Launch Demo Button**
  - Action: Navigate to `/demo`
  - Opens demo mode for testing

- **View Threats Button**
  - Action: Navigate to `/threats`
  - Shows security threat timeline

- **Analytics Button**
  - Action: Navigate to `/analytics` (future feature)
  - Deep-dive analytics dashboard

**Auto-Refresh Behavior:**
- Fetches `/api/metrics/summary` every 3 seconds
- Fetches `/api/demo/stats` every 3 seconds
- Combines data intelligently (prefers demo stats if available)
- Smooth transitions (no flashing)

---

### Demo Mode Page (`/demo`)

Interactive testing interface to simulate attacks and scenarios without real LLM costs.

**Layout:**

```
┌──────────────────────────────────────────────────────────────┐
│  DEMO MODE - ATTACK SIMULATION                               │
├──────────────────────────────────────────────────────────────┤
│  ATTACK LAUNCHER                                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Select Attack Type: [Dropdown ▼]                       │  │
│  │ Number of Attacks:  [Slider] 1 ────●──── 20           │  │
│  │ [🚀 Launch Attack Button]                              │  │
│  └────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  PRESET SCENARIOS                                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ │
│  │🛡️ Sec  │ │💸 Cost  │ │📊 Qual  │ │⚡ Stress│ │🎯 Full│ │
│  │Breach   │ │Crisis   │ │Decline  │ │         │ │       │ │
│  │14 steps │ │60 steps │ │20 steps │ │35 steps │ │65 step│ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └───────┘ │
├──────────────────────────────────────────────────────────────┤
│  LIVE METRICS (4 cards)                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Total    │ │ Threats  │ │ Avg      │ │ Total    │       │
│  │ Requests │ │ Detected │ │ Quality  │ │ Cost     │       │
│  │   150    │ │    12    │ │   0.87   │ │  $2.45   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├──────────────────────────────────────────────────────────────┤
│  SCENARIO PROGRESS (when running)                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Running: Security Breach Scenario                      │  │
│  │ Progress: ████████████░░░░░░░░ 60%                     │  │
│  │ Current Step: Generating jailbreak attempts...         │  │
│  │                                                         │  │
│  │ Steps: 8/14  Records: 45  Time: 12s                    │  │
│  └────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  THREAT BREAKDOWN (if threats detected)                      │
│  [Grid of threat type cards with counts]                     │
├──────────────────────────────────────────────────────────────┤
│  ADDITIONAL STATS                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │ Avg      │ │ Error    │ │ Error    │                     │
│  │ Latency  │ │ Rate     │ │ Count    │                     │
│  │  342ms   │ │   2.1%   │ │    3     │                     │
│  └──────────┘ └──────────┘ └──────────┘                     │
├──────────────────────────────────────────────────────────────┤
│  [🗑️ Reset Demo Data Button]                                │
└──────────────────────────────────────────────────────────────┘
```

**Interactive Elements:**

**1. Attack Type Dropdown**
- Options:
  1. Normal Request (baseline, no threats)
  2. Prompt Injection (SQL injection-style prompts)
  3. PII Leak (contains SSN, credit cards)
  4. Jailbreak Attempt (bypass system prompts)
  5. Toxic Content (harmful/offensive text)
  6. Cost Spike (high token usage)
  7. Quality Degradation (poor responses)
  8. Latency Spike (slow responses 6-12s)
  9. Error Burst (intentional failures)
- Action: Select attack type to generate

**2. Attack Count Slider**
- Range: 1 to 20 attacks
- Shows current value above slider
- Drag to adjust
- Default: 10

**3. Launch Attack Button**
- Action: 
  - Sends POST to `/api/demo/launch-attack`
  - Generates selected number of attack records
  - Shows success message with trace IDs
  - Updates metrics in real-time
- States:
  - Default: Blue "Launch Attack"
  - Loading: Gray "Launching..." (disabled)
  - Success: Green flash "Launched!"
  - Error: Red "Failed to launch"

**4. Preset Scenario Buttons**

Each scenario button runs a multi-step simulation:

- **🛡️ Security Breach (14 steps)**
  - Action: Runs security-focused attacks
  - Sequence:
    1. 3x Normal requests (baseline)
    2. 5x Prompt injection attacks
    3. 2x PII leak attempts
    4. 3x Jailbreak attempts
    5. 1x Toxic content
  - Duration: ~14 seconds
  - Click: Starts scenario → Shows progress → Completes

- **💸 Cost Crisis (60 steps)**
  - Action: Simulates cost spike
  - Sequence:
    1. 10x Normal requests
    2. 50x Cost spike (high tokens)
  - Total cost: ~$550
  - Duration: ~60 seconds

- **📊 Quality Decline (20 steps)**
  - Action: Shows quality degradation
  - Sequence:
    1. 10x Normal (quality 0.85-0.95)
    2. 10x Quality degradation (0.5-0.7)
  - Duration: ~20 seconds

- **⚡ System Stress (35 steps)**
  - Action: Tests performance limits
  - Sequence:
    1. 5x Normal
    2. 10x Latency spike (6-12s)
    3. 20x Error burst (50% failure rate)
  - Duration: ~35 seconds

- **🎯 Comprehensive Test (65 steps)**
  - Action: All attack types combined
  - Full system test
  - Duration: ~65 seconds
  - Best for demo videos!

**5. Scenario Progress Panel**
- Only visible when scenario running
- Real-time updates every 1 second
- Shows:
  - Scenario name
  - Progress bar (0-100%)
  - Current step description
  - Stats: Steps completed, Records created, Elapsed time
- Auto-hides when complete

**6. Reset Demo Data Button**
- Action:
  - Shows confirmation dialog: "This will delete all demo records. Continue?"
  - If confirmed: POST to `/api/demo/reset`
  - Deletes all records with `metadata.demo_mode = true`
  - Resets metrics to zero
  - Shows success: "Demo data cleared!"
- Use case: Clean slate before demo video recording

**Auto-Refresh Behavior:**
- Metrics: Every 2 seconds
- Scenario status: Every 1 second (when running)
- Smooth polling (no page flicker)

---

### Threats Page (`/threats`)

Security monitoring dashboard showing detected threats timeline.

**Layout:**

```
┌──────────────────────────────────────────────────────────────┐
│  🛡️ SECURITY THREATS - Total: 23                             │
├──────────────────────────────────────────────────────────────┤
│  THREAT STATISTICS                                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ │
│  │⚠️ Prompt│ │🔓 PII   │ │🚨 Jail  │ │☢️ Toxic │ │💰 Cost│ │
│  │Injection│ │Leak: 4  │ │break: 2 │ │Content:1│ │Spike:8│ │
│  │  Count:8│ │         │ │         │ │         │ │       │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └───────┘ │
├──────────────────────────────────────────────────────────────┤
│  FILTERS                                                     │
│  🔍 [Search threats...]  [Severity ▼]  [Type ▼]            │
├──────────────────────────────────────────────────────────────┤
│  THREAT TIMELINE                                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ ⚠️ Prompt Injection                            [5]     │  │
│  │ Detected malicious prompt patterns                     │  │
│  │ Severity: Critical  Confidence: 95%  ✓ Blocked        │  │
│  │ [▼ Expand for details]                                 │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ 🔓 PII Leak                                    [4]     │  │
│  │ Personal identifiable information detected             │  │
│  │ Severity: High  Confidence: 98%  ✓ Blocked            │  │
│  │ [▼ Expand for details]                                 │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ 🚨 Jailbreak Attempt                           [2]     │  │
│  │ System prompt bypass detected                          │  │
│  │ Severity: Critical  Confidence: 92%  ✓ Blocked        │  │
│  │ [▼ Expand for details]                                 │  │
│  └────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  SUMMARY STATISTICS                                          │
│  Detection Rate: 100%  │  Blocked: 23/23  │  Avg Conf: 95%  │
└──────────────────────────────────────────────────────────────┘
```

**Interactive Elements:**

**1. Threat Statistic Cards**
- One card per threat type
- Shows icon + count
- Color-coded by default severity:
  - Prompt Injection: Red (Critical)
  - PII Leak: Orange (High)
  - Jailbreak: Red (Critical)
  - Toxic Content: Orange (High)
  - Cost Spike: Yellow (Medium)
  - Quality Degradation: Blue (Low)
- Click: Filters timeline to show only that threat type

**2. Search Filter**
- Text input: "Search threats..."
- Action: Filters threats by name/description in real-time
- Case-insensitive search
- Searches: Threat type, description, indicators

**3. Severity Dropdown**
- Options:
  - All Severities (default)
  - Critical
  - High
  - Medium
  - Low
- Action: Filters threats by severity level
- Combines with other filters (AND logic)

**4. Type Dropdown**
- Options:
  - All Types (default)
  - Prompt Injection
  - PII Leak
  - Jailbreak Attempt
  - Toxic Content
  - Cost Spike
  - Quality Degradation
- Action: Filters threats by specific type
- Combines with other filters

**5. Threat Cards (Collapsed State)**
- Shows:
  - Icon + Threat name
  - Count badge (number of occurrences)
  - One-line description
  - Severity, Confidence, Blocked status
  - Expand arrow
- Color-coded left border by severity
- Click anywhere: Expands card

**6. Threat Cards (Expanded State)**
- Shows all collapsed info PLUS:
  - **Indicators** section:
    - List of detection patterns found
    - Example: "SQL injection patterns", "System prompt bypass"
  - **Timestamp**: When first detected
  - **Actions**:
    - [View Details] - Opens modal with full request/response
    - [Add to Whitelist] - Excludes from future detection
    - [Report False Positive] - Feedback mechanism
- Click expand arrow again: Collapses card

**7. Empty State**
- Visible when no threats detected
- Shows:
  - Green shield icon (large)
  - "No Threats Detected"
  - "Your LLM applications are secure"
  - [Go to Demo Mode] button
- Action: Encourages testing in demo mode

**8. Summary Statistics Bar**
- **Detection Rate**: Percentage of threats caught (always 100% in demo)
- **Blocked**: Fraction of threats blocked (23/23)
- **Avg Confidence**: Average confidence score across all threats (95%)

**Auto-Refresh:**
- Fetches `/api/demo/stats` every 3 seconds
- Recalculates threat breakdown
- Maintains filter state during refresh
- Smooth updates (no page reload)

---

## 🔌 Backend API Reference

### Base URL
```
http://localhost:8000
```

### Authentication
Currently: No authentication required (demo mode)
Production: Add API key header: `X-API-Key: your_key`

---

### Endpoints

#### 1. Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-22T10:30:00Z",
  "version": "1.0.0"
}
```

**Use case:** Check if backend is running

---

#### 2. Receive Telemetry
```http
POST /api/webhooks/telemetry
```

**Request Body:**
```json
{
  "trace_id": "uuid-123",
  "timestamp": "2024-12-22T10:30:00Z",
  "model": "gpt-4",
  "prompt_text": "What is the capital of France?",
  "response_text": "The capital of France is Paris.",
  "tokens_used": 25,
  "cost": 0.0015,
  "latency_ms": 1250,
  "quality_score": 0.95,
  "threats_detected": [],
  "error_occurred": false,
  "metadata": {
    "application": "my_chatbot",
    "user_id": "user_123",
    "demo_mode": false
  }
}
```

**Response:**
```json
{
  "status": "success",
  "trace_id": "uuid-123",
  "message": "Telemetry received and processed"
}
```

**Use case:** Your LLM application sends data here after each request

---

#### 3. Get Metrics Summary
```http
GET /api/metrics/summary
```

**Query Parameters:**
- `start_date` (optional): ISO timestamp
- `end_date` (optional): ISO timestamp
- `model` (optional): Filter by model name

**Response:**
```json
{
  "total_requests": 1234,
  "total_cost": 45.67,
  "avg_latency_ms": 1250,
  "avg_quality_score": 0.89,
  "error_rate": 0.012,
  "threats_by_type": {
    "prompt_injection": 8,
    "pii_leak": 4,
    "jailbreak_attempt": 2,
    "toxic_content": 1
  },
  "time_range": {
    "start": "2024-12-22T00:00:00Z",
    "end": "2024-12-22T23:59:59Z"
  }
}
```

**Use case:** Dashboard page fetches this every 3 seconds

---

#### 4. Launch Demo Attack
```http
POST /api/demo/launch-attack
```

**Request Body:**
```json
{
  "attack_type": "prompt_injection",
  "count": 10
}
```

**Attack Types:**
- `normal` - Baseline requests
- `prompt_injection` - SQL injection-style attacks
- `pii_leak` - SSN/credit card data
- `jailbreak_attempt` - System prompt bypass
- `toxic_content` - Harmful content
- `cost_spike` - High token usage
- `quality_degradation` - Poor quality responses
- `latency_spike` - Slow responses (6-12s)
- `error_burst` - 50% error rate

**Response:**
```json
{
  "status": "success",
  "attack_type": "prompt_injection",
  "count": 10,
  "trace_ids": [
    "demo-uuid-1",
    "demo-uuid-2",
    "..."
  ],
  "message": "Successfully generated 10 prompt_injection attacks"
}
```

**Use case:** Demo page "Launch Attack" button

---

#### 5. Run Demo Scenario
```http
POST /api/demo/run-scenario
```

**Request Body:**
```json
{
  "scenario_type": "security_breach",
  "speed": "normal"
}
```

**Scenario Types:**
- `security_breach` - 14 steps, security-focused
- `cost_crisis` - 60 steps, cost spike simulation
- `quality_decline` - 20 steps, quality degradation
- `system_stress` - 35 steps, performance test
- `comprehensive` - 65 steps, all attack types

**Speed Options:**
- `fast` - 100ms delay between steps
- `normal` - 1000ms delay (default)
- `slow` - 2000ms delay

**Response:**
```json
{
  "scenario_id": "scenario-uuid-123",
  "scenario_type": "security_breach",
  "total_steps": 14,
  "status": "running",
  "message": "Scenario started in background"
}
```

**Use case:** Demo page preset scenario buttons

---

#### 6. Check Scenario Status
```http
GET /api/demo/status/{scenario_id}
```

**Response:**
```json
{
  "scenario_id": "scenario-uuid-123",
  "status": "running",
  "progress_percent": 60,
  "current_step": 8,
  "total_steps": 14,
  "current_step_name": "Generating jailbreak attempts",
  "records_created": 45,
  "elapsed_seconds": 12
}
```

**Statuses:**
- `running` - In progress
- `completed` - Successfully finished
- `failed` - Error occurred

**Use case:** Demo page polls this every 1 second during scenario

---

#### 7. Get Demo Statistics
```http
GET /api/demo/stats
```

**Response:**
```json
{
  "total_requests": 150,
  "total_cost": 2.45,
  "avg_quality": 0.87,
  "avg_latency_ms": 342,
  "error_rate": 0.021,
  "error_count": 3,
  "threats_detected": {
    "prompt_injection": 5,
    "pii_leak": 2,
    "jailbreak_attempt": 1,
    "toxic_content": 0,
    "cost_spike": 3,
    "quality_degradation": 1
  },
  "threat_breakdown": {
    "total": 12,
    "by_severity": {
      "critical": 6,
      "high": 4,
      "medium": 2,
      "low": 0
    }
  }
}
```

**Use case:** Demo and Threats pages fetch this every 2-3 seconds

---

#### 8. Reset Demo Data
```http
POST /api/demo/reset
```

**Response:**
```json
{
  "status": "success",
  "deleted_count": 150,
  "message": "All demo data cleared"
}
```

**Use case:** Demo page "Reset Demo Data" button

---

## 🔗 Integration Guide

### Integrating GuardianAI with Your LLM Application

#### Step 1: Install SDK (Future)
```bash
pip install guardianai-sdk
```

#### Step 2: Initialize Client
```python
from guardianai import GuardianAI

guardian = GuardianAI(
    api_url="https://your-guardianai-backend.com",
    api_key="your_api_key"
)
```

#### Step 3: Wrap Your LLM Calls

**Example: OpenAI Integration**
```python
import openai
import time
import uuid

# Your existing OpenAI call
start_time = time.time()
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_prompt}
    ]
)
latency_ms = int((time.time() - start_time) * 1000)

# Send to GuardianAI
guardian.track(
    trace_id=str(uuid.uuid4()),
    model="gpt-4",
    prompt_text=user_prompt,
    response_text=response.choices[0].message.content,
    tokens_used=response.usage.total_tokens,
    cost=calculate_cost(response.usage.total_tokens),  # Your pricing logic
    latency_ms=latency_ms,
    metadata={
        "user_id": current_user_id,
        "application": "customer_support_bot",
        "environment": "production"
    }
)
```

**Example: Anthropic Claude Integration**
```python
import anthropic
import time
import uuid

client = anthropic.Anthropic(api_key="your_key")

start_time = time.time()
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    messages=[{"role": "user", "content": user_prompt}]
)
latency_ms = int((time.time() - start_time) * 1000)

# Send to GuardianAI
guardian.track(
    trace_id=str(uuid.uuid4()),
    model="claude-3-opus",
    prompt_text=user_prompt,
    response_text=message.content[0].text,
    tokens_used=message.usage.input_tokens + message.usage.output_tokens,
    cost=calculate_claude_cost(message.usage),
    latency_ms=latency_ms
)
```

**Example: Google Gemini Integration**
```python
import google.generativeai as genai
import time
import uuid

genai.configure(api_key="your_key")
model = genai.GenerativeModel('gemini-pro')

start_time = time.time()
response = model.generate_content(user_prompt)
latency_ms = int((time.time() - start_time) * 1000)

# Send to GuardianAI
guardian.track(
    trace_id=str(uuid.uuid4()),
    model="gemini-pro",
    prompt_text=user_prompt,
    response_text=response.text,
    tokens_used=response.usage_metadata.total_token_count,
    cost=calculate_gemini_cost(response.usage_metadata),
    latency_ms=latency_ms
)
```

#### Step 4: Handle Errors
```python
try:
    response = your_llm_api.call(prompt)
    guardian.track(
        # ... success data
        error_occurred=False
    )
except Exception as e:
    guardian.track(
        trace_id=str(uuid.uuid4()),
        model="gpt-4",
        prompt_text=user_prompt,
        response_text="",
        tokens_used=0,
        cost=0,
        latency_ms=0,
        error_occurred=True,
        metadata={"error": str(e)}
    )
    raise
```

#### Step 5: View in Dashboard
1. Open GuardianAI dashboard
2. See real-time metrics populate
3. Threats auto-detected and displayed
4. Datadog alerts triggered if thresholds exceeded

---

## 🎮 Demo Mode

### What is Demo Mode?

Demo mode lets you test GuardianAI without:
- Real LLM API calls
- Actual costs
- External dependencies

Perfect for:
- Demo videos
- Development testing
- Showcasing features
- Training sessions

### How Demo Mode Works

1. **Simulated Data Generation**
   - `DemoDataGenerator` class creates realistic telemetry
   - No actual LLM API calls
   - Deterministic output for reliable demos

2. **Attack Scenarios**
   - Pre-programmed attack sequences
   - Realistic threat patterns
   - Controlled outcomes

3. **Isolated Storage**
   - Demo records tagged with `metadata.demo_mode = true`
   - Separate from production data
   - Easy to reset/clear

### Demo Mode Best Practices

**For Hackathon Demo Video:**
1. Reset demo data before recording
2. Run "Comprehensive Test" scenario (65 steps)
3. Show real-time dashboard updates
4. Navigate to threats page
5. Expand a critical threat
6. Show Datadog monitors (if integrated)

**Recording Script:**
```
0:00 - Login with Google
0:05 - Show empty dashboard
0:10 - Navigate to Demo Mode
0:15 - Click "Comprehensive Test"
0:20 - Show progress bar filling
0:30 - Navigate to Dashboard (populated)
0:40 - Highlight key metrics (threats, cost, quality)
0:50 - Navigate to Threats page
1:00 - Filter by "Critical" severity
1:10 - Expand "Prompt Injection" threat
1:20 - Show threat indicators
1:30 - Navigate back to Dashboard
1:40 - Show Datadog integration (if available)
1:50 - Highlight real-time updates
2:00 - Conclude with value proposition
```

---

## 📊 Metrics Explained

### Health Score (0-100%)
Composite score calculated from:
- Threat detection rate (25%)
- Error rate (25%)
- Average quality (25%)
- Cost efficiency (25%)

**Formula:**
```python
health_score = (
    (1 - error_rate) * 25 +
    avg_quality * 25 +
    (threats_blocked / threats_detected) * 25 +
    (1 - cost_variance) * 25
)
```

### Quality Score (0-1)
Gemini 2.0 Flash analyzes each response for:
- Accuracy and correctness
- Relevance to prompt
- Coherence and clarity
- Completeness
- Tone appropriateness

**Thresholds:**
- 0.9-1.0: Excellent
- 0.7-0.89: Good
- 0.5-0.69: Fair (warning)
- < 0.5: Poor (alert)

### Cost Calculation
```python
cost = (
    (input_tokens * input_price_per_1k / 1000) +
    (output_tokens * output_price_per_1k / 1000)
)
```

**Example (GPT-4):**
- Input: 500 tokens × $0.03/1K = $0.015
- Output: 200 tokens × $0.06/1K = $0.012
- Total: $0.027

### Threat Confidence (0-1)
Probability that detected threat is real:
- 0.95+: Very high confidence
- 0.85-0.94: High confidence
- 0.70-0.84: Medium confidence
- < 0.70: Low confidence (potential false positive)

---

## 🚨 Alert Thresholds (Datadog)

### 1. Cost Spike Alert
- **Trigger**: Daily cost > $100
- **Action**: Email + Slack notification
- **Recommended**: Review token usage patterns

### 2. Threat Detection Alert
- **Trigger**: Any critical severity threat
- **Action**: Immediate email
- **Recommended**: Investigate and block if confirmed

### 3. Quality Degradation Alert
- **Trigger**: Average quality < 0.7 for 10+ requests
- **Action**: Email notification
- **Recommended**: Review model/prompt changes

### 4. High Latency Alert
- **Trigger**: Average latency > 5000ms
- **Action**: Email notification
- **Recommended**: Check API status, increase timeout

### 5. Error Rate Alert
- **Trigger**: Error rate > 10%
- **Action**: Email + Slack notification
- **Recommended**: Check API keys, rate limits, quotas

---

## 🔒 Security Best Practices

### Production Deployment

1. **Enable Authentication**
   - Require API keys for `/api/webhooks/telemetry`
   - Use Firebase Auth for frontend
   - Implement RBAC (role-based access control)

2. **Secure Firestore**
   - Use security rules to restrict access
   - Enable audit logging
   - Backup data regularly

3. **Environment Variables**
   - Never commit `.env` files
   - Use Secret Manager in production
   - Rotate keys quarterly

4. **HTTPS Only**
   - Force HTTPS on all endpoints
   - Use proper TLS certificates
   - Implement HSTS headers

5. **Rate Limiting**
   - Limit API calls per user/IP
   - Prevent DDoS attacks
   - Use Cloud Armor (GCP)

---

## 📈 Roadmap & Future Features

### Phase 1 (MVP - Current)
- ✅ Dashboard with key metrics
- ✅ Demo mode with attack simulation
- ✅ Threat detection and timeline
- ✅ Firebase authentication
- ✅ Datadog integration

### Phase 2 (Next)
- [ ] User management and teams
- [ ] Custom alert rules
- [ ] API key management
- [ ] Cost budgets and limits
- [ ] Email digest reports

### Phase 3 (Future)
- [ ] Incidents page (correlate threats)
- [ ] Traces page (request waterfall)
- [ ] Analytics page (deep-dive charts)
- [ ] Settings page (configuration UI)
- [ ] Mobile app (React Native)
- [ ] Slack/Teams integration
- [ ] Automated remediation (block malicious IPs)
- [ ] A/B testing for prompts
- [ ] LLM model comparison
- [ ] Cost optimization recommendations

---

## 🆘 Troubleshooting

### Frontend Won't Start
**Problem:** `npm run dev` fails  
**Solution:**
1. Delete `node_modules` and `package-lock.json`
2. Run `npm install`
3. Check Node version: `node --version` (need 18+)

### Backend Connection Error
**Problem:** "Failed to fetch" in browser console  
**Solution:**
1. Check backend is running: `curl http://localhost:8000/api/health`
2. Verify CORS settings in `backend/main.py`
3. Check Firestore database exists: `gcloud firestore databases list`

### No Data in Dashboard
**Problem:** Dashboard shows zeros  
**Solution:**
1. Run demo scenario: Navigate to `/demo` → Click "Comprehensive Test"
2. Check backend logs for errors
3. Verify Firestore collection exists: `telemetry_records`

### Authentication Loop
**Problem:** Redirects to login repeatedly  
**Solution:**
1. Clear browser localStorage
2. Check Firebase config in `.env`
3. Verify authentication is enabled in Firebase Console

### Datadog Alerts Not Working
**Problem:** No alerts received  
**Solution:**
1. Check monitor status: `python pipeline/list_monitors.py`
2. Verify API keys are correct
3. Ensure monitors are not muted
4. Check notification channels configured

---

## 📞 Support

For questions or issues:
- **Documentation**: This file
- **Architecture**: See `SYSTEM_OVERVIEW.md`
- **Deployment**: See `docs/DEPLOYMENT.md`
- **Firebase Auth**: See `docs/FIREBASE_AUTH_SETUP.md`

---

**Built for Google Cloud + Datadog Hackathon**  
**Last Updated:** December 22, 2024
