"""API key authentication for sensor ingestion."""
import logging
from fastapi import HTTPException, Header, status

from app.config import get_settings

logger = logging.getLogger(__name__)


def parse_sensor_api_keys() -> dict[str, str]:
    """
    Parse sensor API keys from configuration.

    Format: "sensor_001:key123,sensor_002:key456"

    Returns:
        Dict mapping sensor_id to api_key
    """
    settings = get_settings()
    keys_str = settings.sensor_api_keys

    if not keys_str:
        return {}

    result = {}
    for pair in keys_str.split(","):
        pair = pair.strip()
        if ":" in pair:
            sensor_id, api_key = pair.split(":", 1)
            result[sensor_id.strip()] = api_key.strip()

    return result


async def validate_sensor_api_key(
    x_api_key: str = Header(..., description="Sensor API key in format 'sensor_id:key'"),
    x_sensor_id: str = Header(..., description="Sensor identifier"),
    x_location: str = Header(..., description="Physical location of sensor"),
) -> dict:
    """
    Validate the sensor API key and return sensor info.

    Headers:
        X-API-Key: The API key (format: "sensor_id:key" or just "key")
        X-Sensor-ID: The sensor identifier
        X-Location: The sensor's physical location

    Returns:
        Dict with sensor_id and location

    Raises:
        HTTPException 401 if authentication fails
    """
    valid_keys = parse_sensor_api_keys()

    if not valid_keys:
        logger.warning("No sensor API keys configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sensor authentication not configured",
        )

    # Check if the API key matches
    # Key format can be "sensor_id:key" or just "key"
    is_valid = False

    if ":" in x_api_key:
        # Format: "sensor_id:key"
        key_sensor_id, key = x_api_key.split(":", 1)
        if key_sensor_id == x_sensor_id and valid_keys.get(x_sensor_id) == key:
            is_valid = True
    else:
        # Format: just "key"
        if valid_keys.get(x_sensor_id) == x_api_key:
            is_valid = True

    if not is_valid:
        logger.warning(f"Invalid API key for sensor: {x_sensor_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return {
        "sensor_id": x_sensor_id,
        "location": x_location,
    }
