# Multi-Source HRV Collection - Quick Start Guide

## Overview

The HRV collector now supports **multiple data sources with automatic fallback**. This means you can configure a priority chain of HRV sources, and the system will automatically try each one until it gets valid data.

## Why Use Multiple Sources?

- **Reliability**: Never miss data collection due to API failures
- **Redundancy**: Automatic failback if your primary source is down
- **Flexibility**: Mix real and simulated data for testing
- **Zero Downtime**: Seamless failover between sources

## Quick Examples

### Basic Multi-Source Setup

Try Fitbit first, then Oura, then fall back to simulated data:

```bash
python hrv_collector.py --sources fitbit oura simulated --config hrv_config.json
```

### Production Setup

High reliability with multiple real sources:

```bash
python hrv_collector.py --sources oura fitbit apple_healthkit simulated --config hrv_config.json
```

### Testing Setup

Mix real and simulated data:

```bash
python hrv_collector.py --sources fitbit simulated --config hrv_config.json --interval 30
```

## How It Works

1. **Priority Order**: Sources are tried in the order you specify
2. **Automatic Fallback**: If a source fails, the next one is tried automatically
3. **Caching**: Successful data is cached to minimize API calls
4. **Source Tracking**: Cache remembers which source provided the data

### Example Output

```
HRV Data Collector
==================
Data sources (priority order): fitbit, oura, simulated
Primary source: fitbit
Backend URL: http://localhost:8000/data
Interval: 60 seconds
Cache duration: 300 seconds

Press Ctrl+C to stop

Fetching HRV data from Fitbit...
  ✗ Fitbit failed
Fetching HRV data from Oura Ring...
HRV: 68.5 ms ✓ Sent to backend
```

## Configuration

Your `hrv_config.json` should include credentials for all sources you want to use:

```json
{
  "fitbit": {
    "access_token": "YOUR_FITBIT_TOKEN"
  },
  "oura": {
    "access_token": "YOUR_OURA_TOKEN"
  },
  "garmin": {
    "consumer_key": "YOUR_GARMIN_KEY",
    "consumer_secret": "YOUR_GARMIN_SECRET",
    "access_token": "YOUR_GARMIN_TOKEN",
    "access_token_secret": "YOUR_GARMIN_TOKEN_SECRET"
  },
  "apple_healthkit": {},
  "simulated": {}
}
```

## Command-Line Options

### Single Source (Original Behavior)

```bash
python hrv_collector.py --source fitbit --config hrv_config.json
```

### Multiple Sources (New!)

```bash
python hrv_collector.py --sources fitbit oura simulated --config hrv_config.json
```

**Note**: If you use `--sources`, it overrides `--source`.

## Common Patterns

### Pattern 1: Real Source + Simulated Fallback

Perfect for development and testing:

```bash
python hrv_collector.py --sources fitbit simulated --config hrv_config.json
```

### Pattern 2: Multiple Real Sources

Maximum reliability for production:

```bash
python hrv_collector.py --sources oura fitbit --config hrv_config.json
```

### Pattern 3: All Sources

Try everything:

```bash
python hrv_collector.py --sources fitbit oura garmin apple_healthkit simulated --config hrv_config.json
```

## Caching Behavior

- Cache is checked **before** trying any source
- If cache is valid (< 5 minutes old), no API calls are made
- When cache expires, sources are tried in priority order
- First successful source's data is cached
- Cache stores which source provided the data

## Troubleshooting

### All Sources Failing

If all configured sources fail, the system will try simulated data as a last resort (if not already in your list).

### One Source Always Failing

Check the error messages to identify which source is failing and why:
- 401: Token expired or invalid
- 429: Rate limit exceeded
- Connection errors: Network issues

### Cache Not Working

Delete `hrv_cache.json` to force a fresh fetch from all sources.

## Testing Your Setup

Test with simulated data first:

```bash
python hrv_collector.py --sources simulated
```

Then add your real sources one at a time:

```bash
python hrv_collector.py --sources fitbit simulated --config hrv_config.json
```

## More Information

For detailed documentation, see:
- `HRV_MULTI_SOURCE_GUIDE.md` - Complete guide
- `HRV_SETUP_GUIDE.md` - API setup instructions
- `hrv_config.example.json` - Configuration template

## Support

If you encounter issues:
1. Test with simulated data first
2. Check your configuration file
3. Verify API credentials
4. Review error messages
5. Check the detailed guide

## What's New

✅ **Multi-source support with priority ordering**
✅ **Automatic fallback chain**
✅ **Source tracking in cache**
✅ **Improved error handling**
✅ **Comprehensive test coverage**

Enjoy reliable HRV data collection! 🎉
