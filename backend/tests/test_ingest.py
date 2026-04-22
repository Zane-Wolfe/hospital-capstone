"""Tests for the ingestion module."""
import struct
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.ingest.auth import parse_sensor_api_keys, validate_sensor_api_key
from app.ingest.schemas import IngestResponse, DetectedEvent


class TestApiKeyParsing:
    """Tests for API key parsing."""

    def test_parse_empty_keys(self):
        """Test parsing empty API keys string."""
        with patch("app.ingest.auth.get_settings") as mock_settings:
            mock_settings.return_value.sensor_api_keys = ""
            result = parse_sensor_api_keys()
            assert result == {}

    def test_parse_single_key(self):
        """Test parsing single API key."""
        with patch("app.ingest.auth.get_settings") as mock_settings:
            mock_settings.return_value.sensor_api_keys = "sensor_001:key123"
            result = parse_sensor_api_keys()
            assert result == {"sensor_001": "key123"}

    def test_parse_multiple_keys(self):
        """Test parsing multiple API keys."""
        with patch("app.ingest.auth.get_settings") as mock_settings:
            mock_settings.return_value.sensor_api_keys = (
                "sensor_001:key123,sensor_002:key456"
            )
            result = parse_sensor_api_keys()
            assert result == {"sensor_001": "key123", "sensor_002": "key456"}

    def test_parse_keys_with_whitespace(self):
        """Test parsing API keys with extra whitespace."""
        with patch("app.ingest.auth.get_settings") as mock_settings:
            mock_settings.return_value.sensor_api_keys = (
                " sensor_001 : key123 , sensor_002 : key456 "
            )
            result = parse_sensor_api_keys()
            assert result == {"sensor_001": "key123", "sensor_002": "key456"}


class TestApiKeyValidation:
    """Tests for API key validation."""

    @pytest.fixture
    def mock_valid_keys(self):
        """Mock valid API keys."""
        with patch("app.ingest.auth.parse_sensor_api_keys") as mock:
            mock.return_value = {"sensor_001": "key123", "sensor_002": "key456"}
            yield mock

    @pytest.mark.asyncio
    async def test_valid_key_format_with_sensor_id(self, mock_valid_keys):
        """Test validation with 'sensor_id:key' format."""
        result = await validate_sensor_api_key(
            x_api_key="sensor_001:key123",
            x_sensor_id="sensor_001",
            x_location="ICU-Room-101",
        )
        assert result["sensor_id"] == "sensor_001"
        assert result["location"] == "ICU-Room-101"

    @pytest.mark.asyncio
    async def test_valid_key_format_without_sensor_id(self, mock_valid_keys):
        """Test validation with just 'key' format."""
        result = await validate_sensor_api_key(
            x_api_key="key123",
            x_sensor_id="sensor_001",
            x_location="ICU-Room-101",
        )
        assert result["sensor_id"] == "sensor_001"
        assert result["location"] == "ICU-Room-101"

    @pytest.mark.asyncio
    async def test_invalid_key(self, mock_valid_keys):
        """Test validation with invalid key."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await validate_sensor_api_key(
                x_api_key="wrong_key",
                x_sensor_id="sensor_001",
                x_location="ICU-Room-101",
            )
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_mismatched_sensor_id(self, mock_valid_keys):
        """Test validation with mismatched sensor ID."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await validate_sensor_api_key(
                x_api_key="sensor_001:key123",
                x_sensor_id="sensor_002",  # Wrong sensor
                x_location="ICU-Room-101",
            )
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_no_keys_configured(self):
        """Test validation when no keys are configured."""
        from fastapi import HTTPException

        with patch("app.ingest.auth.parse_sensor_api_keys") as mock:
            mock.return_value = {}
            with pytest.raises(HTTPException) as exc_info:
                await validate_sensor_api_key(
                    x_api_key="key123",
                    x_sensor_id="sensor_001",
                    x_location="ICU-Room-101",
                )
            assert exc_info.value.status_code == 500


