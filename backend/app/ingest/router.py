"""Router for sensor audio ingestion endpoints."""
import logging

from fastapi import APIRouter, Depends, Request, HTTPException, status

from app.ingest.auth import validate_sensor_api_key
from app.ingest.schemas import IngestResponse, IngestHealthResponse
from app.ingest.service import process_audio_segment
from app.inference.model import get_inference
from app.db.influx import get_influx_client
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/audio",
    response_model=IngestResponse,
    summary="Ingest audio segment from sensor",
    description="Receive raw PCM audio data, run ML inference, store detected events",
)
async def ingest_audio(
    request: Request,
    sensor_info: dict = Depends(validate_sensor_api_key),
):
    """
    Receive and process an audio segment from an ESP32 sensor.

    Expected headers:
    - X-API-Key: Sensor API key
    - X-Sensor-ID: Sensor identifier
    - X-Location: Physical location
    - Content-Type: application/octet-stream

    Body: Raw PCM bytes (16-bit signed, 16kHz, mono)
    """
    settings = get_settings()

    # Read raw body
    pcm_bytes = await request.body()

    # Validate payload size
    expected_size = int(
        settings.audio_sample_rate
        * settings.audio_segment_duration_sec
        * 2  # 16-bit = 2 bytes
    )

    if len(pcm_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio payload",
        )

    # Allow some tolerance for payload size (within 10%)
    if abs(len(pcm_bytes) - expected_size) > expected_size * 0.1:
        logger.warning(
            f"Unexpected payload size: {len(pcm_bytes)} bytes "
            f"(expected ~{expected_size})"
        )

    # Process the audio segment
    result = await process_audio_segment(
        pcm_bytes=pcm_bytes,
        sensor_id=sensor_info["sensor_id"],
        location=sensor_info["location"],
    )

    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"],
        )

    return result


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
