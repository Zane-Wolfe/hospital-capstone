#!/usr/bin/env python3
"""
Microphone Sensor Simulator

Simulates an ESP32 sensor by capturing audio from your microphone
and streaming it to the backend via TCP for classification.

Requirements:
    pip install sounddevice numpy requests

Usage:
    python mic_sensor_simulator.py
    python mic_sensor_simulator.py --sensor-id my_sensor --location "Living Room"
    python mic_sensor_simulator.py --list-devices
"""

import argparse
import json
import signal
import socket
import struct
import sys
import threading
import time
from datetime import datetime

try:
    import numpy as np
    import requests
    import sounddevice as sd
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("\nInstall requirements with:")
    print("  pip install sounddevice numpy requests")
    sys.exit(1)


# Default configuration
DEFAULT_CONFIG = {
    "backend_host": "localhost",
    "tcp_port": 8001,
    "http_port": 8000,
    "sensor_id": "mic_simulator",
    "location": "Desktop",
    "api_key": "key123",  # Must match SENSOR_API_KEYS in .env
    "sample_rate": 16000,
    "segment_duration": 1.0,  # seconds - must match backend AUDIO_SEGMENT_DURATION_SEC
    "channels": 1,
    "heartbeat_interval": 30,  # seconds
}


class MicrophoneSensor:
    """Simulates an ESP32 sensor using the computer's microphone via TCP streaming."""

    def __init__(
        self,
        host: str,
        tcp_port: int,
        http_port: int,
        sensor_id: str,
        location: str,
        api_key: str,
        sample_rate: int = 16000,
        segment_duration: float = 1.0,
        device: int | None = None,
        heartbeat_interval: int = 30,
    ):
        self.host = host
        self.tcp_port = tcp_port
        self.http_port = http_port
        self.sensor_id = sensor_id
        self.location = location
        self.api_key = api_key
        self.sample_rate = sample_rate
        self.segment_duration = segment_duration
        self.device = device
        self.heartbeat_interval = heartbeat_interval
        self.running = False
        self._socket: socket.socket | None = None
        self._heartbeat_thread: threading.Thread | None = None

        # Calculate samples per segment
        self.samples_per_segment = int(sample_rate * segment_duration)
        # 16-bit PCM = 2 bytes per sample
        self.bytes_per_segment = self.samples_per_segment * 2

    def _audio_to_pcm_bytes(self, audio: np.ndarray) -> bytes:
        """Convert numpy audio array to 16-bit PCM bytes."""
        # Ensure mono
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # Normalize and convert to 16-bit signed integers
        audio = np.clip(audio, -1.0, 1.0)
        audio_int16 = (audio * 32767).astype(np.int16)

        # Pack as little-endian 16-bit integers
        return struct.pack(f"<{len(audio_int16)}h", *audio_int16)

    def _connect_tcp(self) -> bool:
        """Establish TCP connection and authenticate."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.host, self.tcp_port))
            self._socket.settimeout(10.0)

            # Send handshake
            handshake = {
                "sensor_id": self.sensor_id,
                "api_key": self.api_key,
                "location": self.location,
            }
            handshake_bytes = json.dumps(handshake).encode("utf-8") + b"\n"
            self._socket.sendall(handshake_bytes)

            # Read response
            response_data = b""
            while b"\n" not in response_data:
                chunk = self._socket.recv(1024)
                if not chunk:
                    raise ConnectionError("Connection closed during handshake")
                response_data += chunk

            response = json.loads(response_data.decode("utf-8").strip())

            if response.get("status") == "authenticated":
                buffer_size = response.get("buffer_size_bytes", self.bytes_per_segment)
                print(f"[OK] Authenticated. Server buffer size: {buffer_size} bytes")
                # Remove timeout for streaming
                self._socket.settimeout(None)
                return True
            else:
                error_msg = response.get("message", "Unknown error")
                print(f"[ERROR] Authentication failed: {error_msg}")
                return False

        except socket.timeout:
            print(f"[ERROR] Connection timeout to {self.host}:{self.tcp_port}")
            return False
        except ConnectionRefusedError:
            print(f"[ERROR] Connection refused to {self.host}:{self.tcp_port}")
            print("        Is the backend running? Try: docker compose up")
            return False
        except Exception as e:
            print(f"[ERROR] TCP connection failed: {e}")
            return False

    def _disconnect_tcp(self):
        """Close TCP connection."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def _send_heartbeat(self):
        """Send HTTP heartbeat to device metrics endpoint."""
        url = f"http://{self.host}:{self.http_port}/api/device-metrics/heartbeat"
        headers = {
            "X-API-Key": self.api_key,
            "X-Sensor-ID": self.sensor_id,
            "X-Location": self.location,
            "Content-Type": "application/json",
        }
        payload = {
            "battery_percent": 100.0,  # Simulated - always full
            "bandwidth_kbps": 128.0,   # Simulated
            "signal_strength_dbm": -50.0,  # Simulated - strong signal
            "firmware_version": "simulator-1.0",
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            response.raise_for_status()
            print("[OK] Heartbeat sent successfully")
            return True
        except Exception as e:
            print(f"[WARN] Heartbeat failed: {e}")
            return False

    def _heartbeat_loop(self):
        """Background thread for sending periodic heartbeats."""
        while self.running:
            self._send_heartbeat()
            # Sleep in small intervals to check running flag
            for _ in range(self.heartbeat_interval):
                if not self.running:
                    break
                time.sleep(1)

    def _check_health(self) -> bool:
        """Check backend health via HTTP."""
        url = f"http://{self.host}:{self.http_port}/api/ingest/health"
        try:
            resp = requests.get(url, timeout=5)
            health = resp.json()
            if health.get("model_loaded"):
                print(f"[OK] Model loaded: {health.get('classes', [])}")
            else:
                print("[WARNING] Model not loaded - inference will fail")
            if health.get("influxdb_connected"):
                print("[OK] InfluxDB connected")
            else:
                print("[WARNING] InfluxDB not connected - events won't be stored")
            return True
        except Exception as e:
            print(f"[WARNING] Could not check health: {e}")
            return False

    def run_continuous(self):
        """Continuously capture and stream audio segments via TCP."""
        self.running = True
        segment_count = 0

        print(f"\n{'='*60}")
        print("MICROPHONE SENSOR SIMULATOR (TCP)")
        print(f"{'='*60}")
        print(f"Sensor ID:   {self.sensor_id}")
        print(f"Location:    {self.location}")
        print(f"TCP Server:  {self.host}:{self.tcp_port}")
        print(f"HTTP Server: {self.host}:{self.http_port}")
        print(f"Sample Rate: {self.sample_rate} Hz")
        print(f"Segment:     {self.segment_duration}s ({self.bytes_per_segment} bytes)")
        print(f"{'='*60}")
        print("\nPress Ctrl+C to stop\n")

        # Check backend health
        print("Checking backend health...")
        self._check_health()

        # Connect via TCP
        print(f"\nConnecting to TCP server at {self.host}:{self.tcp_port}...")
        if not self._connect_tcp():
            return

        # Start heartbeat thread
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        print(f"[OK] Heartbeat thread started (interval: {self.heartbeat_interval}s)")

        print(f"\n{'='*60}")
        print("STREAMING AUDIO...")
        print(f"{'='*60}\n")

        try:
            while self.running:
                try:
                    # Record one segment
                    audio = sd.rec(
                        self.samples_per_segment,
                        samplerate=self.sample_rate,
                        channels=1,
                        dtype=np.float32,
                        device=self.device,
                    )
                    sd.wait()  # Wait for recording to complete

                    if not self.running:
                        break

                    # Convert to PCM bytes
                    pcm_bytes = self._audio_to_pcm_bytes(audio.flatten())

                    # Calculate loudness (RMS in dB)
                    rms = np.sqrt(np.mean(audio**2))
                    db = 20 * np.log10(max(rms, 1e-10))

                    # Send to backend via TCP
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    segment_count += 1

                    try:
                        self._socket.sendall(pcm_bytes)
                        print(
                            f"[{timestamp}] #{segment_count:04d} | "
                            f"Sent {len(pcm_bytes)} bytes | "
                            f"Loudness: {db:.1f} dB"
                        )
                    except (BrokenPipeError, ConnectionResetError) as e:
                        print(f"\n[ERROR] Connection lost: {e}")
                        print("Attempting to reconnect...")
                        self._disconnect_tcp()
                        if self._connect_tcp():
                            print("[OK] Reconnected!")
                        else:
                            print("[ERROR] Reconnection failed. Stopping.")
                            break

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"[ERROR] Recording failed: {e}")
                    time.sleep(1)

        finally:
            self._disconnect_tcp()

        print(f"\n{'='*60}")
        print(f"Stopped. Sent {segment_count} segments.")
        print(f"{'='*60}")

    def stop(self):
        """Stop the continuous capture loop."""
        self.running = False
        self._disconnect_tcp()


