# Flow State Tax Monitor - Backend

Python/FastAPI backend for the Flow State Tax Monitor application. This server receives focus data via REST API, calculates Focus Quality Scores (FQS), and streams results to connected clients via WebSocket.

## Features

- **REST API**: Accepts focus data (HRV, notifications, ambient noise)
- **Real-time Streaming**: Broadcasts data to all connected clients via Socket.IO
- **FQS Calculation**: Computes composite focus quality scores with weighted factors
- **Data Validation**: Pydantic models ensure data integrity
- **CORS Support**: Configured for cross-origin requests

## Prerequisites

- Python 3.9 or higher
- pip package manager

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file (optional):
```bash
cp .env.example .env
```

Environment variables:
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `CORS_ORIGINS`: Allowed CORS origins (default: *)

## Running the Server

### Development Mode
```bash
uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn main:socket_app --host 0.0.0.0 --port 8000 --workers 4
```

The server will be available at `http://localhost:8000`

## API Documentation

### REST Endpoints

#### GET /
Root endpoint returning API information.

**Response:**
```json
{
  "message": "Flow State Tax Monitor API"
}
```

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Flow State Tax Monitor",
  "version": "1.0.0"
}
```

#### POST /data
Receive focus data and broadcast to connected clients.

**Request Body:**
```json
{
  "hrv_rmssd": 75.5,
  "notification_count": 2.0,
  "ambient_noise": 4.5
}
```

**Field Descriptions:**
- `hrv_rmssd` (float, required): Heart Rate Variability in milliseconds (expected: 40-100)
- `notification_count` (float, required): Number of notifications (expected: 0-5)
- `ambient_noise` (float, required): Ambient noise level (expected: 0-10)

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Data received and broadcasted"
}
```

