# HRV Collector Setup Guide

This guide walks you through setting up the HRV collector with real fitness tracker data.

## Quick Start (Simulated Data)

The easiest way to get started is with simulated data:

```bash
python hrv_collector.py
```

This requires no setup and generates realistic HRV values for testing.

## Setup with Fitbit

### Prerequisites
- Fitbit account
- Compatible Fitbit device (Charge 5, Sense, Versa 3, Inspire 3, or newer)
- Device must support HRV tracking

### Step 1: Register a Fitbit Developer App

1. Go to https://dev.fitbit.com/apps
2. Click "Register a New App"
3. Fill in the application details:
   - **Application Name**: Flow State Monitor (or your choice)
   - **Description**: Personal HRV monitoring
   - **Application Website**: http://localhost (for personal use)
   - **Organization**: Your name
   - **Organization Website**: http://localhost
   - **OAuth 2.0 Application Type**: **Personal**
   - **Callback URL**: http://localhost:8080/callback
   - **Default Access Type**: Read-Only
4. Agree to terms and click "Register"
5. Note your **Client ID** and **Client Secret**

### Step 2: Get Access Token

#### Option A: Using Fitbit's OAuth 2.0 Tutorial Page (Easiest)

1. Go to your app's page on https://dev.fitbit.com/apps
2. Scroll down to find the "OAuth 2.0 tutorial page" link
3. Click the link and follow the authorization flow
4. After authorizing, you'll see your access token and refresh token
5. Copy the **access_token** (it's a long string starting with "eyJ...")

#### Option B: Manual OAuth Flow (For Production)

If you need automatic token refresh, implement the full OAuth 2.0 flow:

```python
import requests
from urllib.parse import urlencode

# Step 1: Get authorization code
client_id = "YOUR_CLIENT_ID"
redirect_uri = "http://localhost:8080/callback"
scope = "heartrate"

auth_url = f"https://www.fitbit.com/oauth2/authorize?{urlencode({
    'response_type': 'code',
    'client_id': client_id,
    'redirect_uri': redirect_uri,
    'scope': scope
})}"

print(f"Visit this URL: {auth_url}")
# User visits URL, authorizes, gets redirected with code parameter
code = input("Enter the code from the redirect URL: ")

# Step 2: Exchange code for tokens
token_url = "https://api.fitbit.com/oauth2/token"
client_secret = "YOUR_CLIENT_SECRET"

response = requests.post(
    token_url,
    auth=(client_id, client_secret),
    data={
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }
)

tokens = response.json()
print(f"Access Token: {tokens['access_token']}")
print(f"Refresh Token: {tokens['refresh_token']}")
```

### Step 3: Create Configuration File

Create `fitbit_config.json`:

```json
{
  "fitbit": {
    "access_token": "YOUR_ACCESS_TOKEN_HERE"
  }
}
```

**Important:** Keep this file secure! Add it to `.gitignore`.

### Step 4: Run the Collector

```bash
python hrv_collector.py --source fitbit --config fitbit_config.json
```

### Troubleshooting Fitbit

**"Error: Fitbit access token expired or invalid"**
- Fitbit access tokens expire after 8 hours
- You need to refresh the token using your refresh token
- Or get a new token from the OAuth tutorial page

**"Warning: No HRV data available from Fitbit"**
- Make sure your device has synced recently
- HRV data is typically collected during sleep
- Check that your device supports HRV (not all Fitbit devices do)

## Setup with Oura Ring

### Prerequisites
- Oura Ring (Gen 2 or Gen 3)
- Oura account

### Step 1: Get Personal Access Token

1. Log in to Oura Cloud: https://cloud.ouraring.com
2. Go to Personal Access Tokens: https://cloud.ouraring.com/personal-access-tokens
3. Click "Create A New Personal Access Token"
4. Give it a name (e.g., "Flow State Monitor")
5. Copy the token (you won't be able to see it again!)

### Step 2: Create Configuration File

Create `oura_config.json`:

```json
{
  "oura": {
    "access_token": "YOUR_OURA_TOKEN_HERE"
  }
}
```

### Step 3: Run the Collector

```bash
python hrv_collector.py --source oura --config oura_config.json
```

### Troubleshooting Oura

**"Error: Oura access token expired or invalid"**
- Personal Access Tokens don't expire automatically
- If you see this error, the token may have been revoked
- Generate a new token from the Oura Cloud dashboard

**"Warning: No HRV data available from Oura"**
- Oura collects HRV data during sleep
- Make sure you've worn your ring during sleep recently
- Data may take a few hours to sync after waking up

## Setup with Garmin

**Status:** Not yet implemented

Garmin Connect API requires OAuth 1.0 authentication and is more complex to set up. If you need Garmin support, consider:

1. Using Garmin Health API (for developers)
2. Exporting data manually from Garmin Connect
3. Using a third-party integration service

## Testing Your Setup

### 1. Test with Simulated Data First

```bash
python hrv_collector.py
```

Make sure the backend is running and data is being sent successfully.

### 2. Test with Real API

```bash
python hrv_collector.py --source fitbit --config fitbit_config.json
```

You should see output like:
```
HRV Data Collector
==================
Data source: fitbit
Backend URL: http://localhost:8000/data
Interval: 60 seconds
Cache duration: 300 seconds

Press Ctrl+C to stop

Fetching HRV data from fitbit...
Fetched HRV from Fitbit: 72.5
HRV: 72.5 ms ✓ Sent to backend
```

### 3. Verify in Dashboard

Open the frontend dashboard and verify that HRV data is being displayed.

## Common Issues

### "Error: Cannot connect to backend"

**Solution:** Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

### "Error: Configuration file not found"

**Solution:** Make sure your config file exists and the path is correct:
```bash
# Check if file exists
ls fitbit_config.json

# Use absolute path if needed
python hrv_collector.py --source fitbit --config /full/path/to/fitbit_config.json
```

### API Rate Limits

If you hit rate limits:
- Increase the `--interval` parameter (default is 60 seconds)
- The collector uses caching to minimize API calls
- Default cache duration is 5 minutes

### Data Not Updating

If HRV values seem stuck:
- Check that your device has synced recently
- Delete the cache file: `rm hrv_cache.json`
- Restart the collector

## Advanced Configuration

### Custom Update Interval

Send data every 2 minutes instead of 1 minute:
```bash
python hrv_collector.py --interval 120
```

### Custom Backend URL

Connect to a remote backend:
```bash
python hrv_collector.py --backend-url http://192.168.1.100:8000
```

### Running as a Service

#### Windows (Task Scheduler)

1. Create a batch file `start_hrv_collector.bat`:
```batch
@echo off
cd C:\path\to\backend
python hrv_collector.py --source fitbit --config fitbit_config.json
```

2. Open Task Scheduler
3. Create a new task that runs at startup
4. Set the action to run your batch file

#### Linux (systemd)

Create `/etc/systemd/system/hrv-collector.service`:
```ini
[Unit]
Description=HRV Data Collector
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/backend
ExecStart=/usr/bin/python3 hrv_collector.py --source fitbit --config fitbit_config.json
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable hrv-collector
sudo systemctl start hrv-collector
```

#### macOS (launchd)

Create `~/Library/LaunchAgents/com.flowstate.hrv-collector.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.flowstate.hrv-collector</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/backend/hrv_collector.py</string>
        <string>--source</string>
        <string>fitbit</string>
        <string>--config</string>
        <string>/path/to/fitbit_config.json</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.flowstate.hrv-collector.plist
```

## Security Best Practices

1. **Never commit config files to git**
   - Add `*_config.json` to `.gitignore`
   - Use environment variables for production

2. **Protect your tokens**
   - Store config files with restricted permissions: `chmod 600 config.json`
   - Use a secrets manager for production deployments

3. **Rotate tokens regularly**
   - Regenerate access tokens periodically
   - Revoke old tokens when no longer needed

4. **Use HTTPS in production**
   - Never send tokens over unencrypted connections
   - Use SSL/TLS for backend API

## Next Steps

Once you have the HRV collector running:

1. Set up the [Noise Collector](NOISE_COLLECTOR_README.md)
2. Set up the [Notification Counter](NOTIFICATION_COUNTER_README.md)
3. Run all collectors together for complete monitoring
4. View your Focus Quality Score in the dashboard

## Support

For issues or questions:
- Check the [main README](README.md)
- Review the [HRV Collector README](HRV_COLLECTOR_README.md)
- Check Fitbit API documentation: https://dev.fitbit.com/build/reference/
- Check Oura API documentation: https://cloud.ouraring.com/docs/
