"""Service layer for audio ingestion and processing."""
import logging
import time
import uuid
from datetime import datetime, timezone

from app.inference.model import get_inference
from app.db.influx_write import write_audio_events
from app.events.websocket import broadcast_new_event
from app.config import get_settings

logger = logging.getLogger(__name__)


async def process_audio_segment(
    pcm_bytes: bytes,
    sensor_id: str,
    location: str,
) -> dict:
    """
    Process an audio segment: run inference, store events, broadcast updates.

    Args:
        pcm_bytes: Raw PCM audio data (16-bit signed, 16kHz, mono)
        sensor_id: ID of the sensor that sent the audio
        location: Physical location of the sensor

    Returns:
        Dict with processing results
    """
    start_time = time.perf_counter()
    segment_id = str(uuid.uuid4())
    settings = get_settings()

    inference = get_inference()
    if inference is None:
        logger.error("Inference engine not initialized")
        return {
            "status": "error",
            "segment_id": segment_id,
            "detected_events": [],
            "loudness_db": 0.0,
            "processing_time_ms": 0.0,
            "error": "Model not loaded",
        }

    # Run inference
    try:
        result = inference.predict(
            pcm_bytes=pcm_bytes,
            threshold=settings.inference_confidence_threshold,
            multi_label=True,
        )
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        return {
            "status": "error",
            "segment_id": segment_id,
            "detected_events": [],
            "loudness_db": 0.0,
            "processing_time_ms": (time.perf_counter() - start_time) * 1000,
            "error": str(e),
        }

    detected_events = result["detected_events"]
    loudness_db = result["loudness_db"]
    timestamp = datetime.now(timezone.utc)

    # Write to InfluxDB if events were detected
    if detected_events:
        events_written = write_audio_events(
            sensor_id=sensor_id,
            location=location,
            detected_events=detected_events,
            loudness_db=loudness_db,
            timestamp=timestamp,
        )
        logger.info(
            f"Segment {segment_id}: Detected {len(detected_events)} events, "
            f"wrote {events_written} to InfluxDB"
        )

        # Broadcast each event via WebSocket
        for event in detected_events:
            await broadcast_new_event({
                "time": timestamp.isoformat(),
                "sensor_id": sensor_id,
                "location": location,
                "event_type": event["label"],
                "confidence": event["confidence"],
                "loudness_db": loudness_db,
            })

    processing_time_ms = (time.perf_counter() - start_time) * 1000

    return {
        "status": "processed",
        "segment_id": segment_id,
        "detected_events": detected_events,
        "loudness_db": loudness_db,
        "processing_time_ms": round(processing_time_ms, 2),
    }
