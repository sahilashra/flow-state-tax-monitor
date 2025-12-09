# Data Collector Orchestrator

The Data Collector Orchestrator is a unified system that runs all three data collectors (HRV, notifications, and ambient noise) concurrently and aggregates their data before sending it to the backend API.

## Features

- **Concurrent Collection**: Runs all collectors in parallel using threading
- **Data Aggregation**: Combines data from all sources into a single payload
- **Graceful Degradation**: Continues operating even if one collector fails
- **Configurable**: JSON-based configuration for all settings
- **Logging**: Comprehensive logging for debugging and monitoring
- **Auto-start**: Support for Windows Task Scheduler and Linux systemd

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Configuration File

```bash
python data_collector_orchestrator.py --generate-config
```

This creates `collector_config.json` with default settings.

### 3. Edit Configuration

Edit `collector_config.json` to customize:
- Backend URL
- Send interval
- Enable/disable specific collectors
- Collector-specific settings

### 4. Run the Orchestrator

```bash
python data_collector_orchestrator.py
```

## Configuration

### Configuration File Structure

```json
{
  "backend_url": "http://localhost:8000",
  "send_interval": 5,
  "collectors": {
    "hrv": {
      "enabled": true,
      "source": "simulated",
      "sources": ["fitbit", "oura", "simulated"],
      "interval": 60,
      "config_file": "hrv_config.json"
    },
    "notifications": {
      "enabled": true,
      "interval": 5,
      "simulate": false,
      "filter_system": false,
      "filter_app": false
    },
    "noise": {
      "enabled": true,
      "interval": 5,
      "device_index": null
    }
  },
  "graceful_degradation": true,
  "log_level": "INFO"
}
```

### Configuration Options

#### Global Settings

- **backend_url**: URL of the backend API (default: `http://localhost:8000`)
- **send_interval**: Interval in seconds between sending aggregated data (default: 5)
- **graceful_degradation**: Continue if a collector fails (default: true)
- **log_level**: Logging level - DEBUG, INFO, WARNING, ERROR (default: INFO)

#### HRV Collector Settings

- **enabled**: Enable/disable HRV collector (default: true)
- **source**: Primary HRV data source (default: "simulated")
  - Options: "fitbit", "garmin", "oura", "apple_healthkit", "simulated"
- **sources**: List of sources in priority order for fallback (optional)
- **interval**: Interval in seconds between HRV fetches (default: 60)
- **config_file**: Path to HRV API configuration file (default: "hrv_config.json")

#### Notification Counter Settings

- **enabled**: Enable/disable notification counter (default: true)
- **interval**: Interval in seconds between updates (default: 5)
- **simulate**: Use simulated notifications for testing (default: false)
- **filter_system**: Exclude system notifications (default: false)
- **filter_app**: Exclude app notifications (default: false)

#### Noise Collector Settings

- **enabled**: Enable/disable noise collector (default: true)
- **interval**: Interval in seconds between measurements (default: 5)
- **device_index**: Microphone device index (null for default)

## Command-Line Options

```bash
# Run with default configuration
python data_collector_orchestrator.py

# Run with custom configuration file
python data_collector_orchestrator.py --config my_config.json

# Run with custom backend URL (overrides config)
python data_collector_orchestrator.py --backend-url http://192.168.1.100:8000

# Generate default configuration file
python data_collector_orchestrator.py --generate-config

# Print collector status
python data_collector_orchestrator.py --status
```

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Orchestrator Main Thread               │
│  - Manages collector threads                           │
│  - Aggregates data from all sources                    │
│  - Sends combined payload to backend every 5 seconds   │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ HRV Thread   │    │ Notification │    │ Noise Thread │
│              │    │ Thread       │    │              │
│ - Fetches    │    │ - Monitors   │    │ - Captures   │
│   HRV data   │    │   Windows    │    │   microphone │
│ - Updates    │    │   notifs     │    │   input      │
│   aggregator │    │ - Updates    │    │ - Updates    │
│              │    │   aggregator │    │   aggregator │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Data Flow

