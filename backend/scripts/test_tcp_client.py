#!/usr/bin/env python3
"""
TCP client for streaming live microphone audio to the backend.

Usage:
    python test_tcp_client.py [--host HOST] [--port PORT] [--sensor SENSOR_ID] [--key API_KEY] [--location LOCATION]

Examples:
    # Connect with default settings
    python test_tcp_client.py

    # Connect to remote host
    python test_tcp_client.py --host 192.168.1.100 --port 8001

    # Use a specific microphone device
    python test_tcp_client.py --device 2

Requirements:
    pip install sounddevice
    System: portaudio (apt install portaudio19-dev / brew install portaudio)
"""
import argparse
import asyncio
import json
import queue
import signal
import sys
import threading
import time

import requests
import sounddevice as sd

# Audio configuration (matches backend expectations)
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"  # 16-bit signed PCM

# Global shutdown flag
shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\nShutdown requested...")
    shutdown_event.set()


def _heartbeat_loop(
    host: str,
    http_port: int,
    sensor_id: str,
    api_key: str,
    location: str,
    stop_event: threading.Event,
    interval: int = 30,
) -> None:
    """Background thread: POST heartbeat to the device-metrics endpoint."""
    url = f"http://{host}:{http_port}/api/device-metrics/heartbeat"
    headers = {
        "X-API-Key": api_key,
        "X-Sensor-ID": sensor_id,
        "X-Location": location,
        "Content-Type": "application/json",
    }
    payload = {
        "battery_percent": 100.0,
        "bandwidth_kbps": 128.0,
        "signal_strength_dbm": -50.0,
        "firmware_version": "test-client-1.0",
    }
    while not stop_event.wait(interval):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=5)
            print(f"[Heartbeat] {resp.status_code}")
        except Exception as e:
            print(f"[Heartbeat] failed: {e}")


async def stream_from_microphone(
    host: str,
    port: int,
    http_port: int,
    sensor_id: str,
    api_key: str,
    location: str,
    device: int | None = None,
) -> None:
    """
    Connect to TCP server and stream live microphone audio.

    Args:
        host: Server hostname
        port: Server port
        sensor_id: Sensor identifier
        api_key: API key for authentication
        location: Sensor location
        device: Optional audio device index
    """
    print(f"Connecting to {host}:{port}...")

    try:
        reader, writer = await asyncio.open_connection(host, port)
    except ConnectionRefusedError:
        print(f"Error: Could not connect to {host}:{port}")
        print("Make sure the backend is running and the TCP server is started.")
        sys.exit(1)

    print("Connected!")

    # Audio buffer queue
    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time_info, status):
        """Callback for sounddevice InputStream."""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        audio_queue.put(indata.copy().tobytes())

    try:
        # Send handshake
        handshake = {
            "sensor_id": sensor_id,
            "api_key": api_key,
            "location": location,
        }
        print(f"Sending handshake: {handshake}")
        writer.write(json.dumps(handshake).encode() + b"\n")
        await writer.drain()

        # Read response
        response_line = await asyncio.wait_for(reader.readline(), timeout=10.0)
        response = json.loads(response_line.decode())
        print(f"Server response: {response}")

        if response.get("status") != "authenticated":
            print(f"Authentication failed: {response.get('message', 'Unknown error')}")
            return

        buffer_size = response.get("buffer_size_bytes", 96000)
        print(f"Authenticated! Server expects {buffer_size} bytes per segment")

        # Start heartbeat background thread
        hb_stop = threading.Event()
        hb_thread = threading.Thread(
            target=_heartbeat_loop,
            args=(host, http_port, sensor_id, api_key, location, hb_stop),
            daemon=True,
        )
        hb_thread.start()
        print("Heartbeat thread started (every 30s)")

        # Start microphone stream
        print(f"\nStarting microphone capture...")
        print(f"  Sample rate: {SAMPLE_RATE} Hz")
        print(f"  Channels: {CHANNELS}")
        print(f"  Format: 16-bit signed PCM")
        if device is not None:
            print(f"  Device: {device}")
        print("\nPress Ctrl+C to stop streaming.")
        print("-" * 40)

        total_sent = 0
        segments_sent = 0

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            device=device,
            callback=audio_callback,
            blocksize=1024,
        ):
            while not shutdown_event.is_set():
                try:
                    # Get audio data from queue with timeout
                    try:
                        chunk = audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        await asyncio.sleep(0.01)
                        continue

                    # Send audio data
                    writer.write(chunk)
                    await writer.drain()
                    total_sent += len(chunk)

                    # Track segments
                    new_segments = total_sent // buffer_size
                    if new_segments > segments_sent:
                        print(f"Segment {new_segments} sent ({total_sent:,} bytes total)")
                        segments_sent = new_segments

                except Exception as e:
                    print(f"Error sending audio: {e}")
                    break

        print("-" * 40)
        print(f"Streaming stopped.")
        print(f"Total sent: {total_sent:,} bytes ({segments_sent} complete segments)")
        hb_stop.set()

    except asyncio.TimeoutError:
        print("Error: Timeout waiting for server response")
    except sd.PortAudioError as e:
        print(f"Audio device error: {e}")
        print("\nAvailable devices:")
        print(sd.query_devices())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing connection...")
        writer.close()
        await writer.wait_closed()


def list_devices():
    """List available audio input devices."""
    print("Available audio devices:")
    print("-" * 60)
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            default = " (default)" if i == sd.default.device[0] else ""
            print(f"  [{i}] {dev['name']}{default}")
            print(f"      Inputs: {dev['max_input_channels']}, Sample rate: {dev['default_samplerate']}")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="TCP client for live microphone audio streaming",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="Server hostname (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="TCP server port (default: 8001)",
    )
    parser.add_argument(
        "--http-port",
        type=int,
        default=8000,
        help="HTTP server port for heartbeat (default: 8000)",
    )
    parser.add_argument(
        "--sensor",
        default="sensor_001",
        help="Sensor ID (default: sensor_001)",
    )
    parser.add_argument(
        "--key",
        default="key123",
        help="API key (default: key123)",
    )
    parser.add_argument(
        "--location",
        default="TestRoom",
        help="Sensor location (default: TestRoom)",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Audio input device index (use --list-devices to see available)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit",
    )

    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 50)
    print("TCP Microphone Audio Streaming Client")
    print("=" * 50)
    print(f"Target: {args.host}:{args.port}")
    print(f"Sensor: {args.sensor} @ {args.location}")
    print()

    asyncio.run(
        stream_from_microphone(
            host=args.host,
            port=args.port,
            http_port=args.http_port,
            sensor_id=args.sensor,
            api_key=args.key,
            location=args.location,
            device=args.device,
        )
    )


if __name__ == "__main__":
    main()
