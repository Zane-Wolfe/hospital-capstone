"""Router for sensor audio ingestion endpoints."""
import logging

from fastapi import APIRouter

from app.ingest.schemas import IngestHealthResponse
from app.inference.model import get_inference
from app.db.influx import get_influx_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=IngestHealthResponse,
    summary="Check ingestion system health",
    description="Verify ML model is loaded and InfluxDB is connected",
)
async def ingest_health():
    """Check if the ingestion system is ready to process audio."""
    inference = get_inference()

    # Check model status
    if inference is None:
        return IngestHealthResponse(
            model_loaded=False,
            influxdb_connected=False,
            device="none",
            num_classes=0,
            classes=[],
        )

    model_health = inference.health_check()

    # Check InfluxDB connection
    influxdb_connected = False
    try:
        client = get_influx_client()
        influxdb_connected = client.ping()
    except Exception as e:
        logger.warning(f"InfluxDB health check failed: {e}")

    return IngestHealthResponse(
        model_loaded=model_health["model_loaded"],
        influxdb_connected=influxdb_connected,
        device=model_health["device"],
        num_classes=model_health["num_classes"],
        classes=model_health["classes"],
    )
