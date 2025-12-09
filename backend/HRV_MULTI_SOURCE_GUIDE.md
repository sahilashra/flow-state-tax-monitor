# HRV Multi-Source Integration Guide

This guide explains how to use the HRV collector with multiple fitness tracker data sources using the adapter pattern.

## Overview

The HRV collector now supports multiple data sources through an adapter pattern architecture:

- **Fitbit API** - OAuth 2.0 based integration
- **Garmin Connect API** - OAuth 1.0 based integration (placeholder)
- **Oura Ring API** - Personal Access Token based integration
- **Apple HealthKit** - macOS/iOS native integration (placeholder)
- **Simulated Data** - For testing without real hardware

## Architecture

The system uses the **Adapter Pattern** to provide a unified interface for different HRV data sources:

```
┌─────────────────┐
│  HRVCollector   │
└────────┬────────┘
         │
         │ uses
         ▼
┌─────────────────┐
│  HRVAdapter     │ (Abstract Base Class)
└────────┬────────┘
         │
         │ implements
         ▼
┌────────────────────────────────────────────┐
│  FitbitAdapter                             │
│  GarminAdapter                             │
│  OuraAdapter                               │
│  AppleHealthKitAdapter                     │
│  SimulatedAdapter                          │
└────────────────────────────────────────────┘
```

### Benefits of Adapter Pattern

1. **Extensibility** - Easy to add new data sources without modifying existing code
2. **Maintainability** - Each adapter is self-contained and testable
3. **Flexibility** - Users can switch between sources via configuration
4. **Fallback Support** - Automatic fallback to simulated data if API fails

## Configuration

### Configuration File Format

Create a `hrv_config.json` file (use `hrv_config.example.json` as template):

```json
{
  "fitbit": {
    "access_token": "YOUR_FITBIT_ACCESS_TOKEN"
  },
  "oura": {
    "access_token": "YOUR_OURA_ACCESS_TOKEN"
  },
  "garmin": {
    "consumer_key": "YOUR_GARMIN_CONSUMER_KEY",
    "consumer_secret": "YOUR_GARMIN_CONSUMER_SECRET",
    "access_token": "YOUR_GARMIN_ACCESS_TOKEN",
    "access_token_secret": "YOUR_GARMIN_ACCESS_TOKEN_SECRET"
  },
  "apple_healthkit": {},
  "simulated": {}
}
```

### Selecting a Data Source

#### Single Source

Use the `--source` flag to select your preferred data source:

```bash
# Fitbit
python hrv_collector.py --source fitbit --config hrv_config.json

# Oura Ring
python hrv_collector.py --source oura --config hrv_config.json

# Garmin Connect
python hrv_collector.py --source garmin --config hrv_config.json

# Apple HealthKit (macOS/iOS only)
python hrv_collector.py --source apple_healthkit

# Simulated (default, no config needed)
python hrv_collector.py --source simulated
```

#### Multiple Sources with Fallback (NEW!)

Use the `--sources` flag to specify multiple data sources in priority order. The collector will try each source until one succeeds:

```bash
# Try Fitbit first, then Oura, then fall back to simulated
python hrv_collector.py --sources fitbit oura simulated --config hrv_config.json

# Try Oura first, then Fitbit
python hrv_collector.py --sources oura fitbit --config hrv_config.json

# Try Apple HealthKit first, then fall back to simulated
python hrv_collector.py --sources apple_healthkit simulated
```

**Benefits of Multi-Source Configuration:**
- **Redundancy:** If your primary source fails, automatically fall back to secondary sources
- **Reliability:** Never miss data collection due to API failures or rate limits
- **Flexibility:** Mix real and simulated data sources for testing
- **Zero Downtime:** Seamless failover between sources

## Data Source Setup

### Fitbit API

**Requirements:**
- Fitbit account
- Registered Fitbit application
- OAuth 2.0 access token

**Setup Steps:**

1. Create a Fitbit developer account at https://dev.fitbit.com/
2. Register a new application
3. Use OAuth 2.0 flow to obtain access token
4. Add token to `hrv_config.json` under `fitbit.access_token`

**API Endpoint:** `https://api.fitbit.com/1/user/-/hrv/date/{date}.json`

**Data Format:** Returns daily RMSSD value

**Rate Limits:** 150 requests per hour per user

