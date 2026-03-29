"""Tests for TCP audio ingestion."""
import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.ingest.tcp_auth import validate_tcp_credentials
from app.ingest.tcp_server import (
    TCPAudioServer,
    ConnectionState,
    start_tcp_server,
    stop_tcp_server,
)


class TestTCPAuth:
    """Tests for TCP authentication."""

    def test_validate_credentials_no_keys_configured(self):
        """Should return False when no API keys are configured."""
        with patch("app.ingest.tcp_auth.parse_sensor_api_keys", return_value={}):
            assert validate_tcp_credentials("sensor_001", "key123") is False

    def test_validate_credentials_valid_key_only(self):
        """Should validate when just the key is provided."""
        with patch(
            "app.ingest.tcp_auth.parse_sensor_api_keys",
            return_value={"sensor_001": "key123"},
        ):
            assert validate_tcp_credentials("sensor_001", "key123") is True

    def test_validate_credentials_valid_sensor_key_format(self):
        """Should validate when key is in sensor_id:key format."""
        with patch(
            "app.ingest.tcp_auth.parse_sensor_api_keys",
            return_value={"sensor_001": "key123"},
        ):
            assert validate_tcp_credentials("sensor_001", "sensor_001:key123") is True

    def test_validate_credentials_wrong_key(self):
        """Should reject invalid API key."""
        with patch(
            "app.ingest.tcp_auth.parse_sensor_api_keys",
            return_value={"sensor_001": "key123"},
        ):
            assert validate_tcp_credentials("sensor_001", "wrongkey") is False

    def test_validate_credentials_wrong_sensor(self):
        """Should reject unknown sensor."""
        with patch(
            "app.ingest.tcp_auth.parse_sensor_api_keys",
            return_value={"sensor_001": "key123"},
        ):
            assert validate_tcp_credentials("sensor_002", "key123") is False

    def test_validate_credentials_mismatched_sensor_in_key(self):
        """Should reject when sensor_id in key doesn't match."""
        with patch(
            "app.ingest.tcp_auth.parse_sensor_api_keys",
            return_value={"sensor_001": "key123"},
        ):
            assert validate_tcp_credentials("sensor_001", "sensor_002:key123") is False


class TestConnectionState:
    """Tests for ConnectionState dataclass."""

    def test_default_state(self):
        """Should initialize with correct defaults."""
        state = ConnectionState()
        assert state.sensor_id == ""
        assert state.location == ""
        assert state.buffer == bytearray()
        assert state.authenticated is False

    def test_buffer_accumulation(self):
        """Should allow buffer to accumulate data."""
        state = ConnectionState()
        state.buffer.extend(b"hello")
        state.buffer.extend(b"world")
        assert bytes(state.buffer) == b"helloworld"


class TestTCPAudioServer:
    """Tests for TCPAudioServer class."""

    def test_segment_bytes_calculation(self):
        """Should calculate correct segment size."""
        with patch("app.ingest.tcp_server.get_settings") as mock_settings:
            mock_settings.return_value.audio_sample_rate = 16000
            mock_settings.return_value.audio_segment_duration_sec = 3.0
            mock_settings.return_value.tcp_ingest_port = 8001

            server = TCPAudioServer()

            # 16000 samples/sec * 3 sec * 2 bytes/sample = 96000 bytes
            assert server.segment_bytes == 96000

    def test_segment_bytes_1_second(self):
        """Should calculate correct segment size for 1 second."""
        with patch("app.ingest.tcp_server.get_settings") as mock_settings:
            mock_settings.return_value.audio_sample_rate = 16000
            mock_settings.return_value.audio_segment_duration_sec = 1.0
            mock_settings.return_value.tcp_ingest_port = 8001

            server = TCPAudioServer()

            # 16000 samples/sec * 1 sec * 2 bytes/sample = 32000 bytes
            assert server.segment_bytes == 32000


