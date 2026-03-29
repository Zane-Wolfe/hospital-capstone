#!/usr/bin/env python3
"""
TCP Audio Playback Test Server

Listens for the first ESP32 (or simulator) to connect, performs the
authentication handshake, then receives the raw 16-bit PCM stream and
plays it back in real-time through the local speakers.

This is a test-only tool to verify audio is being reconstructed correctly
after being sent in real-time over TCP.

Requirements:
    pip install sounddevice numpy

Usage:
    python tcp_audio_playback_test.py
    python tcp_audio_playback_test.py --port 8001 --sample-rate 16000
    python tcp_audio_playback_test.py --list-devices
    python tcp_audio_playback_test.py --output-device 3
"""

import argparse
import json
import queue
import signal
import socket
import sys
import threading

try:
    import numpy as np
    import sounddevice as sd
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("\nInstall requirements with:")
    print("  pip install sounddevice numpy")
    sys.exit(1)


SAMPLE_RATE = 16000
TCP_PORT = 8001
# How many bytes to recv per network read (must be a multiple of 2 for int16)
RECV_CHUNK_BYTES = 4096
# How many samples to buffer before playback starts (reduces underruns)
PLAYBACK_PREFILL_SAMPLES = SAMPLE_RATE // 4  # 250ms


def list_output_devices():
    print("\nAvailable Audio Output Devices:")
    print("-" * 50)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device["max_output_channels"] > 0:
            default = " (default)" if i == sd.default.device[1] else ""
            print(f"  [{i}] {device['name']}{default}")
            print(f"       Channels: {device['max_output_channels']}, "
                  f"Sample Rate: {device['default_samplerate']:.0f} Hz")
    print()


