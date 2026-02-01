import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.influx import close_influx_client
from app.auth.router import router as auth_router
from app.events.router import router as events_router
from app.events.websocket import router as ws_router
from app.sensors.router import router as sensors_router
from app.ingest.router import router as ingest_router
from app.inference.model import init_inference, close_inference, get_inference

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()

    # Load ML model if path exists
    model_path = Path(settings.model_path)

    if model_path.exists():
        try:
            init_inference(
                model_path=str(model_path),
                input_sample_rate=settings.audio_sample_rate,
                threshold_override=settings.inference_confidence_threshold,
            )
            logger.info("ML model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
    else:
        logger.warning(
            f"ML model file not found at {model_path}. Ingestion will not work."
        )

    yield

    # Shutdown
    close_inference()
    close_influx_client()


app = FastAPI(
    title="Hospital Audio Event Monitor",
    description="API for monitoring hospital audio events",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(events_router, prefix="/api/events", tags=["events"])
app.include_router(sensors_router, prefix="/api/sensors", tags=["sensors"])
app.include_router(ingest_router, prefix="/api/ingest", tags=["ingest"])
app.include_router(ws_router, tags=["websocket"])


@app.get("/api/health")
async def health_check():
    inference = get_inference()
    model_info = None

    if inference is not None:
        health = inference.health_check()
        model_info = {
            "loaded": health["model_loaded"],
            "classes": health["classes"],
            "n_mels": health["n_mels"],
            "threshold": health["threshold"],
        }

    return {
        "status": "healthy",
        "model": model_info,
    }