@pytest.mark.asyncio
class TestTCPServerIntegration:
    """Integration tests for TCP server."""

    async def test_server_start_stop(self):
        """Should start and stop without errors."""
        with patch("app.ingest.tcp_server.get_settings") as mock_settings:
            mock_settings.return_value.audio_sample_rate = 16000
            mock_settings.return_value.audio_segment_duration_sec = 3.0
            mock_settings.return_value.tcp_ingest_port = 18001  # Use alternate port

            server = TCPAudioServer(port=18001)
            await server.start()
            assert server._server is not None

            await server.stop()
            assert server._server.is_serving() is False

    async def test_authentication_success(self):
        """Should authenticate valid credentials and return buffer size."""
        with patch("app.ingest.tcp_server.get_settings") as mock_settings:
            mock_settings.return_value.audio_sample_rate = 16000
            mock_settings.return_value.audio_segment_duration_sec = 3.0
            mock_settings.return_value.tcp_ingest_port = 18002

            with patch(
                "app.ingest.tcp_server.validate_tcp_credentials",
                return_value=True,
            ):
                server = TCPAudioServer(port=18002)
                await server.start()

                try:
                    # Connect as client
                    reader, writer = await asyncio.open_connection("127.0.0.1", 18002)

                    # Send handshake
                    handshake = {
                        "sensor_id": "sensor_001",
                        "api_key": "key123",
                        "location": "ICU",
                    }
                    writer.write(json.dumps(handshake).encode() + b"\n")
                    await writer.drain()

                    # Read response
                    response_line = await asyncio.wait_for(
                        reader.readline(), timeout=5.0
                    )
                    response = json.loads(response_line.decode())

                    assert response["status"] == "authenticated"
                    assert response["buffer_size_bytes"] == 96000

                    writer.close()
                    await writer.wait_closed()
                finally:
                    await server.stop()

    async def test_authentication_failure(self):
        """Should reject invalid credentials."""
        with patch("app.ingest.tcp_server.get_settings") as mock_settings:
            mock_settings.return_value.audio_sample_rate = 16000
            mock_settings.return_value.audio_segment_duration_sec = 3.0
            mock_settings.return_value.tcp_ingest_port = 18003

            with patch(
                "app.ingest.tcp_server.validate_tcp_credentials",
                return_value=False,
            ):
                server = TCPAudioServer(port=18003)
                await server.start()

                try:
                    reader, writer = await asyncio.open_connection("127.0.0.1", 18003)

                    handshake = {
                        "sensor_id": "sensor_001",
                        "api_key": "wrongkey",
                        "location": "ICU",
                    }
                    writer.write(json.dumps(handshake).encode() + b"\n")
                    await writer.drain()

                    response_line = await asyncio.wait_for(
                        reader.readline(), timeout=5.0
                    )
                    response = json.loads(response_line.decode())

                    assert response["status"] == "error"
                    assert "Authentication failed" in response["message"]

                    writer.close()
                    await writer.wait_closed()
                finally:
                    await server.stop()

    async def test_invalid_json_handshake(self):
        """Should reject invalid JSON in handshake."""
        with patch("app.ingest.tcp_server.get_settings") as mock_settings:
            mock_settings.return_value.audio_sample_rate = 16000
            mock_settings.return_value.audio_segment_duration_sec = 3.0
            mock_settings.return_value.tcp_ingest_port = 18004

            server = TCPAudioServer(port=18004)
            await server.start()

            try:
                reader, writer = await asyncio.open_connection("127.0.0.1", 18004)

                # Send invalid JSON
                writer.write(b"not valid json\n")
                await writer.drain()

                response_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
                response = json.loads(response_line.decode())

                assert response["status"] == "error"
                assert "Invalid JSON" in response["message"]

                writer.close()
                await writer.wait_closed()
            finally:
                await server.stop()

    async def test_missing_handshake_fields(self):
        """Should reject handshake missing required fields."""
        with patch("app.ingest.tcp_server.get_settings") as mock_settings:
            mock_settings.return_value.audio_sample_rate = 16000
            mock_settings.return_value.audio_segment_duration_sec = 3.0
            mock_settings.return_value.tcp_ingest_port = 18005

            server = TCPAudioServer(port=18005)
            await server.start()

            try:
                reader, writer = await asyncio.open_connection("127.0.0.1", 18005)

                # Send handshake missing location
                handshake = {"sensor_id": "sensor_001", "api_key": "key123"}
                writer.write(json.dumps(handshake).encode() + b"\n")
                await writer.drain()

                response_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
                response = json.loads(response_line.decode())

                assert response["status"] == "error"
                assert "Missing required fields" in response["message"]

                writer.close()
                await writer.wait_closed()
            finally:
                await server.stop()

    async def test_audio_streaming_triggers_inference(self):
        """Should trigger inference when segment threshold is reached."""
        with patch("app.ingest.tcp_server.get_settings") as mock_settings:
            mock_settings.return_value.audio_sample_rate = 16000
            mock_settings.return_value.audio_segment_duration_sec = 0.1  # Small for test
            mock_settings.return_value.tcp_ingest_port = 18006

            # 16000 * 0.1 * 2 = 3200 bytes
            expected_segment_size = 3200

            with patch(
                "app.ingest.tcp_server.validate_tcp_credentials",
                return_value=True,
            ):
                with patch(
                    "app.ingest.tcp_server.process_audio_segment",
                    new_callable=AsyncMock,
                ) as mock_process:
                    mock_process.return_value = {"detected_events": []}

                    server = TCPAudioServer(port=18006)
                    await server.start()

                    try:
                        reader, writer = await asyncio.open_connection(
                            "127.0.0.1", 18006
                        )

                        # Authenticate
                        handshake = {
                            "sensor_id": "sensor_001",
                            "api_key": "key123",
                            "location": "ICU",
                        }
                        writer.write(json.dumps(handshake).encode() + b"\n")
                        await writer.drain()
                        await reader.readline()

                        # Send exactly one segment worth of audio
                        audio_data = b"\x00" * expected_segment_size
                        writer.write(audio_data)
                        await writer.drain()

                        # Give server time to process
                        await asyncio.sleep(0.2)

                        # Verify inference was called
                        mock_process.assert_called_once()
                        call_args = mock_process.call_args
                        assert len(call_args.kwargs["pcm_bytes"]) == expected_segment_size
                        assert call_args.kwargs["sensor_id"] == "sensor_001"
                        assert call_args.kwargs["location"] == "ICU"

                        writer.close()
                        await writer.wait_closed()
                    finally:
                        await server.stop()


@pytest.mark.asyncio
class TestGlobalServerFunctions:
    """Tests for global start/stop functions."""

    async def test_start_and_stop_tcp_server(self):
        """Should start and stop global server."""
        with patch("app.ingest.tcp_server.get_settings") as mock_settings:
            mock_settings.return_value.audio_sample_rate = 16000
            mock_settings.return_value.audio_segment_duration_sec = 3.0
            mock_settings.return_value.tcp_ingest_port = 18007

            server = await start_tcp_server()
            assert server is not None
            assert server._server.is_serving()

            await stop_tcp_server()
