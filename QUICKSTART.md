# 🚀 Flow State Tax Monitor - Quick Start Guide

This guide shows you exactly what to run in each terminal to get the Flow State Tax Monitor up and running.

---

## 📋 Prerequisites

Make sure you have:
- ✅ Python 3.9+ installed
- ✅ Node.js 16+ installed
- ✅ Dependencies installed (see below)

---

## 🔧 One-Time Setup

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
pip install pywin32  # For Windows notifications
```

### Frontend Setup

```bash
cd frontend
npm install
```

---

## 🎬 Running the Application

You need **3 terminals** open. Here's what to run in each:

### Terminal 1: Backend Server 🖥️

```bash
cd backend
uvicorn main:socket_app --host 0.0.0.0 --port 8000 --reload
```

**What you should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

**Keep this running!** This is your backend API + WebSocket server.

---

### Terminal 2: Frontend Dashboard 📊

```bash
cd frontend
npm run dev
```

**What you should see:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Open your browser to:** `http://localhost:5173`

You should see the Flow State Tax Monitor dashboard with:
- 🟢 "Connected" status (green indicator)
- Current FQS Score display
- Empty chart (waiting for data)

**Keep this running!**

---

### Terminal 3: Data Collection 📡

**Choose ONE of these options:**

#### Option A: Real Data Collection (Recommended)

Collects real Windows notifications + simulated HRV/noise:

```bash
cd backend
python data_collector_orchestrator.py
```

**What you should see:**
```
============================================================
Data Collector Orchestrator Starting
============================================================
Backend URL: http://localhost:8000
Send interval: 5 seconds
Graceful degradation: True
Started 3 collector threads
Press Ctrl+C to stop

Starting notification monitoring (polling mode)...
Initialized Simulated adapter
Fetching HRV data from Simulated...

HRV: 75.2 | Notifications: 0.00 | Noise: 5.00
✓ Data sent to backend
```

**This tracks:**
- ✅ **Real Windows notifications** (your actual notifications!)
- 🔄 Simulated HRV (baseline ~70ms)
- 🔄 Default noise level (neutral 5.0)

---

#### Option B: Demo Mode (For Testing)

Generates realistic simulated data including "Focus Tax" events:

```bash
cd backend
python demo_data_generator.py
```

**What you should see:**
```
Starting demo data generator...
Sending data to: http://localhost:8000/data
Interval: 2 seconds
Press Ctrl+C to stop

HRV: 85.3 | Notifications: 1 | Noise: 3.2 ✓ Sent
HRV: 82.1 | Notifications: 0 | Noise: 4.1 ✓ Sent
```

**This simulates:**
- Random HRV fluctuations
- Occasional notification spikes
- Varying noise levels
- "Focus Tax" events (sudden FQS drops)

---

## 🎯 What You Should See

### In Your Browser Dashboard

1. **Connection Status:** 🟢 Connected (top right)
2. **Current FQS Score:** Large number (0-100)
   - 80-100: Excellent Focus 🟢
   - 60-79: Good Focus 🟡
   - 40-59: Moderate Focus 🟠
   - 0-39: Poor Focus 🔴
3. **FQS History Chart:** Line graph updating in real-time

### In Terminal 3 (Data Collector)

You'll see logs every 5 seconds:
```
HRV: 72.5 | Notifications: 2.00 | Noise: 5.00
✓ Data sent to backend
```

### In Terminal 1 (Backend)

You'll see connection logs:
```
Client connected to /focus_update: <socket_id>
```

---

## 🧪 Testing It Out

### Test Real Notifications (Option A)

1. Open some apps (Settings, File Explorer, etc.)
2. Get some notifications (emails, messages)
3. Watch your FQS drop as notifications increase!

### Test Demo Mode (Option B)

1. Just watch the dashboard
2. You'll see natural FQS fluctuations
3. Occasional "Focus Tax" events (sudden drops)

---

## 🛑 Stopping Everything

Press `Ctrl+C` in each terminal to stop:

1. **Terminal 3** (Data Collector) - Stop first
2. **Terminal 2** (Frontend) - Stop second
3. **Terminal 1** (Backend) - Stop last

---

## 🔍 Troubleshooting

### Dashboard shows "Disconnected" or "Connection Error"

**Problem:** Backend not running or wrong command used

**Solution:**
```bash
# Make sure you're using socket_app, not app!
cd backend
uvicorn main:socket_app --host 0.0.0.0 --port 8000 --reload
```

---

### No data appearing on dashboard

**Problem:** Data collector not running

**Solution:** Make sure Terminal 3 is running one of:
- `python data_collector_orchestrator.py` (real data)
- `python demo_data_generator.py` (demo mode)

---

### "Module not found" errors

**Problem:** Dependencies not installed

**Solution:**
```bash
# Backend
cd backend
pip install -r requirements.txt
pip install pywin32

# Frontend
cd frontend
npm install
```

---

### Windows notification tracking not working

**Problem:** pywin32 not installed

**Solution:**
```bash
cd backend
pip install pywin32
python test_windows_notifications.py  # Test it
```

---

## 📊 Understanding Your FQS Score

The Focus Quality Score (FQS) is calculated from three factors:

| Factor | Weight | Impact |
|--------|--------|--------|
| **HRV** (Heart Rate Variability) | 50% | Higher = Better focus |
| **Notifications** | 30% | More = Worse focus |
| **Ambient Noise** | 20% | Higher = Worse focus |

**Example Scenarios:**

**High Focus (FQS: 85)**
- HRV: 90ms (excellent)
- Notifications: 0 (none)
- Noise: 2/10 (quiet)

**Interrupted Focus (FQS: 35)**
- HRV: 60ms (stressed)
- Notifications: 5 (many)
- Noise: 8/10 (loud)

---

## 🎯 Next Steps

### Add More Real Data Sources

**Real HRV from Fitness Tracker:**
- See: `backend/HRV_SETUP_GUIDE.md`
- Supports: Fitbit, Oura Ring, Garmin, Apple HealthKit

**Real Ambient Noise:**
```bash
pip install pyaudio  # or pipwin install pyaudio
```
Then restart the orchestrator.

### Customize Settings

Edit `backend/collector_config.json` to:
- Change data collection intervals
- Enable/disable specific collectors
- Configure notification filtering
- Adjust graceful degradation behavior

---

## 📚 Additional Documentation

- **Full Setup Guide:** `backend/README.md`
- **Real Data Integration:** `backend/REAL_DATA_INTEGRATION_GUIDE.md`
- **HRV Setup:** `backend/HRV_SETUP_GUIDE.md`
- **Orchestrator Config:** `backend/ORCHESTRATOR_README.md`
- **Test Results:** `backend/E2E_TEST_RESULTS.md`

---

## ✅ Quick Reference

### Three Terminals Summary

| Terminal | Command | Purpose |
|----------|---------|---------|
| **1** | `uvicorn main:socket_app --host 0.0.0.0 --port 8000 --reload` | Backend API + WebSocket |
| **2** | `npm run dev` | Frontend Dashboard |
| **3** | `python data_collector_orchestrator.py` | Real Data Collection |
| **3 (alt)** | `python demo_data_generator.py` | Demo Mode |

### URLs

- **Dashboard:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 🎉 You're All Set!

Your Flow State Tax Monitor is now running and tracking your focus quality in real-time!

**Questions or issues?** Check the troubleshooting section above or refer to the detailed documentation in the `backend/` folder.

Happy focusing! 🧠✨