def run_server(tcp_port: int, sample_rate: int, output_device: int | None):
    # audio_queue holds numpy float32 arrays (mono)
    audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=200)
    stop_event = threading.Event()

    # ------------------------------------------------------------------ #
    # sounddevice output stream callback                                   #
    # ------------------------------------------------------------------ #
    underrun_count = 0

    def audio_callback(outdata: np.ndarray, frames: int,
                       time_info, status):
        nonlocal underrun_count
        if status.output_underflow:
            underrun_count += 1

        remaining = frames
        write_pos = 0

        while remaining > 0:
            try:
                chunk = audio_queue.get_nowait()
            except queue.Empty:
                # No data yet — fill with silence
                outdata[write_pos:] = 0
                break

            take = min(len(chunk), remaining)
            outdata[write_pos:write_pos + take, 0] = chunk[:take]
            write_pos += take
            remaining -= take

            # If the chunk had leftover samples, put them back
            if take < len(chunk):
                audio_queue.put(chunk[take:])

    # ------------------------------------------------------------------ #
    # Network receiver thread                                              #
    # ------------------------------------------------------------------ #
    def receive_audio(conn: socket.socket):
        print("[RX] Receiving audio stream...")
        recv_errors = 0

        while not stop_event.is_set():
            try:
                data = conn.recv(RECV_CHUNK_BYTES)
            except (ConnectionResetError, OSError):
                break

            if not data:
                print("[RX] Connection closed by client.")
                break

            # Ensure we have an even number of bytes for int16 parsing
            if len(data) % 2 != 0:
                data = data[:-1]

            # Convert little-endian int16 PCM → float32 in [-1.0, 1.0]
            samples = np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768.0

            try:
                audio_queue.put(samples, timeout=0.5)
            except queue.Full:
                recv_errors += 1
                if recv_errors % 20 == 1:
                    print(f"[WARN] Audio queue full — dropping chunk "
                          f"({recv_errors} drops so far)")

        stop_event.set()

    # ------------------------------------------------------------------ #
    # TCP server                                                           #
    # ------------------------------------------------------------------ #
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("0.0.0.0", tcp_port))
    server_sock.listen(1)
    server_sock.settimeout(1.0)

    print(f"\n{'='*60}")
    print("TCP AUDIO PLAYBACK TEST SERVER")
    print(f"{'='*60}")
    print(f"Listening on port : {tcp_port}")
    print(f"Sample rate       : {sample_rate} Hz")
    print(f"Output device     : {output_device if output_device is not None else 'default'}")
    print(f"Prefill buffer    : {PLAYBACK_PREFILL_SAMPLES} samples "
          f"({PLAYBACK_PREFILL_SAMPLES / sample_rate * 1000:.0f} ms)")
    print(f"{'='*60}")
    print("\nWaiting for first client to connect... (Ctrl+C to quit)\n")

    conn = None
    try:
        while not stop_event.is_set():
            try:
                conn, addr = server_sock.accept()
                break
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\nAborted.")
        server_sock.close()
        return

    if conn is None:
        server_sock.close()
        return

    print(f"[TCP] Client connected from {addr[0]}:{addr[1]}")

    # ------------------------------------------------------------------ #
    # Handshake                                                            #
    # ------------------------------------------------------------------ #
    conn.settimeout(10.0)
    try:
        raw = b""
        while b"\n" not in raw:
            chunk = conn.recv(1024)
            if not chunk:
                raise ConnectionError("Connection closed before handshake")
            raw += chunk

        handshake = json.loads(raw.strip())
        sensor_id = handshake.get("sensor_id", "unknown")
        location  = handshake.get("location", "unknown")
        print(f"[AUTH] sensor_id={sensor_id!r}  location={location!r}")

        # Accept any credentials — this is a test server
        response = json.dumps({
            "status": "authenticated",
            "buffer_size_bytes": sample_rate * 2,  # 1-second segments
        }) + "\n"
        conn.sendall(response.encode("utf-8"))
        print(f"[AUTH] Handshake accepted\n")

    except Exception as e:
        print(f"[ERROR] Handshake failed: {e}")
        conn.close()
        server_sock.close()
        return

    conn.settimeout(None)

    # ------------------------------------------------------------------ #
    # Start audio output stream                                            #
    # ------------------------------------------------------------------ #
    print(f"[AUDIO] Buffering {PLAYBACK_PREFILL_SAMPLES} samples before playback...")

    stream = sd.OutputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        device=output_device,
        blocksize=1024,
        callback=audio_callback,
    )

    # Start receiving in a background thread
    rx_thread = threading.Thread(target=receive_audio, args=(conn,), daemon=True)
    rx_thread.start()

    # Wait for the prefill buffer before starting playback
    while audio_queue.qsize() * RECV_CHUNK_BYTES // 2 < PLAYBACK_PREFILL_SAMPLES:
        if stop_event.is_set():
            break
        threading.Event().wait(0.01)

    stream.start()
    print(f"[AUDIO] Playback started — you should hear audio now")
    print(f"        Press Ctrl+C to stop\n")

    # ------------------------------------------------------------------ #
    # Stats loop                                                           #
    # ------------------------------------------------------------------ #
    try:
        while not stop_event.is_set():
            threading.Event().wait(5.0)
            q_samples = audio_queue.qsize() * (RECV_CHUNK_BYTES // 2)
            latency_ms = q_samples / sample_rate * 1000
            print(f"[STATS] Queue: {audio_queue.qsize()} chunks "
                  f"(~{latency_ms:.0f} ms)  |  Underruns: {underrun_count}")
    except KeyboardInterrupt:
        print("\nStopping...")

    # ------------------------------------------------------------------ #
    # Cleanup                                                              #
    # ------------------------------------------------------------------ #
    stop_event.set()
    stream.stop()
    stream.close()
    conn.close()
    server_sock.close()
    rx_thread.join(timeout=2.0)
    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Receive ESP32 TCP audio stream and play it on local speakers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Use all defaults
  %(prog)s --port 8001              # Explicit port
  %(prog)s --output-device 2        # Choose output device
  %(prog)s --list-devices           # Show available output devices
        """,
    )
    parser.add_argument("--port", type=int, default=TCP_PORT,
                        help=f"TCP port to listen on (default: {TCP_PORT})")
    parser.add_argument("--sample-rate", type=int, default=SAMPLE_RATE,
                        help=f"Expected audio sample rate in Hz (default: {SAMPLE_RATE})")
    parser.add_argument("--output-device", type=int, default=None,
                        help="sounddevice output device index (default: system default)")
    parser.add_argument("--list-devices", action="store_true",
                        help="List available audio output devices and exit")

    args = parser.parse_args()

    if args.list_devices:
        list_output_devices()
        sys.exit(0)

    def signal_handler(sig, frame):
        print("\nInterrupted.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    run_server(
        tcp_port=args.port,
        sample_rate=args.sample_rate,
        output_device=args.output_device,
    )


if __name__ == "__main__":
    main()
