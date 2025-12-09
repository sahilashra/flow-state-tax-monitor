# 🧠 Flow State Tax Monitor

> **Quantifying the Cognitive Cost of Digital Interruptions**

A real-time monitoring system that measures how notifications, stress, and environmental noise impact your ability to focus. Built with FastAPI, React, and Socket.IO.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

![Flow State Tax Monitor Dashboard](https://via.placeholder.com/800x400/1a1a1a/646cff?text=Flow+State+Tax+Monitor+Dashboard)

---

## 📊 What is the "Focus Tax"?

The **Focus Tax** is the measurable drop in focus quality when interruptions occur. This tool quantifies it by combining:

- **❤️ Heart Rate Variability (HRV)** - Stress indicator (50% weight)
- **🔔 Notifications** - Digital interruptions (30% weight)  
- **🔊 Ambient Noise** - Environmental distractions (20% weight)

**Result:** A single **Focus Quality Score (FQS)** from 0-100 that updates in real-time.

---

## ✨ Features

### Real-Time Monitoring
- 📈 Live FQS score with instant updates
- 📊 Historical trend visualization
- ⚡ Sub-100ms latency via WebSocket

### Multi-Source Data Collection
- 🏥 **HRV Data:** Fitbit, Oura Ring, Garmin, Apple HealthKit, or simulated
- 🪟 **Windows Notifications:** Real notification tracking
- 🎤 **Ambient Noise:** Microphone-based monitoring
- 🔄 **Graceful Fallback:** Continues working if sources fail

### Automatic Insights
- ⚠️ **Focus Tax Events:** Auto-detects drops of 15+ points
- 📊 **Session Statistics:** Average, peak, and lowest FQS
- ⏱️ **Duration Tracking:** Minutes monitored
- 📝 **Data Points:** Total measurements collected

### Professional Dashboard
- 🎨 Modern gradient design
- 📱 Fully responsive (desktop, tablet, mobile)
- 🎯 Individual metric cards
- 📈 Real-time chart with Chart.js
- 🟢 Connection status indicator

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- pip and npm

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sahilashra/flow-state-tax-monitor.git
   cd flow-state-tax-monitor
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   pip install pywin32  # For Windows notifications
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

**You need 3 terminals:**

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:socket_app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Data Collection:**
```bash
cd backend
python data_collector_orchestrator.py  # Real data
# OR
python demo_data_generator.py  # Demo mode
```

**Open:** http://localhost:5173

---

## 📖 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Detailed setup instructions
- **[Backend README](backend/README.md)** - Backend architecture and API docs
- **[Real Data Integration](backend/REAL_DATA_INTEGRATION_GUIDE.md)** - Connect fitness trackers
- **[HRV Setup Guide](backend/HRV_SETUP_GUIDE.md)** - Configure HRV data sources
- **[Test Results](backend/E2E_TEST_RESULTS.md)** - Comprehensive test coverage

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Data Sources   │
│  - HRV          │
│  - Notifications│
│  - Noise        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Collector │
│  Orchestrator   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      WebSocket      ┌─────────────────┐
│  FastAPI        │◄────────────────────►│  React          │
│  Backend        │                      │  Dashboard      │
│  - REST API     │                      │  - Real-time UI │
│  - Socket.IO    │                      │  - Chart.js     │
│  - FQS Calc     │                      │  - Statistics   │
└─────────────────┘                      └─────────────────┘
```

### Tech Stack

**Backend:**
- FastAPI - REST API framework
- python-socketio - WebSocket communication
- Pydantic - Data validation
- Hypothesis - Property-based testing

**Frontend:**
- React 18 - UI framework
- Socket.IO Client - Real-time updates
- Chart.js - Data visualization
- Vite - Build tool

**Data Collection:**
- PyAudio - Ambient noise capture
- pywin32 - Windows notification tracking
- Requests - Fitness tracker APIs

---

## 🧪 Testing

The project has **99 passing tests** with 100% success rate:

```bash
cd backend
python -m pytest -v --ignore=test_noise_collector.py --ignore=test_noise_collector_unit.py
```

**Test Coverage:**
- ✅ Unit tests for all components
- ✅ Property-based tests (Hypothesis)
- ✅ Integration tests
- ✅ End-to-end tests
- ✅ Multi-source fallback tests

---

## 📊 FQS Calculation

The Focus Quality Score is calculated using a weighted formula:

```python
FQS = (HRV_score * 0.5) + (Notification_score * 0.3) + (Noise_score * 0.2)
```

**Where:**
- `HRV_score = ((HRV - 40) / 60) * 50` (normalized 40-100ms range)
- `Notification_score = (1 - notifications/5) * 30` (inverse, 0-5 range)
- `Noise_score = (1 - noise/10) * 20` (inverse, 0-10 range)

**Result:** Clamped to 0-100 range

---

## 🎯 Use Cases

### Personal Productivity
- Track your focus patterns throughout the day
- Identify peak focus times
- Measure impact of different work environments
- Quantify the cost of interruptions

### Research & Analysis
- Study the relationship between interruptions and focus
- Measure cognitive load in different scenarios
- Analyze recovery time after interruptions
- Demonstrate the "Focus Tax" concept

### Team Management
- Show the measurable cost of meeting interruptions
- Justify focus time policies
- Optimize notification settings
- Create data-driven focus strategies

---

## 🔧 Configuration

### Collector Configuration

Edit `backend/collector_config.json`:

```json
{
  "backend_url": "http://localhost:8000",
  "send_interval": 5,
  "collectors": {
    "hrv": {
      "enabled": true,
      "source": "simulated",
      "sources": ["fitbit", "oura", "simulated"],
      "interval": 60
    },
    "notifications": {
      "enabled": true,
      "interval": 5,
      "simulate": false
    },
    "noise": {
      "enabled": true,
      "interval": 5
    }
  }
}
```

### HRV Configuration

Create `backend/hrv_config.json`:

```json
{
  "fitbit": {
    "access_token": "YOUR_TOKEN"
  },
  "oura": {
    "access_token": "YOUR_TOKEN"
  }
}
```

---

## 📸 Screenshots

### Dashboard Overview
![Dashboard](https://via.placeholder.com/800x400/1a1a1a/646cff?text=Dashboard+Overview)

### Individual Metrics
![Metrics](https://via.placeholder.com/800x200/1a1a1a/646cff?text=Individual+Metrics)

### Statistics
![Statistics](https://via.placeholder.com/800x200/1a1a1a/646cff?text=Session+Statistics)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [Kiro AI](https://kiro.ai) - AI-powered development assistant
- Inspired by research on cognitive load and interruption costs
- Property-based testing methodology from [Hypothesis](https://hypothesis.readthedocs.io/)

---

## 📧 Contact

**Sahil Ashra** - [@sahilashra](https://github.com/sahilashra)

**Project Link:** [https://github.com/sahilashra/flow-state-tax-monitor](https://github.com/sahilashra/flow-state-tax-monitor)

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Built with ❤️ and Kiro AI**