def list_audio_devices():
    """List available audio input devices."""
    print("\nAvailable Audio Input Devices:")
    print("-" * 50)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            default = " (default)" if i == sd.default.device[0] else ""
            print(f"  [{i}] {device['name']}{default}")
            print(f"       Channels: {device['max_input_channels']}, Sample Rate: {device['default_samplerate']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Simulate an ESP32 sensor using your microphone (TCP streaming)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use defaults
  %(prog)s --sensor-id test_mic              # Custom sensor ID
  %(prog)s --location "Conference Room"      # Custom location
  %(prog)s --host 192.168.1.100              # Remote backend
  %(prog)s --list-devices                    # Show audio devices
  %(prog)s --device 2                        # Use specific microphone
        """,
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_CONFIG["backend_host"],
        help=f"Backend host (default: {DEFAULT_CONFIG['backend_host']})",
    )
    parser.add_argument(
        "--tcp-port",
        type=int,
        default=DEFAULT_CONFIG["tcp_port"],
        help=f"TCP port for audio streaming (default: {DEFAULT_CONFIG['tcp_port']})",
    )
    parser.add_argument(
        "--http-port",
        type=int,
        default=DEFAULT_CONFIG["http_port"],
        help=f"HTTP port for health/heartbeat (default: {DEFAULT_CONFIG['http_port']})",
    )
    parser.add_argument(
        "--sensor-id",
        default=DEFAULT_CONFIG["sensor_id"],
        help=f"Sensor identifier (default: {DEFAULT_CONFIG['sensor_id']})",
    )
    parser.add_argument(
        "--location",
        default=DEFAULT_CONFIG["location"],
        help=f"Sensor location (default: {DEFAULT_CONFIG['location']})",
    )
    parser.add_argument(
        "--api-key",
        default=DEFAULT_CONFIG["api_key"],
        help=f"API key (default: {DEFAULT_CONFIG['api_key']})",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=DEFAULT_CONFIG["sample_rate"],
        help=f"Sample rate in Hz (default: {DEFAULT_CONFIG['sample_rate']})",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_CONFIG["segment_duration"],
        help=f"Segment duration in seconds (default: {DEFAULT_CONFIG['segment_duration']})",
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=DEFAULT_CONFIG["heartbeat_interval"],
        help=f"Heartbeat interval in seconds (default: {DEFAULT_CONFIG['heartbeat_interval']})",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Audio input device index (use --list-devices to see options)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit",
    )

    args = parser.parse_args()

    if args.list_devices:
        list_audio_devices()
        sys.exit(0)

    # Ensure the sensor_id is in the API keys
    print(f"\n[NOTE] Make sure '{args.sensor_id}:{args.api_key}' is in your SENSOR_API_KEYS")
    print(f"       Example .env: SENSOR_API_KEYS={args.sensor_id}:{args.api_key}\n")

    sensor = MicrophoneSensor(
        host=args.host,
        tcp_port=args.tcp_port,
        http_port=args.http_port,
        sensor_id=args.sensor_id,
        location=args.location,
        api_key=args.api_key,
        sample_rate=args.sample_rate,
        segment_duration=args.duration,
        device=args.device,
        heartbeat_interval=args.heartbeat_interval,
    )

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\nStopping...")
        sensor.stop()

    signal.signal(signal.SIGINT, signal_handler)

    sensor.run_continuous()


if __name__ == "__main__":
    main()
