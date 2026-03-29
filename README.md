# Hospital Sound Classifier

Real-time audio event monitoring system for hospital environments. Uses a CNN-based sound classifier to detect events like alarms, speech, footsteps, and more from ESP32 sensors.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   ESP32     │────▶│   Backend   │────▶│  InfluxDB   │
│   Sensors   │     │   (FastAPI) │     │  (Events)   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                          │ WebSocket
                          ▼
                   ┌─────────────┐
                   │  Frontend   │
                   │   (React)   │
                   └─────────────┘
```

**Components:**
- **Backend** - FastAPI server with PyTorch inference engine
- **Frontend** - React dashboard for viewing events
- **InfluxDB** - Time-series database for event storage
- **Model** - Conv2D CNN using MelSpectrogram features (7 classes)

**Sound Classes:**
- alarms, carts_rolling, coughing, door_knock, door_open_close, footsteps, speech

## Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for running the simulator)
- A trained model checkpoint at `model_training/hospital_sound_classifier.pth`

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd hospital-capstone
```

### 2. Create environment file

```bash
cp .env.example .env
```

Edit `.env` and set your passwords:
```bash
AUTH_PASSWORD=your_secure_password
JWT_SECRET_KEY=generate_a_random_256_bit_key
```

### 3. Ensure model is in place

The trained model checkpoint must exist at:
```
model_training/hospital_sound_classifier.pth
```

The checkpoint should contain embedded config (class_names, n_mels, n_fft, hop_length, threshold).

### 4. Start services

```bash
docker compose up -d --build
```

### 5. Verify services are running

```bash
# Check backend health
curl http://localhost:8000/api/health | jq

# Expected output:
# {
#   "status": "healthy",
#   "model": {
#     "loaded": true,
#     "classes": ["alarms", "carts_rolling", ...],
#     "n_mels": 128,
#     "threshold": 0.5
#   }
# }
```

### 6. Access the frontend

Open http://localhost:3000 in your browser.

Login with credentials from your `.env` file (default username: `admin`).

## Testing with Microphone Simulator

The simulator captures audio from your microphone and sends it to the backend for classification.

### Install dependencies

```bash
pip install sounddevice numpy requests
```

### Add simulator to allowed sensors

Edit `.env` and add `mic_simulator:key123` to `SENSOR_API_KEYS`:
```bash
SENSOR_API_KEYS=sensor_001:key123,mic_simulator:key123
```

Restart backend:
```bash
docker compose restart backend
```

### Run simulator

```bash
cd backend
python scripts/mic_sensor_simulator.py
```

Options:
```bash
# List audio devices
python scripts/mic_sensor_simulator.py --list-devices

# Use specific device
python scripts/mic_sensor_simulator.py --device 2

# Custom location
python scripts/mic_sensor_simulator.py --location "Room 101"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_PATH` | Path to model checkpoint | `/app/models/hospital_sound_classifier.pth` |
| `INFERENCE_CONFIDENCE_THRESHOLD` | Override detection threshold (blank = use checkpoint default) | `` |
| `AUDIO_SAMPLE_RATE` | Audio sample rate in Hz | `16000` |
| `SENSOR_API_KEYS` | Comma-separated sensor credentials | `sensor_001:key123` |
| `AUTH_USERNAME` | Dashboard login username | `admin` |
| `AUTH_PASSWORD` | Dashboard login password | (required) |
| `JWT_SECRET_KEY` | Secret for JWT tokens | (required) |

### Model Checkpoint Format

The `.pth` checkpoint must contain:
```python
{
    "model_state_dict": ...,
    "class_names": ["alarms", "carts_rolling", ...],
    "n_mels": 128,
    "n_fft": 1024,
    "hop_length": 512,
    "sample_rate": 16000,
    "threshold": 0.5,
}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Service health and model info |
| `/api/ingest/health` | GET | Ingest service status |
| `/api/events` | GET | Query historical events |
| `/api/auth/login` | POST | Authenticate user |
| `/api/device-metrics/heartbeat` | POST | Device heartbeat (see below) |
| `/ws/events` | WebSocket | Real-time event stream |

## ESP32 Device API

ESP32 sensors connect to the backend via **TCP streaming** for real-time audio classification.

### Connection Overview

```
ESP32 Sensor                          Backend Server
     │                                      │
     │──── TCP Connect (port 8001) ────────▶│
     │                                      │
     │──── JSON Handshake + \n ────────────▶│
     │                                      │
     │◀─── Auth Response + \n ──────────────│
     │                                      │
     │──── Raw PCM Audio Stream ───────────▶│
     │          (continuous)                │
     │                                      │
     │──── HTTP Heartbeat (periodic) ──────▶│ (port 8000)
     │                                      │
