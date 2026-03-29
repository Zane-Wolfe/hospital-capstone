"""TCP authentication utilities for sensor connections."""
import logging

from app.ingest.auth import parse_sensor_api_keys

logger = logging.getLogger(__name__)


def validate_tcp_credentials(sensor_id: str, api_key: str) -> bool:
    """
    Validate TCP connection credentials.

    Args:
        sensor_id: The sensor identifier
        api_key: The API key (can be "sensor_id:key" format or just "key")

    Returns:
        True if credentials are valid, False otherwise
    """
    valid_keys = parse_sensor_api_keys()

    if not valid_keys:
        logger.warning("No sensor API keys configured")
        return False

    # Check if the API key matches
    # Key format can be "sensor_id:key" or just "key"
    if ":" in api_key:
        # Format: "sensor_id:key"
        key_sensor_id, key = api_key.split(":", 1)
        if key_sensor_id == sensor_id and valid_keys.get(sensor_id) == key:
            return True
    else:
        # Format: just "key"
        if valid_keys.get(sensor_id) == api_key:
            return True

    logger.warning(f"Invalid TCP credentials for sensor: {sensor_id}")
    return False
