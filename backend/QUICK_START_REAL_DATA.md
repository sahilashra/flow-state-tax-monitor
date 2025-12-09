# Quick Start: Real Data Collection

This is a quick reference for getting started with real data collection. For comprehensive documentation, see [REAL_DATA_INTEGRATION_GUIDE.md](REAL_DATA_INTEGRATION_GUIDE.md).

## 🚀 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Start Backend

```bash
uvicorn main:socket_app --reload
```

### Step 3: Choose Your Mode

#### Option A: Demo Mode (Fastest)

```bash
python demo_data_generator.py
```

✅ No setup required  
✅ Works immediately  
✅ Great for testing  

#### Option B: Simulated Mode (Recommended for Development)

```bash
# Generate config
python data_collector_orchestrator.py --generate-config

# Run orchestrator
python data_collector_orchestrator.py
```

✅ Tests full system  
✅ No hardware required  
✅ Realistic data patterns  

#### Option C: Real Data Mode (Production)

See setup instructions below for each data source.

## 📊 Setting Up Real Data Sources

### HRV (Heart Rate Variability)

#### Fitbit (5 minutes)

1. **Get access token:**
   - Go to https://dev.fitbit.com/apps
   - Register app (OAuth 2.0 Type: Personal)
   - Use OAuth tutorial page to get token

2. **Create config:**
   ```bash
   echo '{"fitbit": {"access_token": "YOUR_TOKEN"}}' > hrv_config.json
   ```

3. **Test:**
   ```bash
   python hrv_collector.py --source fitbit --config hrv_config.json
   ```

📖 [Detailed Fitbit Setup](HRV_SETUP_GUIDE.md#setup-with-fitbit)

#### Oura Ring (3 minutes)

1. **Get token:**
   - Go to https://cloud.ouraring.com/personal-access-tokens
   - Create new token

2. **Create config:**
   ```bash
   echo '{"oura": {"access_token": "YOUR_TOKEN"}}' > oura_config.json
   ```

3. **Test:**
   ```bash
   python hrv_collector.py --source oura --config oura_config.json
   ```

📖 [Detailed Oura Setup](HRV_SETUP_GUIDE.md#setup-with-oura)

### Notifications (Windows Only)

#### Windows (2 minutes)

1. **Install library:**
   ```bash
   pip install pywin32
   python -m pywin32_postinstall -install
   ```

2. **Test:**
   ```bash
   python notification_counter.py
   ```

📖 [Notification Counter Details](NOTIFICATION_COUNTER_README.md)

### Ambient Noise (All Platforms)

#### Windows (1 minute)

```bash
pip install pyaudio
python noise_collector.py
```

#### macOS (2 minutes)

```bash
brew install portaudio
pip install pyaudio
python noise_collector.py
```

#### Linux (2 minutes)

```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
python noise_collector.py
```

📖 [Noise Collector Details](NOISE_COLLECTOR_README.md)

## 🔄 Switching Modes

### Using Orchestrator (Recommended)

Edit `collector_config.json`:

**Simulated Mode:**
```json
{
  "collectors": {
    "hrv": {"enabled": true, "source": "simulated"},
    "notifications": {"enabled": true, "simulate": true},
    "noise": {"enabled": true}
  }
}
```

**Real Data Mode:**
```json
{
  "collectors": {
    "hrv": {"enabled": true, "source": "fitbit", "config_file": "hrv_config.json"},
    "notifications": {"enabled": true, "simulate": false},
    "noise": {"enabled": true}
  }
}
```

**Hybrid Mode (Real HRV, Simulated Others):**
```json
{
  "collectors": {
    "hrv": {"enabled": true, "source": "fitbit", "config_file": "hrv_config.json"},
    "notifications": {"enabled": true, "simulate": true},
    "noise": {"enabled": true}
  }
}
```

Then run:
```bash
python data_collector_orchestrator.py
```

### Running Individually

**Demo:**
```bash
python demo_data_generator.py
```

**Real Data:**
```bash
# Terminal 1: HRV
python hrv_collector.py --source fitbit --config hrv_config.json

# Terminal 2: Notifications (Windows)
python notification_counter.py

# Terminal 3: Noise
python noise_collector.py
```

## 🐛 Quick Troubleshooting

### "Cannot connect to backend"

```bash
# Check backend is running
curl http://localhost:8000/health

# If not, start it
uvicorn main:socket_app --reload
```

### "Fitbit token expired"

```bash
# Get new token from https://dev.fitbit.com/apps
# Update hrv_config.json with new token
```

### "Microphone error"

```bash
# List available microphones
python noise_collector.py --list-devices

# Try specific device
python noise_collector.py --device 0
```

### "Windows API not available"

```bash
# Install pywin32
pip install pywin32
python -m pywin32_postinstall -install

# Or use simulation
python notification_counter.py --simulate
```

## 📚 Full Documentation

- **[Real Data Integration Guide](REAL_DATA_INTEGRATION_GUIDE.md)** - Comprehensive setup guide
- **[HRV Setup Guide](HRV_SETUP_GUIDE.md)** - Detailed API setup for fitness trackers
- **[Orchestrator README](ORCHESTRATOR_README.md)** - Full orchestrator documentation
- **[Troubleshooting](REAL_DATA_INTEGRATION_GUIDE.md#troubleshooting)** - Common issues and solutions

## 🎯 Recommended Path

1. ✅ Start with **Demo Mode** to verify system works
2. ✅ Try **Simulated Mode** with orchestrator
3. ✅ Set up **one real data source** (start with noise - easiest)
4. ✅ Add **HRV** from fitness tracker
5. ✅ Add **notifications** (Windows only)
6. ✅ Configure **auto-start** for continuous monitoring

## 💡 Tips

- **Start simple:** Test with simulated data first
- **One at a time:** Set up one data source at a time
- **Check logs:** `logs/collector_orchestrator.log` for debugging
- **Use hybrid mode:** Mix real and simulated sources during setup
- **Secure tokens:** Never commit config files with API keys

## 🔐 Security Reminder

```bash
# Add to .gitignore
echo "*_config.json" >> .gitignore

# Restrict permissions
chmod 600 hrv_config.json
chmod 600 oura_config.json
```

## ⚡ Auto-Start

### Windows

```powershell
.\setup_windows_task.ps1
```

### Linux

```bash
sudo cp flow-state-collector.service /etc/systemd/system/
sudo systemctl enable flow-state-collector
sudo systemctl start flow-state-collector
```

---

**Need help?** See [REAL_DATA_INTEGRATION_GUIDE.md](REAL_DATA_INTEGRATION_GUIDE.md) for detailed instructions.
