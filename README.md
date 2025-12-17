# GuardianAI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)

## 🛡️ Enterprise-Grade LLM Monitoring & Security Platform

GuardianAI is an enterprise-grade LLM monitoring and security platform that provides real-time observability, intelligent threat detection, and automated remediation for Large Language Model applications. The system is architected as a distributed cloud-native application leveraging Google Cloud Platform services and Datadog's observability platform to deliver comprehensive monitoring capabilities.

### 🎯 System Goals

1. **Complete Observability**: Capture and analyze 100% of LLM interactions with sub-500ms telemetry latency
2. **Proactive Security**: Detect and remediate threats (prompt injections, PII leaks, toxic content) in real-time
3. **Cost Control**: Monitor token usage, detect anomalies, and prevent budget overruns through automated rate limiting
4. **Quality Assurance**: Continuously assess response quality, detect hallucinations, and identify model drift
5. **Operational Excellence**: Provide actionable insights through intuitive dashboards and automated incident management

### 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User / Application                          │
└────────────┬────────────────────────────────────────┬───────────────┘
             │                                         │
             ▼                                         ▼
┌────────────────────────┐                 ┌──────────────────────────┐
│   Frontend Dashboard   │                 │  Monitored Application   │
│   (React on Vercel)    │◄────WebSocket───│  (Demo Chatbot)          │
│                        │                 │  + GuardianAI SDK        │
└────────┬───────────────┘                 └──────────┬───────────────┘
         │                                            │
         ▼                                            ▼
┌────────────────────────┐                 ┌──────────────────────────┐
│    Backend API         │◄────Webhook─────│  Processing Pipeline     │
│  (FastAPI/Cloud Run)   │                 │  (Cloud Functions)       │
└────────┬───────────────┘                 └──────────┬───────────────┘
         │                                            │
         ▼                    ▼                       ▼
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│   Firestore     │  │  Datadog Platform│  │  Vertex AI Gemini   │
└─────────────────┘  └──────────────────┘  └─────────────────────┘
```

### 📦 Project Structure

```
guardianai-project/
├── backend/           # FastAPI Backend API (Cloud Run)
│   ├── api/           # REST API endpoints
│   ├── services/      # Business logic services
│   └── main.py        # Application entry point
├── frontend/          # React Dashboard (Vercel)
│   └── src/
│       ├── pages/     # Dashboard views
│       ├── components/# Reusable UI components
│       ├── hooks/     # Custom React hooks
│       └── services/  # API client
├── sdk/               # GuardianAI Python SDK
│   └── guardianai/    # Package source
├── pipeline/          # Cloud Functions Processing Pipeline
├── demo-app/          # Monitored Chatbot Application
├── docs/              # Documentation
└── tests/             # Test suites
```

### 🚀 Key Features

- **Real-Time Request Tracing**: Capture complete LLM request/response telemetry with distributed tracing
- **Performance Metrics**: P50/P95/P99 latency, throughput, error rates with Datadog integration
- **Quality Monitoring**: AI-powered coherence scoring and hallucination detection
- **Security Threat Detection**: Prompt injection, PII leak, and toxic content detection
- **Cost Anomaly Detection**: Token usage monitoring and budget alerts
- **Auto-Remediation**: Rate limiting, circuit breaking, PII redaction
- **Live Dashboard**: Real-time monitoring with WebSocket updates

### 🔧 Technology Stack

| Component | Technology |
|-----------|------------|
| Backend API | Python 3.11, FastAPI, Cloud Run |
| Frontend | React 18, TypeScript, Tailwind CSS, Recharts |
| SDK | Python package with decorators |
| Pipeline | Cloud Functions (Python 3.11) |
| Database | Google Cloud Firestore |
| Observability | Datadog (APM, Metrics, Logs) |
| AI/ML | Vertex AI Gemini |
| Auth | JWT tokens |

### 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud Platform account with enabled APIs
- Datadog account

### ⚙️ Environment Variables

```bash
# GCP Configuration
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Datadog Configuration
DD_API_KEY=your-datadog-api-key
DD_APP_KEY=your-datadog-app-key
DD_SITE=datadoghq.com

# Application Configuration
PIPELINE_URL=https://your-pipeline-url.cloudfunctions.net
BACKEND_URL=https://your-backend-url.run.app
```

### 🏃 Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/guardianai.git
cd guardianai

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install SDK
cd ../sdk
pip install -e .

# Start backend locally
cd ../backend
uvicorn main:app --reload

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

### 📖 Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api.md)
- [SDK Guide](docs/sdk.md)
- [Deployment Guide](docs/deployment.md)

### 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov=sdk --cov=pipeline --cov-report=html
```

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

---

**Built with ❤️ for the Google Cloud Platform Hackathon (Datadog Track)**
