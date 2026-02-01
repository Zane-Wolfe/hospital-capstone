import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.config import get_settings
from app.auth.service import create_tokens


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers with a valid JWT token."""
    tokens = create_tokens("admin")
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def mock_influx_client():
    """Mock the InfluxDB client for testing."""
    with patch("app.db.influx.get_influx_client") as mock:
        mock_client = MagicMock()
        mock_query_api = MagicMock()
        mock_client.query_api.return_value = mock_query_api
        mock.return_value = mock_client
        yield mock_client, mock_query_api


@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        "time": "2024-01-15T10:30:00Z",
        "sensor_id": "sensor_001",
        "location": "ICU",
        "event_type": "alarm",
        "loudness": 75.5,
        "confidence": 0.92,
    }


@pytest.fixture
def sample_events_list(sample_event_data):
    """Sample list of events for testing."""
    return [
        sample_event_data,
        {
            "time": "2024-01-15T10:31:00Z",
            "sensor_id": "sensor_002",
            "location": "ER",
            "event_type": "speech",
            "loudness": 55.0,
            "confidence": 0.88,
        },
        {
            "time": "2024-01-15T10:32:00Z",
            "sensor_id": "sensor_001",
            "location": "ICU",
            "event_type": "cough",
            "loudness": 60.0,
            "confidence": 0.95,
        },
    ]
