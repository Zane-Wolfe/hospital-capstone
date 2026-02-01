#!/usr/bin/env python3
"""
Microphone Sensor Simulator

Simulates an ESP32 sensor by capturing audio from your microphone
and sending it to the backend API for classification.

Requirements:
    pip install sounddevice numpy requests

Usage:
    python mic_sensor_simulator.py
    python mic_sensor_simulator.py --sensor-id my_sensor --location "Living Room"
    python mic_sensor_simulator.py --list-devices
"""

import argparse
import signal
import struct
import sys
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
    "backend_url": "http://localhost:8000/api/ingest/audio",
    "sensor_id": "mic_simulator",
    "location": "Desktop",
    "api_key": "key123",  # Must match SENSOR_API_KEYS in .env
    "sample_rate": 16000,
    "segment_duration": 1.0,  # seconds
    "channels": 1,
}


class MicrophoneSensor:
    """Simulates an ESP32 sensor using the computer's microphone."""

    def __init__(
        self,
        backend_url: str,
        sensor_id: str,
        location: str,
        api_key: str,
        sample_rate: int = 16000,
        segment_duration: float = 1.0,
        device: int | None = None,
    ):
        self.backend_url = backend_url
        self.sensor_id = sensor_id
        self.location = location
        self.api_key = api_key
        self.sample_rate = sample_rate
        self.segment_duration = segment_duration
        self.device = device
        self.running = False

        # Calculate samples per segment
        self.samples_per_segment = int(sample_rate * segment_duration)

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

    def _send_audio(self, pcm_bytes: bytes) -> dict | None:
        """Send audio segment to backend API."""
        headers = {
            "X-API-Key": f"{self.sensor_id}:{self.api_key}",
            "X-Sensor-ID": self.sensor_id,
            "X-Location": self.location,
            "Content-Type": "application/octet-stream",
        }

        try:
            response = requests.post(
                self.backend_url,
                headers=headers,
                data=pcm_bytes,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            print(f"\n[ERROR] Cannot connect to {self.backend_url}")
            print("        Is the backend running? Try: docker compose up")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"\n[ERROR] HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            print(f"\n[ERROR] {e}")
            return None

    def _format_result(self, result: dict) -> str:
        """Format inference result for display."""
        events = result.get("detected_events", [])
        loudness = result.get("loudness_db", 0)
        proc_time = result.get("processing_time_ms", 0)

        if events:
            event_strs = [f"{e['label']}({e['confidence']:.0%})" for e in events]
            events_display = ", ".join(event_strs)
        else:
            events_display = "(none)"

        return f"Detected: {events_display} | Loudness: {loudness:.1f} dB | Time: {proc_time:.0f}ms"

    def run_continuous(self):
        """Continuously capture and send audio segments."""
        self.running = True
        segment_count = 0

        print(f"\n{'='*60}")
        print("MICROPHONE SENSOR SIMULATOR")
        print(f"{'='*60}")
        print(f"Sensor ID:  {self.sensor_id}")
        print(f"Location:   {self.location}")
        print(f"Backend:    {self.backend_url}")
        print(f"Sample Rate: {self.sample_rate} Hz")
        print(f"Segment:    {self.segment_duration}s ({self.samples_per_segment * 2} bytes)")
        print(f"{'='*60}")
        print("\nPress Ctrl+C to stop\n")

        # Test connection first
        print("Testing connection to backend...")
        health_url = self.backend_url.replace("/audio", "/health")
        try:
            resp = requests.get(health_url, timeout=5)
            health = resp.json()
            if health.get("model_loaded"):
                print(f"[OK] Model loaded: {health.get('classes', [])}")
            else:
                print("[WARNING] Model not loaded - inference will fail")
            if health.get("influxdb_connected"):
                print("[OK] InfluxDB connected")
            else:
                print("[WARNING] InfluxDB not connected - events won't be stored")
        except Exception as e:
            print(f"[WARNING] Could not check health: {e}")

        print(f"\n{'='*60}")
        print("STREAMING AUDIO...")
        print(f"{'='*60}\n")

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

                # Send to backend
                timestamp = datetime.now().strftime("%H:%M:%S")
                segment_count += 1

                result = self._send_audio(pcm_bytes)

                if result:
                    print(f"[{timestamp}] #{segment_count:04d} | {self._format_result(result)}")
                else:
                    print(f"[{timestamp}] #{segment_count:04d} | Failed to send")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[ERROR] Recording failed: {e}")
                time.sleep(1)

        print(f"\n{'='*60}")
        print(f"Stopped. Sent {segment_count} segments.")
        print(f"{'='*60}")

    def stop(self):
        """Stop the continuous capture loop."""
        self.running = False


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
        description="Simulate an ESP32 sensor using your microphone",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use defaults
  %(prog)s --sensor-id test_mic              # Custom sensor ID
  %(prog)s --location "Conference Room"      # Custom location
  %(prog)s --backend http://192.168.1.100:8000/api/ingest/audio
  %(prog)s --list-devices                    # Show audio devices
  %(prog)s --device 2                        # Use specific microphone
        """,
    )

    parser.add_argument(
        "--backend",
        default=DEFAULT_CONFIG["backend_url"],
        help=f"Backend URL (default: {DEFAULT_CONFIG['backend_url']})",
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
        backend_url=args.backend,
        sensor_id=args.sensor_id,
        location=args.location,
        api_key=args.api_key,
        sample_rate=args.sample_rate,
        segment_duration=args.duration,
        device=args.device,
    )

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\nStopping...")
        sensor.stop()

    signal.signal(signal.SIGINT, signal_handler)

    sensor.run_continuous()


if __name__ == "__main__":
    main()