**Error Response (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "hrv_rmssd"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### WebSocket Events

Socket.IO server on namespace `/focus_update`

#### Event: `focus_data`
Emitted when new focus data is received.

**Payload:**
```json
{
  "hrv_rmssd": 75.5,
  "notification_count": 2.0,
  "ambient_noise": 4.5,
  "timestamp": "2025-12-08T10:30:45.123Z"
}
```

## FQS Calculation

The Focus Quality Score (FQS) is calculated using weighted factors:

```python
def calculate_fqs(hrv: float, notifications: float, noise_level: float) -> float:
    # HRV Component (50% weight) - higher is better
    hrv_score = ((hrv - 40) / 60) * 50
    
    # Notification Component (30% weight) - lower is better
    notification_score = (1 - notifications / 5) * 30
    
    # Noise Component (20% weight) - lower is better
    noise_score = (1 - noise_level / 10) * 20
    
    # Total FQS (clamped to 0-100)
    fqs = max(0.0, min(100.0, hrv_score + notification_score + noise_score))
    return fqs
```

## Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=main --cov-report=html
```

Run property-based tests only:
```bash
pytest -k "property" -v
```

### Test Structure

- **Unit Tests**: Specific scenarios and edge cases
- **Property-Based Tests**: Universal correctness properties using Hypothesis
  - Input validation (Properties 1-2)
  - WebSocket emission (Properties 3-5)
  - FQS calculation invariants (Properties 6-9)

## Data Collectors

### Demo Data Generator

To test the system with simulated data, run the demo data generator:

```bash
python demo_data_generator.py
```

This will:
- Send focus data every 2 seconds
- Simulate realistic HRV, notification, and noise values
- Trigger "Focus Tax" events every 30 seconds (notification spikes)
- Display calculated FQS scores in the terminal

Press `Ctrl+C` to stop the generator.

See [DEMO_README.md](DEMO_README.md) for more details.

### Ambient Noise Collector

To collect real ambient noise data from your microphone:

```bash
python noise_collector.py
```

This will:
- Capture audio from your system microphone
- Calculate RMS amplitude from audio samples
- Normalize noise levels to 0-10 scale
- Send data to backend every 5 seconds

**Installation:**
```bash
# Windows
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Linux (Ubuntu/Debian)
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**Options:**
```bash
# List available microphones
python noise_collector.py --list-devices

# Use specific microphone
python noise_collector.py --device 1

# Change measurement interval
python noise_collector.py --interval 10

# Connect to different backend
python noise_collector.py --backend-url http://192.168.1.100:8000
```

See [NOISE_COLLECTOR_README.md](NOISE_COLLECTOR_README.md) for detailed documentation.

### Windows Notification Counter

To monitor Windows notifications:

```bash
python notification_counter.py
```

This will:
- Monitor Windows notification center
- Count notifications in a rolling 5-minute window
- Normalize count to 0-5 scale
- Send data to backend every 5 seconds

**Options:**
```bash
# Run in simulation mode (for testing)
python notification_counter.py --simulate

# Filter out system notifications
python notification_counter.py --filter-system

# Change update interval
python notification_counter.py --interval 10
```

See [NOTIFICATION_COUNTER_README.md](NOTIFICATION_COUNTER_README.md) for detailed documentation.

### HRV Data Collector

To collect Heart Rate Variability data from fitness trackers:

```bash
# Run with simulated data (default)
python hrv_collector.py

# Run with Fitbit API
python hrv_collector.py --source fitbit --config fitbit_config.json

# Run with Oura Ring API
python hrv_collector.py --source oura --config oura_config.json
```

This will:
- Fetch HRV (RMSSD) data from fitness tracker APIs
- Cache data locally to minimize API calls (5-minute cache)
- Handle API rate limits and authentication
- Fall back to simulated data if API is unavailable
- Send data to backend every 60 seconds

**Supported APIs:**
- Fitbit (requires OAuth 2.0 access token)
- Oura Ring (requires Personal Access Token)
- Garmin Connect (placeholder - not yet implemented)
- Simulated data (for testing)

**Options:**
```bash
# Change update interval
python hrv_collector.py --interval 120

# Connect to different backend
python hrv_collector.py --backend-url http://192.168.1.100:8000

# Use specific fitness tracker
python hrv_collector.py --source oura --config oura_config.json
```

See [HRV_COLLECTOR_README.md](HRV_COLLECTOR_README.md) for detailed setup instructions and API configuration.

### Unified Data Collector Orchestrator

To run all data collectors together in a unified system:

```bash
# Generate default configuration
python data_collector_orchestrator.py --generate-config

# Run the orchestrator
python data_collector_orchestrator.py
```

This will:
- Run HRV, notification, and noise collectors concurrently
- Aggregate data from all three sources
- Send combined data payload to backend every 5 seconds
- Implement graceful degradation if one collector fails
- Provide comprehensive logging for debugging

**Features:**
- **Concurrent Collection**: All collectors run in parallel using threading
- **Data Aggregation**: Combines data from all sources into a single payload
- **Graceful Degradation**: Continues operating even if one collector fails
- **Configurable**: JSON-based configuration for all settings
- **Auto-start**: Support for Windows Task Scheduler and Linux systemd

**Configuration:**
Edit `collector_config.json` to customize:
- Backend URL
- Send interval
- Enable/disable specific collectors
- Collector-specific settings (intervals, sources, etc.)

**Auto-start on Windows:**
```powershell
# Run as Administrator
.\setup_windows_task.ps1
```

**Auto-start on Linux:**
```bash
# Edit service file with your paths
sudo cp flow-state-collector.service /etc/systemd/system/
sudo systemctl enable flow-state-collector
sudo systemctl start flow-state-collector
```

See [ORCHESTRATOR_README.md](ORCHESTRATOR_README.md) for comprehensive documentation.

## Project Structure

```
backend/
├── main.py                            # FastAPI application and Socket.IO server
├── test_focus_data.py                 # Test suite (unit + property-based)
├── demo_data_generator.py             # Demo data simulator
├── noise_collector.py                 # Ambient noise data collector
├── notification_counter.py            # Windows notification counter
├── hrv_collector.py                   # HRV data collector with fitness API integration
├── hrv_adapters.py                    # Adapter pattern for multiple HRV sources
├── data_collector_orchestrator.py     # Unified orchestrator for all collectors
├── test_orchestrator.py               # Tests for orchestrator
├── test_noise_collector_unit.py       # Unit tests for noise collector
├── verify_noise_collector.py          # Verification script for noise collector
├── test_hrv_collector_quick.py        # Quick tests for HRV collector
├── hrv_config.example.json            # Example API configuration for HRV collector
├── collector_config.example.json      # Example orchestrator configuration
├── flow-state-collector.service       # Linux systemd service file
├── setup_windows_task.ps1             # Windows Task Scheduler setup script
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variable template
├── .gitignore                         # Git ignore patterns
├── README.md                          # This file
├── DEMO_README.md                     # Demo generator documentation
├── NOISE_COLLECTOR_README.md          # Noise collector documentation
├── NOTIFICATION_COUNTER_README.md     # Notification counter documentation
├── HRV_COLLECTOR_README.md            # HRV collector documentation
└── ORCHESTRATOR_README.md             # Orchestrator documentation
```

## Dependencies

- **fastapi**: Modern web framework for building APIs
- **python-socketio**: Socket.IO server implementation
- **uvicorn**: ASGI server for running FastAPI
- **pydantic**: Data validation using Python type annotations
- **pytest**: Testing framework
- **hypothesis**: Property-based testing library
- **httpx**: HTTP client for testing
- **requests**: HTTP library for demo generator and data collectors
- **pyaudio**: Audio I/O library for microphone access (noise collector)
- **numpy**: Numerical computing library for audio processing

## Troubleshooting

**Port already in use:**
```bash
uvicorn main:socket_app --host 0.0.0.0 --port 8001
```

**CORS errors:**
- Update CORS_ORIGINS in .env file
- Ensure frontend URL is included in allowed origins

**Socket.IO connection fails:**
- Verify server is running on expected port
- Check firewall settings
- Ensure WebSocket transport is not blocked

## API Testing with curl

Test the /data endpoint:
```bash
curl -X POST http://localhost:8000/data \
  -H "Content-Type: application/json" \
  -d '{"hrv_rmssd": 75.5, "notification_count": 2.0, "ambient_noise": 4.5}'
```

Test the health endpoint:
```bash
curl http://localhost:8000/health
```

## Switching Between Demo and Real Data

### Quick Switch Guide

**Demo Mode:**
```bash
python demo_data_generator.py
```

**Real Data Mode (Orchestrator):**
```bash
# Generate config if not exists
python data_collector_orchestrator.py --generate-config

# Edit collector_config.json to enable real sources
# Then run:
python data_collector_orchestrator.py
```

**Real Data Mode (Individual Collectors):**
```bash
# Terminal 1: HRV
python hrv_collector.py --source fitbit --config hrv_config.json

# Terminal 2: Notifications
python notification_counter.py

# Terminal 3: Noise
python noise_collector.py
```

See [Real Data Integration Guide](REAL_DATA_INTEGRATION_GUIDE.md) for comprehensive setup instructions.

## Related Documentation

- [Main README](../README.md) - Project overview and full setup guide
- [Real Data Integration Guide](REAL_DATA_INTEGRATION_GUIDE.md) - **Comprehensive guide for real data collection**
- [HRV Setup Guide](HRV_SETUP_GUIDE.md) - Detailed Fitbit/Oura API setup
- [HRV Collector README](HRV_COLLECTOR_README.md) - HRV collector documentation
- [Noise Collector README](NOISE_COLLECTOR_README.md) - Microphone setup and usage
- [Notification Counter README](NOTIFICATION_COUNTER_README.md) - Windows notification tracking
- [Orchestrator README](ORCHESTRATOR_README.md) - Unified orchestrator documentation
- [Demo README](DEMO_README.md) - Demo data generator
- [Requirements](../.kiro/specs/flow-state-tax-monitor/requirements.md) - Feature requirements
- [Design](../.kiro/specs/flow-state-tax-monitor/design.md) - System architecture