1. **Collector Threads**: Each collector runs in its own thread, continuously gathering data
2. **Data Aggregator**: Thread-safe shared state that stores the latest value from each collector
3. **Main Loop**: Periodically reads aggregated data and sends it to the backend
4. **Graceful Degradation**: If a collector fails, the orchestrator continues with available data

### Thread Safety

The orchestrator uses thread locks to ensure safe concurrent access to shared data:
- Each data field (HRV, notifications, noise) has its own lock
- Updates are atomic and thread-safe
- No race conditions or data corruption

## Auto-Start Configuration

### Windows (Task Scheduler)

1. Open PowerShell as Administrator
2. Navigate to the backend directory
3. Run the setup script:

```powershell
.\setup_windows_task.ps1
```

This creates a scheduled task that:
- Starts the orchestrator when you log in
- Restarts automatically if it crashes
- Runs in the background

**Manual Task Management:**

```powershell
# Start the task
Start-ScheduledTask -TaskName "FlowStateCollector"

# Stop the task
Stop-ScheduledTask -TaskName "FlowStateCollector"

# View task status
Get-ScheduledTask -TaskName "FlowStateCollector"

# Remove the task
Unregister-ScheduledTask -TaskName "FlowStateCollector" -Confirm:$false
```

### Linux (systemd)

1. Edit `flow-state-collector.service`:
   - Replace `YOUR_USERNAME` with your username
   - Replace `/path/to/backend` with the actual path
   - Replace `/path/to/venv/bin/python` with your Python path

2. Copy the service file:

```bash
sudo cp flow-state-collector.service /etc/systemd/system/
```

3. Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable flow-state-collector

# Start service now
sudo systemctl start flow-state-collector

# Check status
sudo systemctl status flow-state-collector

# View logs
sudo journalctl -u flow-state-collector -f
```

**Service Management:**

```bash
# Stop the service
sudo systemctl stop flow-state-collector

# Restart the service
sudo systemctl restart flow-state-collector

# Disable auto-start
sudo systemctl disable flow-state-collector

# Remove the service
sudo systemctl stop flow-state-collector
sudo systemctl disable flow-state-collector
sudo rm /etc/systemd/system/flow-state-collector.service
sudo systemctl daemon-reload
```

## Logging

Logs are written to:
- **File**: `logs/collector_orchestrator.log`
- **Console**: Standard output

Log format:
```
2025-12-09 10:30:45,123 - Orchestrator - INFO - HRV: 75.0 | Notifications: 2.00 | Noise: 4.50
2025-12-09 10:30:45,456 - Orchestrator - INFO - ✓ Data sent to backend
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about operation
- **WARNING**: Warning messages (non-critical issues)
- **ERROR**: Error messages (critical issues)

Change log level in configuration file:
```json
{
  "log_level": "DEBUG"
}
```

## Troubleshooting

### Orchestrator won't start

1. Check that all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify configuration file is valid JSON:
   ```bash
   python -m json.tool collector_config.json
   ```

3. Check logs for error messages:
   ```bash
   cat logs/collector_orchestrator.log
   ```

### Collector fails to start

1. Check collector-specific configuration
2. Verify required permissions (microphone, Windows API, etc.)
3. Enable graceful degradation to continue with other collectors:
   ```json
   {
     "graceful_degradation": true
   }
   ```

### Backend connection fails

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check backend URL in configuration
3. Verify network connectivity

### HRV collector fails

1. Check HRV configuration file exists: `hrv_config.json`
2. Verify API credentials are valid
3. Try simulated mode:
   ```json
   {
     "collectors": {
       "hrv": {
         "source": "simulated"
       }
     }
   }
   ```

### Notification counter fails

1. On Windows, ensure pywin32 is installed:
   ```bash
   pip install pywin32
   python -m pywin32_postinstall -install
   ```

2. Try simulation mode:
   ```json
   {
     "collectors": {
       "notifications": {
         "simulate": true
       }
     }
   }
   ```

