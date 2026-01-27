from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np


# 1. Configuration (Must match your docker-compose.yml)
# Change these to Environment Variables later
url = "http://localhost:8086"
token = "my-super-secret-auth-token"
org = "hospital_monitoring_org"
bucket = "hospital_sounds"

def setup_database_connection():
    print(f"Connecting to InfluxDB at {url}...")
    client = InfluxDBClient(url=url, token=token, org=org)
    
    # Create the Write API
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    # 2. Create a "Test" Data Point
    # This single write action CREATES your schema (measurements, tags, fields)
    p = Point("audio_event") \
        .tag("sensor_id", "TEST_UNIT_00") \
        .tag("location", "Server_Room") \
        .tag("category", "Test_Signal") \
        .field("confidence", 1.0) \
        .field("loudness_db", -60.0) \
        .field("duration_sec", 0.5)

    try:
        write_api.write(bucket=bucket, org=org, record=p)
        print("Success! Test data written.")
        print("   - Bucket 'hospital_sounds' is active.")
        print("   - Measurement 'audio_event' created.")
        print("   - Schema initialized.")
    except Exception as e:
        print(f"Error connecting to InfluxDB: {e}")
        print("   Did you run 'docker-compose up'?")


def calculate_loudness(audio_chunk):
    """
    Calculates the loudness of a 16-bit PCM chunk in dBFS.
    Input: raw bytes or bytearray (from your socket)
    Output: float (e.g., -14.5)
    """
    # 1. Convert raw bytes to integers
    # 'int16' is standard for 16-bit audio
    audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
    
    # Safety check: if chunk is empty
    if len(audio_data) == 0:
        return -96.0

    # 2. Calculate RMS (Root Mean Square)
    # We cast to float64 to prevent overflow when squaring big numbers
    rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
    
    # 3. Handle absolute silence (prevent log(0) error)
    # If the mic is unplugged or dead silent, RMS might be 0.
    if rms < 0.0001:
        return -96.0 # The theoretical floor of 16-bit audio

    # 4. Convert to dBFS
    # 32768 is the maximum value for a 16-bit signed integer
    db_fs = 20 * np.log10(rms / 32768.0)
    
    return float(db_fs)


if __name__ == "__main__":
    setup_database_connection() 