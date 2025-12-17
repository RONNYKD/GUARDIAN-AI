# GuardianAI Architecture

## Overview

This document describes the architecture of GuardianAI, an enterprise-grade LLM monitoring and security platform.

## Components

### 1. GuardianAI SDK
- Python package with decorator-based API
- Zero-friction instrumentation for LLM applications
- Captures request/response telemetry
- Integrates with Datadog APM tracing

### 2. Processing Pipeline
- Google Cloud Functions (Python 3.11)
- Receives telemetry from SDK
- Performs threat detection and quality analysis
- Publishes metrics to Datadog

### 3. Backend API
- FastAPI application on Cloud Run
- Serves dashboard data
- Manages incidents and remediation
- WebSocket server for real-time updates

### 4. Frontend Dashboard
- React 18 with TypeScript
- Tailwind CSS for styling
- Recharts for visualizations
- Real-time updates via WebSocket

### 5. Monitored Demo Application
- FastAPI chatbot with Vertex AI Gemini
- Demonstrates SDK integration
- Used for hackathon demos

## Data Flow

See [design.md](../.kiro/specs/guardianai/design.md) for detailed data flow diagrams.

## Integration Points

### SDK → Pipeline
- Async HTTP POST with telemetry data
- Batching for efficiency

### Pipeline → Datadog
- Custom metrics with namespace `guardianai.*`
- APM traces and logs

### Datadog → Backend
- Webhook alerts for incident creation
- Auto-remediation triggers

### Backend → Frontend
- REST API for data queries
- WebSocket for real-time updates
