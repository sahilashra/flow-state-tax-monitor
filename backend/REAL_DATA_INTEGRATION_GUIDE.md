# Real Data Integration Guide

This comprehensive guide covers everything you need to know about collecting real data for the Flow State Tax Monitor.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Data Source Setup](#data-source-setup)
4. [Switching Between Modes](#switching-between-modes)
5. [Troubleshooting](#troubleshooting)
6. [Security Best Practices](#security-best-practices)
7. [Advanced Configuration](#advanced-configuration)

## Overview

The Flow State Tax Monitor can operate in three modes:

| Mode | Description | Best For |
|------|-------------|----------|
| **Demo Mode** | Single script generates all data | Quick demos, testing |
| **Simulated Mode** | Orchestrator with simulated data | Development without hardware |
| **Real Data Mode** | Actual data from devices/APIs | Production monitoring |

### Data Sources

The system collects three types of data:

1. **HRV (Heart Rate Variability)** - 50% weight in FQS
   - Sources: Fitbit, Oura Ring, Garmin (planned)
   - Measures: Physiological stress and recovery
   - Update frequency: Every 60 seconds (cached for 5 minutes)

2. **Notification Count** - 30% weight in FQS
   - Sources: Windows notification center (macOS/Linux planned)
   - Measures: Digital interruptions
   - Update frequency: Every 5 seconds (rolling 5-minute window)

3. **Ambient Noise** - 20% weight in FQS
   - Sources: System microphone
   - Measures: Environmental distractions
   - Update frequency: Every 5 seconds

## Quick Start

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Generate Configuration

```bash
python data_collector_orchestrator.py --generate-config
```

This creates `collector_config.json` with default settings.

### Step 3: Test with Simulated Data

```bash
# Start backend
uvicorn main:socket_app --reload

# In another terminal, start orchestrator
python data_collector_orchestrator.py
```

### Step 4: Set Up Real Data Sources

Follow the detailed setup instructions below for each data source you want to use.

### Step 5: Update Configuration

Edit `collector_config.json` to enable real data sources:

```json
{
  "backend_url": "http://localhost:8000",
  "send_interval": 5,
  "collectors": {
    "hrv": {
      "enabled": true,
      "source": "fitbit",
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

### Step 6: Run with Real Data

```bash
python data_collector_orchestrator.py
```

## Data Source Setup

### HRV Data Collection

#### Option 1: Fitbit

**Prerequisites:**
- Fitbit account
- Compatible device (Charge 5, Sense, Versa 3, Inspire 3, or newer)
- Device must support HRV tracking

**Setup Steps:**

1. **Register Fitbit Developer App**
   - Go to https://dev.fitbit.com/apps
   - Click "Register a New App"
   - Fill in details:
     - Application Name: Flow State Monitor
     - Application Website: http://localhost
     - OAuth 2.0 Application Type: **Personal**
     - Callback URL: http://localhost:8080/callback
     - Default Access Type: Read-Only
   - Note your Client ID and Client Secret

2. **Get Access Token**
   - Go to your app's page on https://dev.fitbit.com/apps
   - Find the "OAuth 2.0 tutorial page" link
   - Follow the authorization flow
   - Copy the access token (starts with "eyJ...")

3. **Create Configuration File**
   ```bash
   cat > hrv_config.json << EOF
   {
     "fitbit": {
       "access_token": "YOUR_ACCESS_TOKEN_HERE"
     }
   }
   EOF
   ```

4. **Test the Collector**
   ```bash
   python hrv_collector.py --source fitbit --config hrv_config.json
   ```

**Important Notes:**
- Fitbit access tokens expire after 8 hours
- For production, implement token refresh (see HRV_SETUP_GUIDE.md)
- HRV data is typically collected during sleep
- Sync your device regularly for latest data

#### Option 2: Oura Ring

**Prerequisites:**
- Oura Ring (Gen 2 or Gen 3)
- Oura account

**Setup Steps:**

1. **Get Personal Access Token**
   - Log in to https://cloud.ouraring.com
   - Go to https://cloud.ouraring.com/personal-access-tokens
   - Click "Create A New Personal Access Token"
   - Give it a name (e.g., "Flow State Monitor")
   - Copy the token (you won't see it again!)

2. **Create Configuration File**
   ```bash
   cat > oura_config.json << EOF
   {
     "oura": {
       "access_token": "YOUR_OURA_TOKEN_HERE"
     }
   }
   EOF
   ```

3. **Test the Collector**
   ```bash
   python hrv_collector.py --source oura --config oura_config.json
   ```

**Important Notes:**
- Personal Access Tokens don't expire automatically
- HRV data is collected during sleep
- Data may take a few hours to sync after waking

#### Option 3: Simulated Data

For testing without a fitness tracker:

```bash
python hrv_collector.py
# or
python hrv_collector.py --source simulated
```

### Notification Counter

#### Windows Setup

**Prerequisites:**
- Windows 10 or Windows 11
- Python 3.9+

**Setup Steps:**

1. **Install Windows API Library**
   ```bash
   pip install pywin32
   python -m pywin32_postinstall -install
   ```

2. **Test the Collector**
   ```bash
   python notification_counter.py
   ```

3. **Verify Notifications**
   - Trigger a test notification (e.g., from Teams, Outlook)
   - Check that the collector detects it

**Options:**
```bash
# Filter out system notifications
python notification_counter.py --filter-system

# Use simulation mode for testing
python notification_counter.py --simulate
```

#### macOS Setup (Placeholder)

Not yet implemented. Use simulation mode:
```bash
python notification_counter.py --simulate
```

#### Linux Setup (Placeholder)

Not yet implemented. Use simulation mode:
```bash
python notification_counter.py --simulate
```

### Ambient Noise Collection

#### Windows Setup

**Prerequisites:**
- System microphone
- PyAudio library

**Setup Steps:**

1. **Install PyAudio**
   ```bash
   pip install pyaudio
   ```

2. **Grant Microphone Permissions**
   - Open Settings → Privacy → Microphone
   - Enable microphone access for Python/Terminal

3. **List Available Microphones**
   ```bash
   python noise_collector.py --list-devices
   ```

4. **Test the Collector**
   ```bash
   # Use default microphone
   python noise_collector.py

   # Or use specific device
   python noise_collector.py --device 0
   ```

#### macOS Setup

**Prerequisites:**
- System microphone
- Homebrew (for portaudio)

**Setup Steps:**

1. **Install Dependencies**
   ```bash
   brew install portaudio
   pip install pyaudio
   ```

2. **Grant Microphone Permissions**
   - System Preferences → Security & Privacy → Privacy → Microphone
   - Enable microphone access for Terminal

3. **Test the Collector**
   ```bash
   python noise_collector.py --list-devices
   python noise_collector.py
   ```

#### Linux Setup

**Prerequisites:**
- System microphone
- ALSA or PulseAudio

**Setup Steps:**

1. **Install Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install portaudio19-dev python3-pyaudio
   pip install pyaudio

   # Fedora
   sudo dnf install portaudio-devel
   pip install pyaudio
   ```

2. **Test the Collector**
   ```bash
   python noise_collector.py --list-devices
   python noise_collector.py
   ```

## Switching Between Modes

### Method 1: Using the Orchestrator (Recommended)

The orchestrator provides a unified way to manage all collectors.

**Demo Mode (No Real Data):**
```json
{
  "collectors": {
    "hrv": {"enabled": true, "source": "simulated"},
    "notifications": {"enabled": true, "simulate": true},
    "noise": {"enabled": true}
  }
}
```

**Real Data Mode (All Real Sources):**
```json
{
  "collectors": {
    "hrv": {
      "enabled": true,
      "source": "fitbit",
      "config_file": "hrv_config.json"
    },
    "notifications": {
      "enabled": true,
      "simulate": false
    },
    "noise": {
      "enabled": true,
      "device_index": null
    }
  }
}
```

**Hybrid Mode (Mix of Real and Simulated):**
```json
{
  "collectors": {
    "hrv": {
      "enabled": true,
      "source": "fitbit",
      "config_file": "hrv_config.json"
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

**Selective Collectors (Only Some Enabled):**
```json
{
  "collectors": {
    "hrv": {"enabled": true, "source": "fitbit", "config_file": "hrv_config.json"},
    "notifications": {"enabled": false},
    "noise": {"enabled": true}
  }
}
```

### Method 2: Running Collectors Individually

**Demo Mode:**
```bash
python demo_data_generator.py
```

**Real Data Mode:**
```bash
# Terminal 1: Backend
uvicorn main:socket_app --reload

# Terminal 2: HRV
python hrv_collector.py --source fitbit --config hrv_config.json

# Terminal 3: Notifications
python notification_counter.py

# Terminal 4: Noise
python noise_collector.py
```

### Method 3: Command-Line Override

Override configuration file settings:

```bash
# Use different backend URL
python data_collector_orchestrator.py --backend-url http://192.168.1.100:8000

# Use custom config file
python data_collector_orchestrator.py --config my_config.json
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Cannot connect to backend"

**Symptoms:**
- Collectors show connection errors
- Data not appearing in dashboard

**Solutions:**

1. **Verify backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check backend URL in configuration:**
   ```json
   {
     "backend_url": "http://localhost:8000"
   }
   ```

3. **Check firewall settings:**
   - Ensure port 8000 is not blocked
   - Try disabling firewall temporarily to test

4. **Verify network connectivity:**
   ```bash
   ping localhost
   ```

#### Issue: "Fitbit access token expired"

**Symptoms:**
- "Error: Fitbit access token expired or invalid"
- HRV collector falls back to simulated data

**Solutions:**

1. **Get a new access token:**
   - Go to https://dev.fitbit.com/apps
   - Find your app
   - Use OAuth 2.0 tutorial page to get new token

2. **Update configuration file:**
   ```bash
   # Edit hrv_config.json with new token
   nano hrv_config.json
   ```

3. **Implement token refresh (production):**
   - See HRV_SETUP_GUIDE.md for refresh token implementation

#### Issue: "No HRV data available"

**Symptoms:**
- "Warning: No HRV data available from Fitbit/Oura"
- Collector continues with cached or simulated data

**Solutions:**

1. **Sync your device:**
   - Open Fitbit/Oura app
   - Ensure device is synced

2. **Check device compatibility:**
   - Not all Fitbit devices support HRV
   - Verify your device model supports HRV tracking

3. **Wait for sleep data:**
   - HRV is typically measured during sleep
   - Data may not be available until after sleep period

4. **Clear cache and retry:**
   ```bash
   rm hrv_cache.json
   python hrv_collector.py --source fitbit --config hrv_config.json
   ```

#### Issue: "Windows API libraries not available"

**Symptoms:**
- "Error: Windows API libraries not available"
- Notification counter won't start

**Solutions:**

1. **Install pywin32:**
   ```bash
   pip install pywin32
   python -m pywin32_postinstall -install
   ```

2. **Restart terminal/IDE:**
   - Close and reopen terminal
   - Restart your IDE if using one

3. **Use simulation mode for testing:**
   ```bash
   python notification_counter.py --simulate
   ```

#### Issue: "Error initializing microphone"

**Symptoms:**
- "Error initializing microphone"
- Noise collector won't start

**Solutions:**

1. **Check microphone permissions:**
   - Windows: Settings → Privacy → Microphone
   - macOS: System Preferences → Security & Privacy → Microphone
   - Linux: Check PulseAudio/ALSA settings

2. **List available devices:**
   ```bash
   python noise_collector.py --list-devices
   ```

3. **Try specific device:**
   ```bash
   python noise_collector.py --device 0
   ```

4. **Check if microphone is in use:**
   - Close other applications using microphone
   - Restart audio service

5. **Reinstall PyAudio:**
   ```bash
   pip uninstall pyaudio
   pip install pyaudio
   ```

#### Issue: "Input overflowed"

**Symptoms:**
- Warning messages about audio buffer overflow
- Noise collector continues working

**Solutions:**

1. **This is usually harmless:**
   - The collector handles overflow gracefully
   - Data collection continues normally

2. **If persistent, adjust buffer size:**
   - Edit `noise_collector.py`
   - Increase `CHUNK` size (e.g., from 1024 to 2048)

#### Issue: "Orchestrator collector thread failed"

**Symptoms:**
- One or more collectors fail to start
- Orchestrator continues with remaining collectors

**Solutions:**

1. **Check logs:**
   ```bash
   cat logs/collector_orchestrator.log
   ```

2. **Test collector individually:**
   ```bash
   # Test HRV
   python hrv_collector.py --source fitbit --config hrv_config.json

   # Test notifications
   python notification_counter.py

   # Test noise
   python noise_collector.py
   ```

3. **Disable problematic collector:**
   ```json
   {
     "collectors": {
       "hrv": {"enabled": false},
       "notifications": {"enabled": true},
       "noise": {"enabled": true}
     }
   }
   ```

4. **Enable strict mode to debug:**
   ```json
   {
     "graceful_degradation": false
   }
   ```

### Platform-Specific Issues

#### Windows

**Issue: Task Scheduler not starting orchestrator**

**Solutions:**
1. Check task is enabled: `Get-ScheduledTask -TaskName "FlowStateCollector"`
2. Verify paths in task are correct
3. Check task history for errors
4. Run manually first to verify it works

#### macOS

**Issue: Microphone permission denied**

**Solutions:**
1. System Preferences → Security & Privacy → Privacy → Microphone
2. Add Terminal to allowed apps
3. Restart Terminal

#### Linux

**Issue: systemd service fails to start**

**Solutions:**
1. Check service status: `sudo systemctl status flow-state-collector`
2. View logs: `sudo journalctl -u flow-state-collector -n 50`
3. Verify paths in service file
4. Check file permissions

## Security Best Practices

### Protecting API Keys and Tokens

1. **Never commit configuration files:**
   ```bash
   # Add to .gitignore
   echo "*_config.json" >> .gitignore
   echo "hrv_config.json" >> .gitignore
   echo "oura_config.json" >> .gitignore
   echo "collector_config.json" >> .gitignore
   ```

2. **Restrict file permissions:**
   ```bash
   chmod 600 hrv_config.json
   chmod 600 oura_config.json
   ```

3. **Use environment variables (production):**
   ```bash
   export FITBIT_ACCESS_TOKEN="your_token_here"
   export OURA_ACCESS_TOKEN="your_token_here"
   ```

4. **Rotate tokens regularly:**
   - Regenerate access tokens periodically
   - Revoke old tokens when no longer needed

### Network Security

1. **Use HTTPS in production:**
   - Never send tokens over unencrypted connections
   - Configure SSL/TLS for backend API

2. **Restrict CORS origins:**
   ```python
   # In main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Not "*"
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"]
   )
   ```

3. **Use firewall rules:**
   - Restrict access to backend port
   - Only allow connections from trusted sources

### Data Privacy

1. **Local data storage:**
   - All data is processed locally by default
   - No data sent to third parties (except fitness APIs)

2. **Cache files:**
   - HRV cache stored locally: `hrv_cache.json`
   - Clear cache regularly if concerned about privacy

3. **Logging:**
   - Logs don't contain sensitive data
   - Review logs before sharing for debugging

## Advanced Configuration

### Multiple HRV Sources with Fallback

Configure multiple HRV sources in priority order:

```json
{
  "collectors": {
    "hrv": {
      "enabled": true,
      "sources": ["fitbit", "oura", "simulated"],
      "config_file": "hrv_config.json"
    }
  }
}
```

The orchestrator tries each source until one succeeds.

### Custom Update Intervals

Adjust how often each collector sends data:

```json
{
  "send_interval": 5,
  "collectors": {
    "hrv": {
      "enabled": true,
      "interval": 120,
      "source": "fitbit"
    },
    "notifications": {
      "enabled": true,
      "interval": 10
    },
    "noise": {
      "enabled": true,
      "interval": 3
    }
  }
}
```

### Logging Configuration

Adjust log level for debugging:

```json
{
  "log_level": "DEBUG"
}
```

Levels: DEBUG, INFO, WARNING, ERROR

### Graceful Degradation

Control behavior when collectors fail:

```json
{
  "graceful_degradation": true
}
```

- `true`: Continue with available collectors if one fails
- `false`: Stop orchestrator if any collector fails

### Custom Backend URL

Connect to remote backend:

```json
{
  "backend_url": "https://api.example.com"
}
```

Or via command line:
```bash
python data_collector_orchestrator.py --backend-url https://api.example.com
```

## Performance Optimization

### Reducing API Calls

1. **Increase HRV interval:**
   ```json
   {"hrv": {"interval": 300}}
   ```

2. **Use caching:**
   - HRV collector caches data for 5 minutes by default
   - Reduces API calls significantly

3. **Batch updates:**
   - Orchestrator aggregates data before sending
   - Reduces network overhead

### Reducing CPU Usage

1. **Increase send interval:**
   ```json
   {"send_interval": 10}
   ```

2. **Disable unused collectors:**
   ```json
   {"notifications": {"enabled": false}}
   ```

3. **Adjust noise collector interval:**
   ```json
   {"noise": {"interval": 10}}
   ```

### Memory Management

1. **Frontend history limit:**
   - Dashboard limits history to 1000 entries
   - Prevents memory growth over time

2. **Clear cache files periodically:**
   ```bash
   rm hrv_cache.json
   ```

## Next Steps

1. **Test with simulated data first**
2. **Set up one real data source at a time**
3. **Verify each collector works individually**
4. **Use orchestrator to combine all sources**
5. **Configure auto-start for continuous monitoring**
6. **Monitor logs for issues**
7. **Adjust configuration based on your needs**

## Additional Resources

- [HRV Setup Guide](HRV_SETUP_GUIDE.md) - Detailed Fitbit/Oura setup
- [HRV Collector README](HRV_COLLECTOR_README.md) - HRV collector documentation
- [Noise Collector README](NOISE_COLLECTOR_README.md) - Microphone setup
- [Notification Counter README](NOTIFICATION_COUNTER_README.md) - Windows notifications
- [Orchestrator README](ORCHESTRATOR_README.md) - Unified orchestrator
- [Multi-Source Guide](HRV_MULTI_SOURCE_GUIDE.md) - Multiple HRV sources

## Support

For issues or questions:
1. Check this guide first
2. Review collector-specific READMEs
3. Check logs: `logs/collector_orchestrator.log`
4. Test collectors individually
5. Use simulation mode to isolate issues
