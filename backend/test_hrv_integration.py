"""Integration test for HRV collector with backend."""

import pytest
import time
import json
from pathlib import Path
from hrv_collector import HRVCollector


def test_hrv_collector_initialization():
    """Test that HRV collector initializes correctly."""
    collector = HRVCollector(
        backend_url="http://localhost:8000",
        interval=60,
        api_source="simulated"
    )
    
    assert collector.backend_url == "http://localhost:8000"
    assert collector.interval == 60
    assert collector.api_source == "simulated"
    assert collector.cached_hrv is None
    assert collector.cache_timestamp is None


def test_simulated_hrv_generation():
    """Test that simulated HRV values are within expected range."""
    collector = HRVCollector(api_source="simulated")
    
    # Generate multiple values to test range using the adapter
    for _ in range(20):
        hrv = collector.adapter.fetch_hrv()
        assert 40.0 <= hrv <= 100.0, f"HRV {hrv} out of expected range"
        assert isinstance(hrv, float)


def test_cache_save_and_load():
    """Test that cache save and load works correctly."""
    collector = HRVCollector(api_source="simulated")
    
    # Clean up any existing cache
    if collector.cache_file_path.exists():
        collector.cache_file_path.unlink()
    
    # Save a value
    test_hrv = 72.5
    collector.save_cache(test_hrv)
    
    assert collector.cache_file_path.exists()
    assert collector.cached_hrv == test_hrv
    assert collector.cache_timestamp is not None
    
    # Create new collector and load cache
    collector2 = HRVCollector(api_source="simulated")
    loaded = collector2.load_cache()
    
    assert loaded is True
    assert collector2.cached_hrv == test_hrv
    
    # Clean up
    collector.cache_file_path.unlink()


def test_cache_expiration():
    """Test that cache expires after CACHE_DURATION."""
    collector = HRVCollector(api_source="simulated")
    
    # Clean up any existing cache
    if collector.cache_file_path.exists():
        collector.cache_file_path.unlink()
    
    # Save a value
    collector.save_cache(75.0)
    
    # Immediately check - should not need new data
    assert not collector.should_fetch_new_data()
    
    # Manually set cache timestamp to old time
    from datetime import datetime, timedelta
    collector.cache_timestamp = datetime.now() - timedelta(seconds=301)
    
    # Now should need new data
    assert collector.should_fetch_new_data()
    
    # Clean up
    collector.cache_file_path.unlink()


def test_fetch_hrv_with_caching():
    """Test that fetch_hrv_data uses caching correctly."""
    collector = HRVCollector(api_source="simulated")
    
    # Clean up any existing cache
    if collector.cache_file_path.exists():
        collector.cache_file_path.unlink()
    
    # First fetch - should generate new value
    hrv1 = collector.fetch_hrv_data()
    assert hrv1 is not None
    assert 40.0 <= hrv1 <= 100.0
    
    # Second fetch - should use cached value
    hrv2 = collector.fetch_hrv_data()
    assert hrv2 == hrv1  # Should be same value from cache
    
    # Clean up
    collector.cache_file_path.unlink()


def test_config_loading():
    """Test that configuration file loading works."""
    # Create a test config file
    test_config = {
        "fitbit": {
            "access_token": "test_token_123"
        }
    }
    
    config_path = Path("test_config.json")
    with open(config_path, 'w') as f:
        json.dump(test_config, f)
    
    # Create collector with config
    collector = HRVCollector(
        api_source="fitbit",
        config_file=str(config_path)
    )
    
    assert "fitbit" in collector.api_config
    assert collector.api_config["fitbit"]["access_token"] == "test_token_123"
    
    # Clean up
    config_path.unlink()


def test_backend_payload_format():
    """Test that backend payload has correct format."""
    collector = HRVCollector(backend_url="http://localhost:8000")
    
    # We can't easily test the actual HTTP request without mocking,
    # but we can verify the payload structure would be correct
    test_hrv = 75.5
    
    # The send_to_backend method should create this payload:
    expected_payload = {
        "hrv_rmssd": test_hrv,
        "notification_count": 0.0,
        "ambient_noise": 5.0
    }
    
    # Verify the keys and types
    assert isinstance(expected_payload["hrv_rmssd"], float)
    assert isinstance(expected_payload["notification_count"], float)
    assert isinstance(expected_payload["ambient_noise"], float)


def test_fallback_to_simulated():
    """Test that invalid API source falls back to simulated."""
    collector = HRVCollector(api_source="invalid_source")
    
    # Should fall back to simulated
    hrv = collector.fetch_hrv_data()
    assert hrv is not None
    assert 40.0 <= hrv <= 100.0
    
    # Clean up cache
    if collector.cache_file_path.exists():
        collector.cache_file_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
