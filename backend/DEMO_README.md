# Demo Data Generator

This script simulates realistic focus data for the Flow State Tax Monitor application.

## Features

- **Realistic Data Generation**: Generates HRV (40-100), notifications (0-5), and ambient noise (0-10) values
- **Focus Tax Events**: Periodically simulates notification spikes that cause FQS drops
- **Real-time Monitoring**: Displays calculated FQS scores as data is sent
- **Continuous Operation**: Runs indefinitely until stopped

## Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure the backend server is running:
   ```bash
   uvicorn main:app --reload
   ```

## Usage

Run the demo data generator:

```bash
python demo_data_generator.py
```

The script will:
- Send focus data to `http://localhost:8000/data` every 2 seconds
- Trigger a "Focus Tax" event (notification spike) every 30 seconds
- Display real-time FQS calculations in the console

## Output Example

```
======================================================================
Flow State Tax Monitor - Demo Data Generator
======================================================================
Backend URL: http://localhost:8000/data
Update interval: 2 seconds
Focus Tax events every ~30 seconds
======================================================================

Starting data generation... (Press Ctrl+C to stop)

[10:30:45] Sent data - HRV: 72.3, Notifications: 1.2, Noise: 3.5 → FQS: 78.4
[10:30:47] Sent data - HRV: 68.9, Notifications: 0.8, Noise: 2.9 → FQS: 81.2
...
======================================================================
🚨 FOCUS TAX EVENT - Notification spike detected!
======================================================================
[10:31:15] Sent data - HRV: 56.2, Notifications: 4.7, Noise: 6.8 → FQS: 42.1
```

## Configuration

You can modify these constants in `demo_data_generator.py`:

- `BACKEND_URL`: Backend API endpoint (default: `http://localhost:8000/data`)
- `UPDATE_INTERVAL`: Seconds between updates (default: 2)
- `FOCUS_TAX_INTERVAL`: Seconds between Focus Tax events (default: 30)

## Stopping the Demo

Press `Ctrl+C` to stop the data generator gracefully.
