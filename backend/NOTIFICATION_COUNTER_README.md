# Windows Notification Counter

A Python script that monitors Windows notifications and sends normalized notification counts to the Flow State Tax Monitor backend API.

## Overview

The notification counter tracks Windows notification events in a rolling 5-minute window and normalizes the count to a 0-5 scale for API compatibility. This data is used to calculate the Focus Quality Score (FQS), as notifications are a key indicator of digital interruptions that impact focus.

## Features

- **Rolling Window Tracking**: Counts notifications in a 5-minute rolling window
- **Normalization**: Maps notification counts to 0-5 scale (0 = no notifications, 5 = 20+ notifications)
- **Filtering Options**: Filter system vs app notifications
- **Graceful Error Handling**: Handles Windows API access errors
- **Simulation Mode**: Test without Windows API for development
- **Real-time Updates**: Sends data to backend at configurable intervals

## Requirements

### Windows-Specific Requirements

- Windows 10 or Windows 11
- Python 3.9+
- pywin32 library for Windows API access

### Installation

```bash
pip install pywin32 requests
```

After installing pywin32, you may need to run the post-install script:

```bash
python -m pywin32_postinstall -install
```

## Usage

### Basic Usage

Run with default settings (connects to localhost:8000, 5-second intervals):

```bash
python notification_counter.py
```

### Custom Backend URL

```bash
python notification_counter.py --backend-url http://192.168.1.100:8000
```

### Custom Update Interval

Send data every 10 seconds instead of 5:

```bash
python notification_counter.py --interval 10
```

### Filtering Notifications

Exclude system notifications:

```bash
python notification_counter.py --filter-system
```

Exclude app notifications:

```bash
python notification_counter.py --filter-app
```

### Simulation Mode

For testing without Windows API (useful for development on non-Windows systems):

```bash
python notification_counter.py --simulate
```

## How It Works

### Notification Detection

The script uses Windows API (win32gui) to detect notification windows. It looks for windows with specific class names associated with Windows 10/11 notifications:

- `Windows.UI.Core.CoreWindow`
- `NotifyIcon`
- `ToastNotification`

### Rolling Window

Notifications are tracked in a 5-minute rolling window using a deque data structure. Old notifications are automatically removed as they fall outside the window.

### Normalization

The raw notification count is normalized to a 0-5 scale:

- 0 notifications → 0.0
- 1-19 notifications → Linear interpolation (e.g., 10 notifications → 2.5)
- 20+ notifications → 5.0

Formula: `normalized = (count / 20) * 5.0`

### Data Transmission

The script sends data to the backend `/data` endpoint with this payload structure:

```json
{
  "hrv_rmssd": 70.0,
  "notification_count": 2.5,
  "ambient_noise": 5.0
}
```

Note: HRV and noise are set to neutral default values (70.0 and 5.0) since this script only tracks notifications. Use the unified orchestrator to combine data from all sources.

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--backend-url` | Backend API URL | `http://localhost:8000` |
| `--interval` | Seconds between updates | `5` |
| `--filter-system` | Exclude system notifications | `False` |
| `--filter-app` | Exclude app notifications | `False` |
| `--simulate` | Run in simulation mode | `False` |

## Output

The script displays real-time information:

```
Starting notification counter...
Sending data to: http://localhost:8000/data
Interval: 5 seconds
Rolling window: 300 seconds (5 minutes)
Press Ctrl+C to stop

[10:30:15] Detected notification: Microsoft Teams
Notifications (5min): 3 -> 0.75/5 (Total: 15) ✓ Sent to backend
Notifications (5min): 3 -> 0.75/5 (Total: 15) ✓ Sent to backend
[10:30:42] Detected notification: Outlook
Notifications (5min): 4 -> 1.00/5 (Total: 16) ✓ Sent to backend
```

## Limitations

### Current Implementation

The current implementation uses window enumeration to detect notifications, which has some limitations:

- May not catch all notification types
- Polling-based approach (checks every second)
- May miss very brief notifications

### Future Improvements

For production use, consider:

- Using Windows notification APIs directly (Windows.UI.Notifications)
- Monitoring the Windows notification database
- Using event-driven approach instead of polling
- Adding support for notification content analysis

## Troubleshooting

### "Windows API libraries not available"

Install pywin32:

```bash
pip install pywin32
python -m pywin32_postinstall -install
```

### "Cannot connect to backend"

Ensure the backend server is running:

```bash
cd backend
python main.py
```

### "This script only works on Windows"

Use simulation mode for testing on other platforms:

```bash
python notification_counter.py --simulate
```

### No notifications detected

- Check Windows notification settings (Settings → System → Notifications)
- Ensure notifications are enabled for apps
- Try triggering a test notification
- Consider using simulation mode to verify the rest of the system works

## Integration with Flow State Tax Monitor

This script is part of the Flow State Tax Monitor system. To use it with the full system:

1. Start the backend server:
   ```bash
   cd backend
   python main.py
   ```

2. Start the frontend dashboard:
   ```bash
   cd frontend
   npm start
   ```

3. Start the notification counter:
   ```bash
   cd backend
   python notification_counter.py
   ```

4. (Optional) Start other data collectors:
   ```bash
   python noise_collector.py
   # python hrv_collector.py (when implemented)
   ```

The notification data will flow through the system and appear in the dashboard, contributing to the Focus Quality Score calculation.

## Technical Details

### Thread Safety

The script uses threading to separate notification monitoring from data transmission. A lock ensures thread-safe access to the notification queue.

### Error Handling

- Windows API errors are caught and logged
- Connection errors to backend are handled gracefully
- The script continues running even if individual operations fail

### Performance

- Minimal CPU usage (polling at 1-second intervals)
- Memory-efficient deque for rolling window
- Automatic cleanup of old notifications

## License

Part of the Flow State Tax Monitor project.