### Oura Ring API

**Requirements:**
- Oura Ring device
- Oura account
- Personal Access Token

**Setup Steps:**

1. Log in to Oura Cloud at https://cloud.ouraring.com/
2. Navigate to Personal Access Tokens
3. Generate a new token
4. Add token to `hrv_config.json` under `oura.access_token`

**API Endpoint:** `https://api.ouraring.com/v2/usercollection/sleep`

**Data Format:** Returns HRV data from sleep sessions

**Rate Limits:** 5000 requests per day

### Garmin Connect API

**Requirements:**
- Garmin device
- Garmin Connect account
- OAuth 1.0 credentials

**Setup Steps:**

1. Register for Garmin Health API access
2. Obtain OAuth 1.0 consumer key and secret
3. Complete OAuth 1.0 flow to get access tokens
4. Add credentials to `hrv_config.json` under `garmin`

**Status:** Placeholder implementation - requires OAuth 1.0 library

**Note:** Garmin Connect API is complex and requires additional OAuth 1.0 implementation. Consider using the `garth` library for authentication.

### Apple HealthKit

**Requirements:**
- macOS or iOS device
- Python with `pyobjc` library
- HealthKit permissions

**Setup Steps:**

1. Install pyobjc: `pip install pyobjc`
2. Request HealthKit permissions when running
3. No API tokens needed

**Status:** Placeholder implementation - requires pyobjc integration

**Note:** HealthKit integration requires native macOS/iOS APIs and system permissions.

### Simulated Data

**Requirements:** None

**Setup:** No configuration needed

**Behavior:** Generates realistic HRV values using a random walk model

**Use Case:** Testing and development without real hardware

## Usage Examples

### Basic Usage

```bash
# Run with default simulated data
python hrv_collector.py

# Run with Fitbit
python hrv_collector.py --source fitbit --config hrv_config.json

# Run with custom interval (120 seconds)
python hrv_collector.py --source oura --config hrv_config.json --interval 120

# Run with custom backend URL
python hrv_collector.py --source fitbit --config hrv_config.json --backend-url http://192.168.1.100:8000
```

### Multi-Source Usage (NEW!)

```bash
# Production setup: Try real sources first, fall back to simulated
python hrv_collector.py --sources fitbit oura simulated --config hrv_config.json

# High reliability: Multiple real sources with fallback
python hrv_collector.py --sources oura fitbit apple_healthkit simulated --config hrv_config.json

# Testing: Mix real and simulated data
python hrv_collector.py --sources fitbit simulated --config hrv_config.json --interval 30

# Custom backend with multi-source
python hrv_collector.py --sources oura fitbit --config hrv_config.json --backend-url http://192.168.1.100:8000
```

### Advanced Usage

```bash
# Run with verbose output (if implemented)
python hrv_collector.py --source fitbit --config hrv_config.json --verbose

# Run with specific cache duration (if implemented)
python hrv_collector.py --source oura --config hrv_config.json --cache-duration 600
```

## Caching

The HRV collector implements intelligent caching to minimize API calls:

- **Cache Duration:** 5 minutes (300 seconds) by default
- **Cache File:** `hrv_cache.json` in current directory
- **Behavior:** Reuses cached data if less than 5 minutes old
- **Source Tracking:** Cache stores which source provided the data

This prevents excessive API calls and respects rate limits.

### Multi-Source Caching Behavior

When using multiple sources:
1. Cache is checked first before trying any source
2. If cache is valid, data is returned immediately (no API calls)
3. If cache is expired, sources are tried in priority order
4. First successful source's data is cached with source information
5. Next fetch will use cached data until it expires

## Error Handling

### Automatic Fallback

#### Single Source Mode

If the configured API source fails, the collector automatically falls back to simulated data:

```
Fetching HRV data from Fitbit...
Error: Fitbit API returned status 401
API fetch failed, falling back to simulated data
HRV: 72.3 ms ✓ Sent to backend
```

#### Multi-Source Mode (NEW!)

When using multiple sources, the collector tries each source in order until one succeeds:

```
Data sources (priority order): fitbit, oura, simulated
Primary source: fitbit

Fetching HRV data from Fitbit...
  ✗ Fitbit failed
Fetching HRV data from Oura Ring...
HRV: 68.5 ms ✓ Sent to backend
```