```

### Step 1: TCP Connection

Connect to the backend TCP server:

| Setting | Value |
|---------|-------|
| Host | Backend server IP/hostname |
| Port | `8001` (default, configurable via `TCP_INGEST_PORT`) |
| Protocol | TCP |

### Step 2: Authentication Handshake

Immediately after connecting, send a JSON handshake followed by a newline (`\n`):

```json
{"sensor_id": "sensor_001", "api_key": "key123", "location": "Room 101"}\n
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sensor_id` | string | Yes | Unique identifier for this sensor |
| `api_key` | string | Yes | API key matching `SENSOR_API_KEYS` in backend `.env` |
| `location` | string | Yes | Human-readable location (e.g., "ICU Room 5") |

**Server Response (success):**
```json
{"status": "authenticated", "buffer_size_bytes": 32000}\n
```

**Server Response (failure):**
```json
{"status": "error", "message": "Authentication failed"}\n
```

The `buffer_size_bytes` tells you how many bytes make up one audio segment for inference.

### Step 3: Stream Audio Data

After successful authentication, continuously stream raw PCM audio data:

| Setting | Value |
|---------|-------|
| Format | Raw PCM (no headers) |
| Bit Depth | 16-bit signed integers |
| Byte Order | Little-endian |
| Sample Rate | 16,000 Hz |
| Channels | 1 (mono) |
| Bytes per Sample | 2 |

**Segment Size Calculation:**
```
segment_bytes = sample_rate × segment_duration × 2
              = 16000 × 1.0 × 2
              = 32,000 bytes (with default 1-second segments)
```

The backend buffers incoming audio and triggers ML inference when a complete segment is received.

### Step 4: Heartbeat (Optional but Recommended)

Send periodic HTTP heartbeats to report device status and appear as "online" in the dashboard:

**Endpoint:** `POST /api/device-metrics/heartbeat`

**Headers:**
```
X-API-Key: key123
X-Sensor-ID: sensor_001
X-Location: Room 101
Content-Type: application/json
```

**Body:**
```json
{
  "battery_percent": 85.5,
  "bandwidth_kbps": 128.0,
  "signal_strength_dbm": -65.0,
  "firmware_version": "1.2.3"
}
```

All body fields are optional. Send heartbeats every 30 seconds (recommended).

### ESP32 Arduino Example

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

// Configuration
const char* WIFI_SSID = "your_wifi";
const char* WIFI_PASS = "your_password";
const char* SERVER_HOST = "192.168.1.100";
const int TCP_PORT = 8001;
const int HTTP_PORT = 8000;
const char* SENSOR_ID = "sensor_001";
const char* API_KEY = "key123";
const char* LOCATION = "Room 101";

// Audio settings
const int SAMPLE_RATE = 16000;
const int BUFFER_SIZE = 1024;  // Send in chunks
int16_t audioBuffer[BUFFER_SIZE];

// Heartbeat settings
const unsigned long HEARTBEAT_INTERVAL = 30000;  // 30 seconds
unsigned long lastHeartbeat = 0;

WiFiClient tcpClient;

void setup() {
  Serial.begin(115200);
  connectWiFi();
  connectTCP();
}

void connectWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.println("IP: " + WiFi.localIP().toString());
}

void connectTCP() {
  Serial.println("Connecting to TCP server...");
  if (tcpClient.connect(SERVER_HOST, TCP_PORT)) {
    // Send authentication handshake
    String handshake = "{\"sensor_id\":\"" + String(SENSOR_ID) +
                       "\",\"api_key\":\"" + String(API_KEY) +
                       "\",\"location\":\"" + String(LOCATION) + "\"}\n";
    tcpClient.print(handshake);

    // Wait for response
    unsigned long start = millis();
    while (!tcpClient.available() && millis() - start < 5000) {
      delay(10);
    }

    if (tcpClient.available()) {
      String response = tcpClient.readStringUntil('\n');
      if (response.indexOf("authenticated") > 0) {
        Serial.println("Authenticated successfully!");
      } else {
        Serial.println("Authentication failed!");
        tcpClient.stop();
      }
    } else {
      Serial.println("No response from server");
      tcpClient.stop();
    }
  } else {
    Serial.println("TCP connection failed");
  }
}

void sendHeartbeat() {
  HTTPClient http;
  String url = "http://" + String(SERVER_HOST) + ":" + String(HTTP_PORT) +
               "/api/device-metrics/heartbeat";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  http.addHeader("X-Sensor-ID", SENSOR_ID);
  http.addHeader("X-Location", LOCATION);

  // Build payload with device metrics
  // Customize these values based on your hardware
  float battery = getBatteryPercent();  // Implement based on your hardware
  int rssi = WiFi.RSSI();

  String payload = "{\"battery_percent\":" + String(battery, 1) +
                   ",\"signal_strength_dbm\":" + String(rssi) +
                   ",\"firmware_version\":\"1.0.0\"}";

  int httpCode = http.POST(payload);
  if (httpCode == 200) {
    Serial.println("Heartbeat sent successfully");
  } else {
    Serial.println("Heartbeat failed: " + String(httpCode));
  }
  http.end();
}

float getBatteryPercent() {
  // Implement battery reading based on your hardware
  // Example for ESP32 with voltage divider on GPIO 35:
  // int raw = analogRead(35);
  // float voltage = (raw / 4095.0) * 3.3 * 2;  // Adjust multiplier for your divider
  // return map(voltage, 3.0, 4.2, 0, 100);
  return 100.0;  // Default: return 100% if no battery monitoring
}

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    connectWiFi();
  }

  // Handle TCP audio streaming
  if (tcpClient.connected()) {
    // Read audio from I2S microphone (e.g., INMP441)
    // Fill audioBuffer with 16-bit PCM samples
    readMicrophoneData(audioBuffer, BUFFER_SIZE);

    // Send raw PCM bytes (little-endian)
    tcpClient.write((uint8_t*)audioBuffer, BUFFER_SIZE * 2);
  } else {
    // Reconnect if disconnected
    Serial.println("TCP disconnected, reconnecting...");
    delay(5000);
    connectTCP();
  }

  // Send periodic heartbeat
  if (millis() - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
}

void readMicrophoneData(int16_t* buffer, int samples) {
  // Implement I2S microphone reading here
  // Example for INMP441:
  // i2s_read(I2S_NUM_0, buffer, samples * 2, &bytesRead, portMAX_DELAY);
}
```

