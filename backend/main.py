"""
GuardianAI Backend API

Enterprise-grade LLM monitoring and security platform.
FastAPI application providing:
- REST API endpoints for dashboard data
- WebSocket server for real-time updates
- Webhook handlers for Datadog alerts
- Auto-remediation orchestration
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from api.health import router as health_router
from api.metrics import router as metrics_router
from api.incidents import router as incidents_router
from api.webhooks import router as webhooks_router
from api.demo import router as demo_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    
    Initializes resources on startup and cleans up on shutdown.
    """
    # Startup
    logger.info("Starting GuardianAI Backend API...")
    settings = get_settings()
    logger.info(f"Environment: {settings.dd_env}")
    logger.info(f"GCP Project: {settings.gcp_project_id}")
    
    # Set up Datadog monitors on startup
    if settings.dd_env == "production":
        try:
            from services.datadog_monitors import get_monitor_manager
            logger.info("Setting up Datadog monitors...")
            monitor_manager = get_monitor_manager()
            monitors = monitor_manager.setup_all_monitors()
            logger.info(f"Datadog monitors configured: {monitors}")
        except Exception as e:
            logger.error(f"Failed to set up Datadog monitors: {e}")
            logger.warning("Continuing without monitors - they can be set up manually")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GuardianAI Backend API...")


# Create FastAPI application
app = FastAPI(
    title="GuardianAI API",
    description="Enterprise-grade LLM monitoring and security platform API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(metrics_router, prefix="/api", tags=["Metrics"])
app.include_router(incidents_router, prefix="/api", tags=["Incidents"])
app.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(demo_router, prefix="/api/demo", tags=["Demo"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning API info."""
    return {
        "name": "GuardianAI API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
