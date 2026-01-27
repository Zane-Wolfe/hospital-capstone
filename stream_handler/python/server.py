# Create a server to handle many incoming audio streams with TCP sockets
# Prepare each audio stream to be analysed by pytorch model and output results to InfluxDB
import socket
import threading
from database_handler import setup_database_connection, calculate_loudness
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np

# 1. Configuration (Must match your docker-compose.yml)
# Change these to Environment Variables later
url = "http://localhost:8086"
token = "my-super-secret-auth-token"
org = "hospital_monitoring_org"
bucket = "hospital_sounds"

# 2. PyTorch Model (Placeholder for actual model loading)
def load_model():
    # Replace with actual model loading logic
    print("Loading PyTorch model...")
    return None

# 3. Audio Processing
def process_audio(audio_data):
    # Replace with actual audio processing logic
    print("Processing audio data...")
    return np.random.rand(1, 10)  # Example processed data

# 4. InfluxDB Write Function
def write_to_influxdb(client, measurement, fields):
    point = Point(measurement).field("value", fields)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=bucket, org=org, record=point)

# 5. Client Handler
def handle_client(client_socket, model, influx_client):
    try:
        while True:
            # Receive audio data from the client
            audio_data = client_socket.recv(4096)
            if not audio_data:
                break

            # # Process the audio data
            # processed_data = process_audio(audio_data)

            # # Analyze with the model (Placeholder for actual inference)
            # print("Analyzing audio data...")
            # result = np.argmax(processed_data)  # Example result

            # # Write the result to InfluxDB
            # write_to_influxdb(influx_client, "audio_analysis", result)
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

# 6. Main Server Logic
def start_server(host="0.0.0.0", port=5000):
    model = load_model()
    influx_client = InfluxDBClient(url=url, token=token, org=org)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket, model, influx_client))
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()