class TestIngestEndpoint:
    """Tests for the ingestion endpoint."""

    @pytest.fixture
    def mock_inference(self):
        """Mock the inference engine."""
        with patch("app.ingest.service.get_inference") as mock:
            mock_engine = MagicMock()
            mock_engine.predict.return_value = {
                "detected_events": [
                    {"label": "alarm", "confidence": 0.92},
                    {"label": "speech", "confidence": 0.78},
                ],
                "all_probabilities": {
                    "alarm": 0.92,
                    "speech": 0.78,
                    "silence": 0.15,
                },
                "loudness_dba": -24.5,
            }
            mock.return_value = mock_engine
            yield mock_engine

    @pytest.fixture
    def mock_write_events(self):
        """Mock InfluxDB write."""
        with patch("app.ingest.service.write_audio_events") as mock:
            mock.return_value = 2  # 2 events written
            yield mock

    @pytest.fixture
    def mock_broadcast(self):
        """Mock WebSocket broadcast."""
        with patch("app.ingest.service.broadcast_new_event") as mock:
            mock.return_value = AsyncMock()
            yield mock

    @pytest.mark.asyncio
    async def test_process_audio_segment(
        self, mock_inference, mock_write_events, mock_broadcast
    ):
        """Test audio segment processing."""
        from app.ingest.service import process_audio_segment

        # Create 1 second of 16kHz audio (32KB)
        num_samples = 16000
        pcm_bytes = struct.pack(f"<{num_samples}h", *([0] * num_samples))

        result = await process_audio_segment(
            pcm_bytes=pcm_bytes,
            sensor_id="sensor_001",
            location="ICU-Room-101",
        )

        assert result["status"] == "processed"
        assert "segment_id" in result
        assert len(result["detected_events"]) == 2
        assert result["loudness_dba"] == -24.5
        assert result["processing_time_ms"] > 0

        # Verify inference was called
        mock_inference.predict.assert_called_once()

        # Verify events were written to InfluxDB
        mock_write_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_audio_no_model(self, mock_write_events, mock_broadcast):
        """Test handling when model is not loaded."""
        from app.ingest.service import process_audio_segment

        with patch("app.ingest.service.get_inference") as mock:
            mock.return_value = None

            num_samples = 16000
            pcm_bytes = struct.pack(f"<{num_samples}h", *([0] * num_samples))

            result = await process_audio_segment(
                pcm_bytes=pcm_bytes,
                sensor_id="sensor_001",
                location="ICU-Room-101",
            )

            assert result["status"] == "error"
            assert "Model not loaded" in result.get("error", "")


class TestIngestHealthEndpoint:
    """Tests for the ingestion health endpoint."""

    def test_health_with_model(self, client):
        """Test health endpoint when model is loaded."""
        with patch("app.ingest.router.get_inference") as mock_inference:
            mock_engine = MagicMock()
            mock_engine.health_check.return_value = {
                "model_loaded": True,
                "device": "cpu",
                "num_classes": 3,
                "classes": ["alarm", "speech", "silence"],
            }
            mock_inference.return_value = mock_engine

            with patch("app.ingest.router.get_influx_client") as mock_influx:
                mock_client = MagicMock()
                mock_client.ping.return_value = True
                mock_influx.return_value = mock_client

                response = client.get("/api/ingest/health")

                assert response.status_code == 200
                data = response.json()
                assert data["model_loaded"] is True
                assert data["influxdb_connected"] is True

    def test_health_without_model(self, client):
        """Test health endpoint when model is not loaded."""
        with patch("app.ingest.router.get_inference") as mock:
            mock.return_value = None

            response = client.get("/api/ingest/health")

            assert response.status_code == 200
            data = response.json()
            assert data["model_loaded"] is False
            assert data["num_classes"] == 0


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_detected_event_validation(self):
        """Test DetectedEvent schema validation."""
        event = DetectedEvent(label="alarm", confidence=0.92)
        assert event.label == "alarm"
        assert event.confidence == 0.92

    def test_detected_event_confidence_bounds(self):
        """Test confidence value bounds."""
        from pydantic import ValidationError

        # Valid values
        DetectedEvent(label="test", confidence=0.0)
        DetectedEvent(label="test", confidence=1.0)

        # Invalid values
        with pytest.raises(ValidationError):
            DetectedEvent(label="test", confidence=1.5)
        with pytest.raises(ValidationError):
            DetectedEvent(label="test", confidence=-0.1)

    def test_ingest_response_structure(self):
        """Test IngestResponse schema."""
        response = IngestResponse(
            status="processed",
            segment_id="uuid-123",
            detected_events=[
                DetectedEvent(label="alarm", confidence=0.92),
            ],
            loudness_dba=-24.5,
            processing_time_ms=45.0,
        )
        assert response.status == "processed"
        assert len(response.detected_events) == 1
