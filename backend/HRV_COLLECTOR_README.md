# HRV Data Collector

The HRV (Heart Rate Variability) Data Collector fetches HRV data from fitness tracker APIs and sends it to the Flow State Tax Monitor backend. HRV is a key physiological indicator of stress and focus quality.

## Features

- **Multiple API Support**: Fitbit, Oura Ring, and simulated data
- **Smart Caching**: Minimizes API calls by caching data locally (5-minute cache)
- **Rate Limit Handling**: Respects API rate limits and handles errors gracefully
- **Automatic Fallback**: Falls back to simulated data if API is unavailable
- **Token Refresh Support**: Handles authentication token expiration
- **Configurable Intervals**: Customize how often data is sent to backend

## Supported Data Sources

### 1. Simulated Data (Default)
Perfect for testing and development. Generates realistic HRV values using a random walk model.

**Usage:**
```bash
python hrv_collector.py
```

### 2. Fitbit API
Fetches real HRV (RMSSD) data from your Fitbit device.

**Requirements:**
- Fitbit account with a compatible device (Charge 5, Sense, Versa 3, etc.)
- Fitbit Developer App registration
- OAuth 2.0 access token

**Setup:**
1. Go to https://dev.fitbit.com/apps
2. Register a new application
3. Set OAuth 2.0 Application Type to "Personal"
4. Note your Client ID and Client Secret
5. Use the OAuth 2.0 flow to get an access token
6. Create a configuration file (see below)

**Usage:**
```bash
python hrv_collector.py --source fitbit --config fitbit_config.json
```

### 3. Oura Ring API
Fetches HRV data from your Oura Ring.

**Requirements:**
- Oura Ring (Gen 2 or Gen 3)
- Oura account
- Personal Access Token

**Setup:**
1. Go to https://cloud.ouraring.com/personal-access-tokens
2. Create a new Personal Access Token
3. Create a configuration file (see below)

**Usage:**
```bash
python hrv_collector.py --source oura --config oura_config.json
```

### 4. Garmin Connect API
**Status:** Placeholder implementation

Garmin Connect API requires OAuth 1.0 authentication and is more complex to set up. Consider using the Garmin Health API for developers if you need Garmin integration.

## Configuration

### Configuration File Format

Create a JSON file with your API credentials:

```json
{
  "fitbit": {
    "access_token": "eyJhbGciOiJIUzI1NiJ9..."
  },
  "oura": {
    "access_token": "YOUR_OURA_PERSONAL_ACCESS_TOKEN"
  }
}
```

**Security Note:** Keep your configuration file secure and never commit it to version control!

### Example Configuration Files

**fitbit_config.json:**
```json
{
  "fitbit": {
    "access_token": "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyM0JLUkwiLCJzdWIiOiI5V0hYWjIiLCJpc3MiOiJGaXRiaXQiLCJ0eXAiOiJhY2Nlc3NfdG9rZW4iLCJzY29wZXMiOiJyaHIgcnNsZSByYWN0IHJzZXQgcnBybyIsImlhdCI6MTYzOTU4NzYwMCwiZXhwIjoxNjM5NjE2NDAwfQ.abc123..."
  }
}
```

**oura_config.json:**
```json
{
  "oura": {
    "access_token": "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
  }
}
```

## Usage

### Basic Usage

Run with simulated data (no setup required):
```bash
python hrv_collector.py
```

### With Real Fitness Tracker

Run with Fitbit:
```bash
python hrv_collector.py --source fitbit --config fitbit_config.json
```

Run with Oura Ring:
```bash
python hrv_collector.py --source oura --config oura_config.json
```

### Custom Configuration

Specify custom backend URL:
```bash
python hrv_collector.py --backend-url http://192.168.1.100:8000
```

Change update interval (in seconds):
```bash
python hrv_collector.py --interval 120
```

Combine options:
```bash
python hrv_collector.py --source fitbit --config fitbit_config.json --interval 120 --backend-url http://192.168.1.100:8000
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--backend-url` | Backend API URL | `http://localhost:8000` |
| `--interval` | Seconds between updates | `60` |
| `--source` | Data source (fitbit, oura, garmin, simulated) | `simulated` |
| `--config` | Path to API configuration file | None |

## How It Works

1. **Initialization**: Loads configuration and checks cache
2. **Data Fetching**: 
   - Checks if cached data is still valid (< 5 minutes old)
   - If cache is stale, fetches new data from API
   - Falls back to simulated data if API fails
3. **Caching**: Saves fetched data to local cache file (`hrv_cache.json`)
4. **Sending**: Sends HRV data to backend `/data` endpoint
5. **Repeat**: Waits for specified interval and repeats

