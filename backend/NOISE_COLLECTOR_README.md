# Ambient Noise Collector

The Ambient Noise Collector captures ambient noise from your system microphone and sends normalized noise levels to the Flow State Tax Monitor backend.

## Features

- Captures audio from system microphone using PyAudio
- Calculates RMS (Root Mean Square) amplitude from audio samples
- Normalizes audio levels to 0-10 scale (0 = silent, 10 = very loud)
- Sends data to backend API at configurable intervals (default: 5 seconds)
- Graceful error handling for microphone access issues
- Configurable microphone device selection
- Lists available audio input devices

## Installation

### Prerequisites

**Windows:**
```bash
pip install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run with default settings (default microphone, 5-second interval):

```bash
python noise_collector.py
```

### List Available Microphones

To see all available audio input devices:

```bash
python noise_collector.py --list-devices
```

This will display something like:
```
Available audio input devices:
------------------------------------------------------------
Device 0: Built-in Microphone
  Channels: 2
  Sample Rate: 44100.0

Device 1: USB Microphone
  Channels: 1
  Sample Rate: 48000.0
```

### Select Specific Microphone

Use a specific microphone device:

```bash
python noise_collector.py --device 1
```

### Configure Backend URL

Connect to a different backend server:

```bash
python noise_collector.py --backend-url http://192.168.1.100:8000
```

### Configure Measurement Interval

Change the interval between measurements (in seconds):

```bash
python noise_collector.py --interval 10
```

### Combined Options

```bash
python noise_collector.py --device 1 --interval 3 --backend-url http://localhost:8000
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--backend-url` | Backend API URL | `http://localhost:8000` |
| `--device` | Microphone device index | System default |
| `--interval` | Seconds between measurements | `5` |
| `--list-devices` | List available devices and exit | - |

## How It Works

### Audio Capture

1. Opens audio stream from selected microphone
2. Captures audio chunks (1024 samples at 44.1kHz)
3. Converts audio bytes to numpy array

### RMS Calculation

The RMS (Root Mean Square) amplitude is calculated as:

```
RMS = sqrt(mean(samples^2))
```

This provides a measure of the audio signal's power/loudness.

### Normalization

The RMS value is normalized to a 0-10 scale:

- **0**: Silent (RMS ≤ 100)
- **5**: Moderate noise (RMS ≈ 2550)
- **10**: Very loud (RMS ≥ 5000)

The normalization uses linear interpolation:
```
noise_level = ((RMS - 100) / (5000 - 100)) * 10
```

### Data Transmission

Every interval (default 5 seconds), the collector sends data to the backend:

```json
{
  "hrv_rmssd": 70.0,
  "notification_count": 0.0,
  "ambient_noise": 4.5
}
```

Note: Since this collector only measures noise, it sends neutral default values for HRV (70.0) and notifications (0.0).

## Troubleshooting

### "Error initializing microphone"

**Possible causes:**
1. Microphone not connected
2. Microphone permissions not granted
3. Another application is using the microphone
4. Wrong device index specified

**Solutions:**
- Check microphone connection
- Grant microphone permissions in system settings
- Close other applications using the microphone
- Use `--list-devices` to find the correct device index
- Try a different device with `--device` flag

### "Cannot connect to backend"

**Possible causes:**
1. Backend server is not running
2. Wrong backend URL
3. Firewall blocking connection

**Solutions:**
- Start the backend server: `uvicorn main:app --reload`
- Verify backend URL with `--backend-url` flag
- Check firewall settings

### "Input overflowed"

This warning can occur when the audio buffer overflows. It's usually harmless and handled gracefully by the collector.

### Calibration

If noise levels seem incorrect (always too high or too low), you may need to adjust the calibration constants in `noise_collector.py`:

```python
MIN_RMS = 100   # Adjust for your environment's noise floor
MAX_RMS = 5000  # Adjust for maximum expected noise
```

## Integration with Full System

For complete focus monitoring, run the noise collector alongside:

1. **Backend server**: `uvicorn main:app --reload`
2. **Frontend dashboard**: `npm start` (in frontend directory)
3. **Noise collector**: `python noise_collector.py`
4. **HRV collector**: (Task 16 - to be implemented)
5. **Notification counter**: (Task 15 - to be implemented)

## Example Output

```
Using default microphone
Microphone initialized successfully

Starting noise collection...
Sending data to: http://localhost:8000/data
Interval: 5 seconds
Press Ctrl+C to stop

Noise level: 2.34/10 ✓ Sent to backend
Noise level: 3.12/10 ✓ Sent to backend
Noise level: 1.89/10 ✓ Sent to backend
^C
Stopping noise collector...
Cleanup complete
```

## Technical Details

- **Audio Format**: 16-bit PCM
- **Sample Rate**: 44.1 kHz
- **Channels**: Mono (1 channel)
- **Chunk Size**: 1024 samples (~23ms at 44.1kHz)
- **Normalization Range**: 0-10 (float)
- **API Endpoint**: POST `/data`

## Requirements Validation

This implementation satisfies:
- **Requirement 1.1**: Accepts and sends focus data to backend API
- **Requirement 3.4**: Measures ambient noise for FQS calculation
