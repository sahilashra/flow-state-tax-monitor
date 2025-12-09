# Data Collector Orchestrator - Quick Start Guide

## What is it?

The Data Collector Orchestrator is a unified system that runs all three data collectors (HRV, notifications, and ambient noise) concurrently and sends aggregated data to the backend.

## Quick Start (3 steps)

### 1. Generate Configuration

```bash
cd backend
python data_collector_orchestrator.py --generate-config
```

This creates `collector_config.json` with default settings.

### 2. Edit Configuration (Optional)

Open `collector_config.json` and customize:
- Backend URL (if not localhost:8000)
- Enable/disable specific collectors
- Adjust intervals and settings

### 3. Run the Orchestrator

```bash
python data_collector_orchestrator.py
```

That's it! The orchestrator will:
- ✓ Start all enabled collectors in parallel
- ✓ Aggregate data from all sources
- ✓ Send combined data to backend every 5 seconds
- ✓ Continue running even if one collector fails
- ✓ Log everything to `logs/collector_orchestrator.log`

## What You'll See

```
2025-12-09 10:30:45 - Orchestrator - INFO - Data Collector Orchestrator Starting
2025-12-09 10:30:45 - Orchestrator - INFO - Backend URL: http://localhost:8000
2025-12-09 10:30:45 - Orchestrator - INFO - Started 3 collector threads
2025-12-09 10:30:47 - Orchestrator - INFO - HRV: 75.0 | Notifications: 2.00 | Noise: 4.50
2025-12-09 10:30:47 - Orchestrator - INFO - ✓ Data sent to backend
```

## Configuration Examples

### Development (Simulated Data)

```json
{
  "backend_url": "http://localhost:8000",
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
  }
}
```

### Production (Real Data)

```json
{
  "backend_url": "http://localhost:8000",
  "collectors": {
    "hrv": {
      "enabled": true,
      "sources": ["fitbit", "oura", "simulated"],
      "config_file": "hrv_config.json"
    },
    "notifications": {
      "enabled": true,
      "simulate": false
    },
    "noise": {
      "enabled": true
    }
  }
}
```

### HRV Only

```json
{
  "backend_url": "http://localhost:8000",
  "collectors": {
    "hrv": {
      "enabled": true,
      "sources": ["fitbit", "simulated"]
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

## Auto-Start

### Windows

```powershell
# Run as Administrator
.\setup_windows_task.ps1
```

The orchestrator will now start automatically when you log in.

### Linux

```bash
# Edit service file with your paths
sudo cp flow-state-collector.service /etc/systemd/system/
sudo systemctl enable flow-state-collector
sudo systemctl start flow-state-collector
```

## Troubleshooting

### Backend connection fails

Make sure the backend is running:
```bash
cd backend
uvicorn main:socket_app --reload
```

### Collector fails to start

Check the logs:
```bash
cat logs/collector_orchestrator.log
```

Enable graceful degradation (default):
```json
{
  "graceful_degradation": true
}
```

### Need more details?

See [ORCHESTRATOR_README.md](ORCHESTRATOR_README.md) for comprehensive documentation.

## Command Reference

```bash
# Generate config
python data_collector_orchestrator.py --generate-config

# Run with default config
python data_collector_orchestrator.py

# Run with custom config
python data_collector_orchestrator.py --config my_config.json

# Run with custom backend URL
python data_collector_orchestrator.py --backend-url http://192.168.1.100:8000

# Check status
python data_collector_orchestrator.py --status
```

## What's Next?

1. **Configure HRV sources**: See [HRV_COLLECTOR_README.md](HRV_COLLECTOR_README.md)
2. **Set up auto-start**: Use the scripts provided
3. **Monitor logs**: Check `logs/collector_orchestrator.log`
4. **Customize settings**: Edit `collector_config.json`

For complete documentation, see [ORCHESTRATOR_README.md](ORCHESTRATOR_README.md).