## Caching Behavior

The collector uses smart caching to minimize API calls:

- **Cache Duration**: 5 minutes (300 seconds)
- **Cache File**: `hrv_cache.json` (created automatically)
- **Cache Invalidation**: Automatic after 5 minutes
- **Benefits**: 
  - Reduces API calls (respects rate limits)
  - Faster response times
  - Works even if API is temporarily unavailable

## API Rate Limits

Different fitness APIs have different rate limits:

| API | Rate Limit | Notes |
|-----|------------|-------|
| Fitbit | 150 requests/hour | Per user |
| Oura | 5,000 requests/day | Per token |
| Garmin | Varies | Depends on API tier |

The collector's default 60-second interval with 5-minute caching means:
- **API calls per hour**: ~12 (well within limits)
- **API calls per day**: ~288 (well within limits)

## Troubleshooting

### "Error: Fitbit access token expired or invalid"

**Solution:** Fitbit access tokens expire after 8 hours. You need to:
1. Implement token refresh using your refresh token
2. Or manually get a new access token from Fitbit Developer Console

### "Error: Cannot connect to backend"

**Solution:** Make sure the backend server is running:
```bash
cd backend
uvicorn main:app --reload
```

### "Warning: No HRV data available"

**Possible causes:**
- Your device hasn't synced recently
- No sleep data available yet (HRV is typically measured during sleep)
- Device doesn't support HRV measurements

**Solution:** 
- Sync your device
- Wait for sleep data to be available
- Use simulated data for testing

### "Error: Oura access token expired or invalid"

**Solution:** Personal Access Tokens don't expire, but they can be revoked. Generate a new token at https://cloud.ouraring.com/personal-access-tokens

## Getting Fitbit Access Token

### Quick Method (For Testing)

1. Go to https://dev.fitbit.com/apps
2. Register a new app (OAuth 2.0 Application Type: Personal)
3. Go to your app's page
4. Scroll to "OAuth 2.0 tutorial page"
5. Click the link and follow the flow
6. Copy the access token

### Production Method (With Refresh)

For production use, implement the full OAuth 2.0 flow with token refresh:

```python
import requests

def refresh_fitbit_token(client_id, client_secret, refresh_token):
    """Refresh Fitbit access token."""
    url = "https://api.fitbit.com/oauth2/token"
    
    auth = (client_id, client_secret)
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    response = requests.post(url, auth=auth, data=data)
    
    if response.status_code == 200:
        tokens = response.json()
        return tokens['access_token'], tokens['refresh_token']
    else:
        raise Exception(f"Token refresh failed: {response.text}")
```

## Getting Oura Access Token

1. Log in to Oura Cloud: https://cloud.ouraring.com
2. Go to Personal Access Tokens: https://cloud.ouraring.com/personal-access-tokens
3. Click "Create A New Personal Access Token"
4. Give it a name (e.g., "Flow State Monitor")
5. Copy the token (you won't be able to see it again!)
6. Add it to your configuration file

## HRV Data Explained

**What is HRV?**
Heart Rate Variability (HRV) measures the variation in time between heartbeats. Higher HRV generally indicates:
- Better stress resilience
- Better recovery
- Better focus capacity

**RMSSD:**
Root Mean Square of Successive Differences (RMSSD) is a specific HRV metric that:
- Measures short-term HRV
- Reflects parasympathetic nervous system activity
- Typical range: 40-100 ms (higher is generally better)

**In Flow State Tax Monitor:**
- HRV contributes 50% to the Focus Quality Score
- Higher HRV = Higher FQS (better focus)
- Expected range: 40-100 ms

## Integration with Other Collectors

The HRV collector works alongside:
- **Noise Collector** (`noise_collector.py`): Captures ambient noise
- **Notification Counter** (`notification_counter.py`): Tracks notifications

For complete monitoring, run all three collectors simultaneously. See the main README for orchestration setup.

## Example Output

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
Using cached HRV: 72.5
HRV: 72.5 ms ✓ Sent to backend
Fetching HRV data from fitbit...
Fetched HRV from Fitbit: 74.2
HRV: 74.2 ms ✓ Sent to backend
```

## Future Enhancements

Potential improvements for future versions:
- Apple HealthKit integration (macOS/iOS)
- Garmin Connect API implementation
- Polar H10 direct Bluetooth connection
- Automatic token refresh for Fitbit
- Multiple device support
- Historical data backfill
- Data quality indicators

## Requirements

See `requirements.txt` for Python dependencies:
- `requests`: HTTP client for API calls
- `python-dotenv`: Environment variable management (optional)

## License

Part of the Flow State Tax Monitor project.