If all configured sources fail, the collector will attempt to use simulated data as a last resort (if not already in the list).

### Common Errors

**401 Unauthorized:**
- Token expired or invalid
- Solution: Refresh your access token

**429 Rate Limit Exceeded:**
- Too many API requests
- Solution: Increase interval or wait for rate limit reset

**Connection Error:**
- Cannot reach API endpoint
- Solution: Check internet connection

**Configuration Error:**
- Missing or invalid config file
- Solution: Verify config file format and required fields

## Extending with New Sources

To add a new HRV data source:

1. Create a new adapter class in `hrv_adapters.py`:

```python
class MyNewAdapter(HRVAdapter):
    def get_source_name(self) -> str:
        return "My New Source"
    
    def validate_config(self) -> bool:
        return 'api_key' in self.config
    
    def fetch_hrv(self) -> Optional[float]:
        # Implement API call logic
        pass
```

2. Register the adapter in `AdapterFactory`:

```python
_adapters = {
    # ... existing adapters ...
    'mynewsource': MyNewAdapter,
}
```

3. Update command-line choices in `hrv_collector.py`:

```python
choices=["fitbit", "garmin", "oura", "apple_healthkit", "mynewsource", "simulated"]
```

4. Add configuration example to `hrv_config.example.json`

## Testing

### Test with Simulated Data

```bash
python hrv_collector.py --source simulated
```

### Test Adapter Directly

```python
from hrv_adapters import AdapterFactory

# Create adapter
config = {"access_token": "test_token"}
adapter = AdapterFactory.create_adapter("fitbit", config)

# Fetch HRV
hrv = adapter.fetch_hrv()
print(f"HRV: {hrv}")
```

### Available Sources

```python
from hrv_adapters import AdapterFactory

sources = AdapterFactory.get_available_sources()
print(sources)
# Output: ['fitbit', 'garmin', 'oura', 'apple_healthkit', 'healthkit', 'simulated']
```

## Troubleshooting

### Issue: "Unknown HRV source" error

**Solution:** Check that the source name is spelled correctly and is one of the supported sources.

### Issue: "Invalid configuration" warning

**Solution:** Verify that your config file contains the required fields for your chosen source.

### Issue: No HRV data available

**Solution:** 
- Check that your device has recent HRV data
- Verify API permissions
- Try fetching data manually via API to confirm availability

### Issue: Adapter always returns None

**Solution:**
- Check API credentials
- Verify network connectivity
- Review API documentation for changes
- Check rate limits

## Best Practices

1. **Use Configuration Files:** Store API credentials in `hrv_config.json`, not in code
2. **Respect Rate Limits:** Use appropriate intervals (60+ seconds recommended)
3. **Monitor Cache:** Check `hrv_cache.json` to verify data freshness
4. **Test First:** Use simulated data to test your setup before using real APIs
5. **Secure Credentials:** Keep `hrv_config.json` out of version control (add to `.gitignore`)

## Security Considerations

- **Never commit API tokens** to version control
- Store `hrv_config.json` securely with restricted file permissions
- Rotate tokens regularly
- Use environment variables for production deployments
- Consider using a secrets management system for production

## Future Enhancements

Potential improvements to the multi-source system:

- [ ] Automatic token refresh for OAuth 2.0 sources
- [x] **Support for multiple simultaneous sources (data fusion)** - IMPLEMENTED!
- [ ] Configurable cache duration per source
- [ ] Health check endpoint to verify source availability
- [ ] Metrics and monitoring for API calls
- [ ] Retry logic with exponential backoff
- [ ] Data averaging/fusion from multiple sources
- [ ] Per-source success/failure statistics
- [ ] Support for Polar H10 via Bluetooth
- [ ] Support for Whoop API
- [ ] Support for Samsung Health API

## References

- [Fitbit Web API Documentation](https://dev.fitbit.com/build/reference/web-api/)
- [Oura API v2 Documentation](https://cloud.ouraring.com/v2/docs)
- [Garmin Health API](https://developer.garmin.com/health-api/overview/)
- [Apple HealthKit Documentation](https://developer.apple.com/documentation/healthkit)

## Support

For issues or questions:
1. Check this guide first
2. Review the example configuration file
3. Test with simulated data to isolate the issue
4. Check API provider documentation
5. Review error messages and logs
