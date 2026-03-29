"""TCP server for streaming audio ingestion from ESP32 sensors."""
import asyncio
import json
import logging
from dataclasses import dataclass, field

from app.config import get_settings
from app.ingest.tcp_auth import validate_tcp_credentials
from app.ingest.service import process_audio_segment

logger = logging.getLogger(__name__)

# Authentication timeout in seconds
AUTH_TIMEOUT_SEC = 10.0


@dataclass
class ConnectionState:
    """State for a single TCP connection."""

    sensor_id: str = ""
    location: str = ""
    buffer: bytearray = field(default_factory=bytearray)
    authenticated: bool = False


class TCPAudioServer:
    """Asyncio TCP server for streaming audio ingestion."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8001):
        """
        Initialize the TCP server.

        Args:
            host: Host address to bind to
            port: Port number to bind to
        """
        self.host = host
        self.port = port
        self._server: asyncio.Server | None = None
        self._active_connections: set[asyncio.Task] = set()

        # Calculate segment size based on settings
        settings = get_settings()
        self.sample_rate = settings.audio_sample_rate
        self.segment_duration_sec = settings.audio_segment_duration_sec
        # 16-bit PCM = 2 bytes per sample
        self.segment_bytes = int(self.sample_rate * self.segment_duration_sec * 2)

        logger.info(
            f"TCP server configured: {self.segment_duration_sec}s segments, "
            f"{self.segment_bytes} bytes/segment"
        )

    async def start(self) -> None:
        """Start the TCP server."""
        self._server = await asyncio.start_server(
            self._handle_connection,
            self.host,
            self.port,
        )
        logger.info(f"TCP audio server started on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the TCP server and close all connections."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            logger.info("TCP audio server stopped")

        # Cancel all active connection handlers
        for task in self._active_connections:
            task.cancel()

        if self._active_connections:
            await asyncio.gather(*self._active_connections, return_exceptions=True)
            self._active_connections.clear()

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """
        Handle an incoming TCP connection.

        Protocol:
        1. Client sends JSON handshake: {"sensor_id": "...", "api_key": "...", "location": "..."}\n
        2. Server responds: {"status": "authenticated", "buffer_size_bytes": N}\n
        3. Client streams raw PCM (16-bit, 16kHz, mono)
        4. Server accumulates and triggers inference at segment_bytes threshold
        """
        peer = writer.get_extra_info("peername")
        logger.info(f"New TCP connection from {peer}")

        state = ConnectionState()

        # Track this connection
        current_task = asyncio.current_task()
        if current_task:
            self._active_connections.add(current_task)

        try:
            # Step 1: Authenticate
            if not await self._authenticate(reader, writer, state):
                return

            # Step 2: Stream audio
            await self._stream_audio(reader, writer, state)

        except asyncio.CancelledError:
            logger.info(f"Connection to {peer} cancelled")
        except ConnectionResetError:
            logger.info(f"Connection reset by {peer}")
        except Exception as e:
            logger.error(f"Error handling connection from {peer}: {e}")
        finally:
            # Discard incomplete buffer on disconnect
            if len(state.buffer) > 0:
                logger.info(
                    f"Discarding incomplete buffer ({len(state.buffer)} bytes) "
                    f"from {state.sensor_id}"
                )

            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

            if current_task:
                self._active_connections.discard(current_task)

            logger.info(f"Connection from {peer} closed")

    async def _authenticate(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        state: ConnectionState,
    ) -> bool:
        """
        Perform JSON handshake authentication.

        Expected format: {"sensor_id": "...", "api_key": "...", "location": "..."}\n

        Returns:
            True if authentication succeeded, False otherwise
        """
        peer = writer.get_extra_info("peername")

        try:
            # Read handshake with timeout
            line = await asyncio.wait_for(
                reader.readline(),
                timeout=AUTH_TIMEOUT_SEC,
            )

            if not line:
                logger.warning(f"Empty handshake from {peer}")
                await self._send_error(writer, "Empty handshake")
                return False

            # Parse JSON
            try:
                handshake = json.loads(line.decode("utf-8").strip())
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON handshake from {peer}: {e}")
                await self._send_error(writer, "Invalid JSON")
                return False

            # Validate required fields
            sensor_id = handshake.get("sensor_id")
            api_key = handshake.get("api_key")
            location = handshake.get("location")

            if not all([sensor_id, api_key, location]):
                logger.warning(f"Missing handshake fields from {peer}")
                await self._send_error(writer, "Missing required fields")
                return False

            # Validate credentials
            if not validate_tcp_credentials(sensor_id, api_key):
                logger.warning(f"Authentication failed for sensor {sensor_id} from {peer}")
                await self._send_error(writer, "Authentication failed")
                return False

            # Authentication successful
            state.sensor_id = sensor_id
            state.location = location
            state.authenticated = True

            # Send success response
            response = {
                "status": "authenticated",
                "buffer_size_bytes": self.segment_bytes,
            }
            writer.write(json.dumps(response).encode("utf-8") + b"\n")
            await writer.drain()

            logger.info(f"Sensor {sensor_id} authenticated from {peer}")
            return True

        except asyncio.TimeoutError:
            logger.warning(f"Authentication timeout from {peer}")
            await self._send_error(writer, "Authentication timeout")
            return False

    async def _stream_audio(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        state: ConnectionState,
    ) -> None:
        """
        Stream audio data, accumulate in buffer, trigger inference at threshold.
        """
        peer = writer.get_extra_info("peername")
        logger.info(
            f"Starting audio stream from {state.sensor_id} "
            f"(segment size: {self.segment_bytes} bytes)"
        )

        while True:
            # Read available data (up to 4KB at a time)
            try:
                data = await reader.read(4096)
            except ConnectionResetError:
                break

            if not data:
                # EOF - client disconnected
                break

            # Accumulate in buffer
            state.buffer.extend(data)

            # Process complete segments
            while len(state.buffer) >= self.segment_bytes:
                # Extract one segment
                segment = bytes(state.buffer[: self.segment_bytes])
                del state.buffer[: self.segment_bytes]

                # Process the segment
                try:
                    result = await process_audio_segment(
                        pcm_bytes=segment,
                        sensor_id=state.sensor_id,
                        location=state.location,
                    )

                    events_count = len(result.get("detected_events", []))
                    logger.debug(
                        f"Processed segment from {state.sensor_id}: "
                        f"{events_count} events detected"
                    )

                except Exception as e:
                    logger.error(
                        f"Error processing audio from {state.sensor_id}: {e}"
                    )

    async def _send_error(
        self,
        writer: asyncio.StreamWriter,
        message: str,
    ) -> None:
        """Send an error response to the client."""
        response = {"status": "error", "message": message}
        try:
            writer.write(json.dumps(response).encode("utf-8") + b"\n")
            await writer.drain()
        except Exception:
            pass


# Global TCP server instance
_tcp_server: TCPAudioServer | None = None


async def start_tcp_server() -> TCPAudioServer:
    """Start the global TCP audio server."""
    global _tcp_server

    settings = get_settings()
    _tcp_server = TCPAudioServer(
        host="0.0.0.0",
        port=settings.tcp_ingest_port,
    )
    await _tcp_server.start()
    return _tcp_server


async def stop_tcp_server() -> None:
    """Stop the global TCP audio server."""
    global _tcp_server

    if _tcp_server is not None:
        await _tcp_server.stop()
        _tcp_server = None


def get_tcp_server() -> TCPAudioServer | None:
    """Get the global TCP server instance."""
    return _tcp_server
