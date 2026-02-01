"""InfluxDB write operations for audio events."""
import logging
from datetime import datetime, timezone

from influxdb_client import Point

from app.config import get_settings
from app.db.influx import get_write_api

logger = logging.getLogger(__name__)


def write_audio_event(
    sensor_id: str,
    location: str,
    event_type: str,
    confidence: float,
    loudness_db: float,
    timestamp: datetime | None = None,
) -> bool:
    """
    Write a single audio event to InfluxDB.

    Args:
        sensor_id: ID of the sensor that detected the event
        location: Physical location of the sensor
        event_type: Type of event detected (e.g., 'alarm', 'speech')
        confidence: Confidence score (0.0 - 1.0)
        loudness_db: Loudness in dBFS
        timestamp: Event timestamp (defaults to now)

    Returns:
        True if write was successful, False otherwise
    """
    settings = get_settings()

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    point = (
        Point("audio_events")
        .tag("sensor_id", sensor_id)
        .tag("location", location)
        .tag("event_type", event_type)
        .field("confidence", confidence)
        .field("loudness_db", loudness_db)
        .time(timestamp)
    )

    try:
        write_api = get_write_api()
        write_api.write(bucket=settings.influxdb_bucket, record=point)
        logger.debug(
            f"Wrote event: sensor={sensor_id}, location={location}, "
            f"type={event_type}, confidence={confidence:.2f}"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to write audio event to InfluxDB: {e}")
        return False


def write_audio_events(
    sensor_id: str,
    location: str,
    detected_events: list[dict],
    loudness_db: float,
    timestamp: datetime | None = None,
) -> int:
    """
    Write multiple detected events to InfluxDB (multi-label support).

    Args:
        sensor_id: ID of the sensor
        location: Physical location of the sensor
        detected_events: List of dicts with 'label' and 'confidence' keys
        loudness_db: Loudness in dBFS
        timestamp: Event timestamp (defaults to now)

    Returns:
        Number of events successfully written
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    successful = 0
    for event in detected_events:
        if write_audio_event(
            sensor_id=sensor_id,
            location=location,
            event_type=event["label"],
            confidence=event["confidence"],
            loudness_db=loudness_db,
            timestamp=timestamp,
        ):
            successful += 1

    return successful
