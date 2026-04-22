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
    loudness_dba: float,
    timestamp: datetime | None = None,
) -> bool:
    """
    Write a single audio event to InfluxDB.

    Args:
        sensor_id: ID of the sensor that detected the event
        location: Physical location of the sensor
        event_type: Type of event detected (e.g., 'alarm', 'speech')
        confidence: Confidence score (0.0 - 1.0)
        loudness_dba: A-weighted loudness in absolute dBA
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
        .field("loudness_dba", loudness_dba)
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
    loudness_dba: float,
    timestamp: datetime | None = None,
) -> int:
    """
    Write multiple detected events to InfluxDB (multi-label support).

    Args:
        sensor_id: ID of the sensor
        location: Physical location of the sensor
        detected_events: List of dicts with 'label' and 'confidence' keys
        loudness_dba: A-weighted loudness in absolute dBA
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
            loudness_dba=loudness_dba,
            timestamp=timestamp,
        ):
            successful += 1

    return successful


def write_audio_level(
    sensor_id: str,
    location: str,
    loudness_dba: float,
    timestamp: datetime | None = None,
) -> bool:
    """Write a continuous audio level sample in dBA to InfluxDB for every processed segment."""
    settings = get_settings()

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    point = (
        Point("audio_level")
        .tag("sensor_id", sensor_id)
        .tag("location", location)
        .field("loudness_dba", loudness_dba)
        .time(timestamp)
    )

    try:
        write_api = get_write_api()
        write_api.write(bucket=settings.influxdb_bucket, record=point)
        return True
    except Exception as e:
        logger.error(f"Failed to write audio level to InfluxDB: {e}")
        return False


def write_heartbeat(
    sensor_id: str,
    location: str,
    battery_percent: float | None = None,
    bandwidth_kbps: float | None = None,
    signal_strength_dbm: float | None = None,
    timestamp: datetime | None = None,
) -> bool:
    """Write heartbeat metrics to InfluxDB for time series tracking."""
    settings = get_settings()

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    point = (
        Point("device_heartbeat")
        .tag("sensor_id", sensor_id)
        .tag("location", location or "unknown")
    )

    # Add fields (only if provided)
    if battery_percent is not None:
        point = point.field("battery_percent", battery_percent)
    if bandwidth_kbps is not None:
        point = point.field("bandwidth_kbps", bandwidth_kbps)
    if signal_strength_dbm is not None:
        point = point.field("signal_strength_dbm", signal_strength_dbm)

    point = point.time(timestamp)

    try:
        write_api = get_write_api()
        write_api.write(bucket=settings.influxdb_bucket, record=point)
        return True
    except Exception as e:
        logger.error(f"Failed to write heartbeat to InfluxDB: {e}")
        return False