### Noise collector fails

1. Check microphone permissions
2. List available devices:
   ```bash
   python noise_collector.py --list-devices
   ```

3. Try a specific device:
   ```json
   {
     "collectors": {
       "noise": {
         "device_index": 0
       }
     }
   }
   ```

## Advanced Usage

### Disable Specific Collectors

To run only certain collectors, disable others in configuration:

```json
{
  "collectors": {
    "hrv": {
      "enabled": true
    },
    "notifications": {
      "enabled": false
    },
    "noise": {
      "enabled": false
    }
  }
}
```

### Multiple HRV Sources with Fallback

Configure multiple HRV sources in priority order:

```json
{
  "collectors": {
    "hrv": {
      "sources": ["fitbit", "oura", "simulated"],
      "config_file": "hrv_config.json"
    }
  }
}
```

The orchestrator will try each source in order until one succeeds.

### Custom Send Interval

Adjust how often aggregated data is sent to the backend:

```json
{
  "send_interval": 10
}
```

This sends data every 10 seconds instead of the default 5 seconds.

### Strict Mode (No Graceful Degradation)

Require all collectors to work:

```json
{
  "graceful_degradation": false
}
```

The orchestrator will stop if any collector fails.

## Integration with Backend

The orchestrator sends data to the backend `/data` endpoint with this payload:

```json
{
  "hrv_rmssd": 75.5,
  "notification_count": 2.0,
  "ambient_noise": 4.5
}
```

The backend then:
1. Validates the data
2. Calculates the Focus Quality Score (FQS)
3. Broadcasts to all connected WebSocket clients
4. Updates the dashboard in real-time

## Performance Considerations

- **CPU Usage**: Minimal - collectors use blocking I/O and sleep between measurements
- **Memory Usage**: Low - no data buffering, immediate transmission
- **Network Usage**: ~1 KB per transmission (every 5 seconds by default)
- **Thread Count**: 4 threads (main + 3 collectors)

## Security Considerations

- **API Keys**: Store in separate configuration files, not in code
- **File Permissions**: Restrict access to configuration files containing credentials
- **Network**: Use HTTPS for production deployments
- **Logging**: Avoid logging sensitive data (API keys, tokens)

## Examples

### Example 1: Development Setup

```json
{
  "backend_url": "http://localhost:8000",
  "send_interval": 5,
  "collectors": {
    "hrv": {
      "enabled": true,
      "source": "simulated"
    },
    "notifications": {
      "enabled": true,
      "simulate": true
    },
    "noise": {
      "enabled": true
    }
  },
  "graceful_degradation": true,
  "log_level": "DEBUG"
}
```

### Example 2: Production Setup with Real Data

```json
{
  "backend_url": "https://api.example.com",
  "send_interval": 5,
  "collectors": {
    "hrv": {
      "enabled": true,
      "sources": ["fitbit", "oura", "simulated"],
      "interval": 60,
      "config_file": "hrv_config.json"
    },
    "notifications": {
      "enabled": true,
      "interval": 5,
      "simulate": false,
      "filter_system": false
    },
    "noise": {
      "enabled": true,
      "interval": 5,
      "device_index": null
    }
  },
  "graceful_degradation": true,
  "log_level": "INFO"
}
```

### Example 3: HRV Only

```json
{
  "backend_url": "http://localhost:8000",
  "send_interval": 60,
  "collectors": {
    "hrv": {
      "enabled": true,
      "sources": ["fitbit", "simulated"],
      "interval": 60,
      "config_file": "hrv_config.json"
    },
    "notifications": {
      "enabled": false
    },
    "noise": {
      "enabled": false
    }
  },
  "graceful_degradation": true,
  "log_level": "INFO"
}
```

## Support

For issues or questions:
1. Check the logs: `logs/collector_orchestrator.log`
2. Review this README
3. Check individual collector READMEs:
   - `HRV_COLLECTOR_README.md`
   - `NOTIFICATION_COUNTER_README.md`
   - `NOISE_COLLECTOR_README.md`
