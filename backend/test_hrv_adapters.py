"""
Unit tests for HRV adapters.

Tests the adapter pattern implementation for multiple HRV data sources.
"""

import pytest
from hrv_adapters import (
    HRVAdapter,
    FitbitAdapter,
    GarminAdapter,
    OuraAdapter,
    AppleHealthKitAdapter,
    SimulatedAdapter,
    AdapterFactory
)


class TestAdapterFactory:
    """Test the AdapterFactory."""
    
    def test_create_simulated_adapter(self):
        """Test creating a simulated adapter."""
        adapter = AdapterFactory.create_adapter("simulated", {})
        assert isinstance(adapter, SimulatedAdapter)
        assert adapter.get_source_name() == "Simulated"
    
    def test_create_fitbit_adapter(self):
        """Test creating a Fitbit adapter."""
        config = {"access_token": "test_token"}
        adapter = AdapterFactory.create_adapter("fitbit", config)
        assert isinstance(adapter, FitbitAdapter)
        assert adapter.get_source_name() == "Fitbit"
    
    def test_create_oura_adapter(self):
        """Test creating an Oura adapter."""
        config = {"access_token": "test_token"}
        adapter = AdapterFactory.create_adapter("oura", config)
        assert isinstance(adapter, OuraAdapter)
        assert adapter.get_source_name() == "Oura Ring"
    
    def test_create_garmin_adapter(self):
        """Test creating a Garmin adapter."""
        config = {
            "consumer_key": "key",
            "consumer_secret": "secret",
            "access_token": "token",
            "access_token_secret": "token_secret"
        }
        adapter = AdapterFactory.create_adapter("garmin", config)
        assert isinstance(adapter, GarminAdapter)
        assert adapter.get_source_name() == "Garmin Connect"
    
    def test_create_apple_healthkit_adapter(self):
        """Test creating an Apple HealthKit adapter."""
        adapter = AdapterFactory.create_adapter("apple_healthkit", {})
        assert isinstance(adapter, AppleHealthKitAdapter)
        assert adapter.get_source_name() == "Apple HealthKit"
    
    def test_create_healthkit_alias(self):
        """Test that 'healthkit' is an alias for 'apple_healthkit'."""
        adapter = AdapterFactory.create_adapter("healthkit", {})
        assert isinstance(adapter, AppleHealthKitAdapter)
    
    def test_create_unknown_adapter_raises_error(self):
        """Test that creating an unknown adapter raises ValueError."""
        with pytest.raises(ValueError, match="Unknown HRV source"):
            AdapterFactory.create_adapter("unknown_source", {})
    
    def test_get_available_sources(self):
        """Test getting list of available sources."""
        sources = AdapterFactory.get_available_sources()
        assert "fitbit" in sources
        assert "garmin" in sources
        assert "oura" in sources
        assert "apple_healthkit" in sources
        assert "healthkit" in sources
        assert "simulated" in sources
    
    def test_case_insensitive_source_names(self):
        """Test that source names are case-insensitive."""
        adapter1 = AdapterFactory.create_adapter("FITBIT", {"access_token": "test"})
        adapter2 = AdapterFactory.create_adapter("Fitbit", {"access_token": "test"})
        adapter3 = AdapterFactory.create_adapter("fitbit", {"access_token": "test"})
        
        assert isinstance(adapter1, FitbitAdapter)
        assert isinstance(adapter2, FitbitAdapter)
        assert isinstance(adapter3, FitbitAdapter)


class TestSimulatedAdapter:
    """Test the SimulatedAdapter."""
    
    def test_fetch_hrv_returns_float(self):
        """Test that fetch_hrv returns a float value."""
        adapter = SimulatedAdapter({})
        hrv = adapter.fetch_hrv()
        assert isinstance(hrv, float)
    
    def test_fetch_hrv_in_valid_range(self):
        """Test that simulated HRV is in valid range."""
        adapter = SimulatedAdapter({})
        hrv = adapter.fetch_hrv()
        assert 40.0 <= hrv <= 100.0
    
    def test_fetch_hrv_random_walk(self):
        """Test that simulated HRV uses random walk (values change slightly)."""
        adapter = SimulatedAdapter({})
        hrv1 = adapter.fetch_hrv()
        hrv2 = adapter.fetch_hrv()
        
        # Values should be different but close (random walk)
        assert hrv1 != hrv2
        assert abs(hrv1 - hrv2) < 20  # Should not jump too much
    
    def test_validate_config_always_true(self):
        """Test that simulated adapter always validates."""
        adapter = SimulatedAdapter({})
        assert adapter.validate_config() is True


class TestFitbitAdapter:
    """Test the FitbitAdapter."""
    
    def test_validate_config_with_token(self):
        """Test config validation with access token."""
        adapter = FitbitAdapter({"access_token": "test_token"})
        assert adapter.validate_config() is True
    
    def test_validate_config_without_token(self):
        """Test config validation without access token."""
        adapter = FitbitAdapter({})
        assert adapter.validate_config() is False
    
    def test_fetch_hrv_without_token_returns_none(self):
        """Test that fetch_hrv returns None without token."""
        adapter = FitbitAdapter({})
        hrv = adapter.fetch_hrv()
        assert hrv is None


class TestOuraAdapter:
    """Test the OuraAdapter."""
    
    def test_validate_config_with_token(self):
        """Test config validation with access token."""
        adapter = OuraAdapter({"access_token": "test_token"})
        assert adapter.validate_config() is True
    
    def test_validate_config_without_token(self):
        """Test config validation without access token."""
        adapter = OuraAdapter({})
        assert adapter.validate_config() is False
    
    def test_fetch_hrv_without_token_returns_none(self):
        """Test that fetch_hrv returns None without token."""
        adapter = OuraAdapter({})
        hrv = adapter.fetch_hrv()
        assert hrv is None


class TestGarminAdapter:
    """Test the GarminAdapter."""
    
    def test_validate_config_with_all_fields(self):
        """Test config validation with all required fields."""
        config = {
            "consumer_key": "key",
            "consumer_secret": "secret",
            "access_token": "token",
            "access_token_secret": "token_secret"
        }
        adapter = GarminAdapter(config)
        assert adapter.validate_config() is True
    
    def test_validate_config_missing_fields(self):
        """Test config validation with missing fields."""
        adapter = GarminAdapter({"consumer_key": "key"})
        assert adapter.validate_config() is False
    
    def test_fetch_hrv_returns_none_placeholder(self):
        """Test that Garmin adapter returns None (placeholder)."""
        config = {
            "consumer_key": "key",
            "consumer_secret": "secret",
            "access_token": "token",
            "access_token_secret": "token_secret"
        }
        adapter = GarminAdapter(config)
        hrv = adapter.fetch_hrv()
        assert hrv is None


class TestAppleHealthKitAdapter:
    """Test the AppleHealthKitAdapter."""
    
    def test_validate_config_always_true(self):
        """Test that HealthKit adapter always validates."""
        adapter = AppleHealthKitAdapter({})
        assert adapter.validate_config() is True
    
    def test_fetch_hrv_returns_none_placeholder(self):
        """Test that HealthKit adapter returns None (placeholder)."""
        adapter = AppleHealthKitAdapter({})
        hrv = adapter.fetch_hrv()
        assert hrv is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
