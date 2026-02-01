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
| `/api/ingest/audio` | POST | Submit audio for classification |
| `/api/ingest/health` | GET | Ingest service status |
| `/api/events` | GET | Query historical events |
| `/api/auth/login` | POST | Authenticate user |
| `/ws/events` | WebSocket | Real-time event stream |

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