### Sensor Registration

Before a sensor can connect, its credentials must be added to the backend:

1. Edit `.env` file:
   ```bash
   SENSOR_API_KEYS=sensor_001:key123,sensor_002:key456,my_new_sensor:secretkey
   ```

2. Restart the backend:
   ```bash
   docker compose restart backend
   ```

### Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Backend not running or wrong port | Check `docker compose ps`, verify port 8001 is exposed |
| Authentication failed | Invalid credentials | Ensure `sensor_id:api_key` is in `SENSOR_API_KEYS` |
| Connection reset | Network issue or server restart | Implement auto-reconnect with backoff |
| No inference results | Model not loaded | Check `/api/ingest/health` endpoint |

### Testing Your Device

Use the microphone simulator to test the protocol before deploying hardware:

```bash
cd backend/scripts
python mic_sensor_simulator.py --sensor-id test_device --location "Test Room"
```

This mimics exactly what an ESP32 should do, including TCP streaming and heartbeats.

## Development

### Run backend tests

```bash
docker compose exec backend pytest tests/ -v
```

### View logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend
```

### Rebuild after changes

```bash
docker compose up -d --build
```

### Reset everything

```bash
docker compose down -v
docker compose up -d --build
```

## Project Structure

```
hospital-capstone/
├── backend/
│   ├── app/
│   │   ├── auth/          # Authentication
│   │   ├── db/            # InfluxDB client
│   │   ├── events/        # Event queries & WebSocket
│   │   ├── inference/     # ML model & audio processing
│   │   ├── ingest/        # Sensor data ingestion
│   │   ├── sensors/       # Sensor management
│   │   ├── config.py      # Settings
│   │   └── main.py        # FastAPI app
│   ├── scripts/
│   │   └── mic_sensor_simulator.py
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/    # React components
│       ├── pages/         # Page views
│       └── types/         # TypeScript types
├── model_training/        # Model checkpoint (mounted read-only)
├── docker-compose.yml
├── .env.example
└── README.md
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Model not loaded" | Ensure `model_training/hospital_sound_classifier.pth` exists |
| "403 Forbidden" on simulator | Add sensor credentials to `SENSOR_API_KEYS` in `.env` |
| Events not appearing in frontend | Check WebSocket connection in browser dev tools |
| Backend startup fails | Check `docker compose logs backend` for errors |
