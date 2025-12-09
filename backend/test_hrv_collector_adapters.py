"""
Integration tests for HRV collector with adapter pattern.

Tests that the HRV collector correctly uses adapters to fetch data.
"""

import pytest
import json
import tempfile
from pathlib import Path
from hrv_collector import HRVCollector


class TestHRVCollectorWithAdapters:
    """Test HRV collector integration with adapters."""
    
    def test_collector_initializes_with_simulated_adapter(self):
        """Test that collector initializes with simulated adapter by default."""
        collector = HRVCollector(api_source="simulated")
        assert collector.adapter is not None
        assert collector.adapter.get_source_name() == "Simulated"
    
    def test_collector_initializes_with_fitbit_adapter(self):
        """Test that collector initializes with Fitbit adapter."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {"fitbit": {"access_token": "test_token"}}
            json.dump(config, f)
            config_file = f.name
        
        try:
            collector = HRVCollector(
                api_source="fitbit",
                config_file=config_file
            )
            assert collector.adapter is not None
            assert collector.adapter.get_source_name() == "Fitbit"
        finally:
            Path(config_file).unlink()
    
    def test_collector_initializes_with_oura_adapter(self):
        """Test that collector initializes with Oura adapter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {"oura": {"access_token": "test_token"}}
            json.dump(config, f)
            config_file = f.name
        
        try:
            collector = HRVCollector(
                api_source="oura",
                config_file=config_file
            )
            assert collector.adapter is not None
            assert collector.adapter.get_source_name() == "Oura Ring"
        finally:
            Path(config_file).unlink()
    
    def test_collector_falls_back_to_simulated_on_unknown_source(self):
        """Test that collector falls back to simulated on unknown source."""
        collector = HRVCollector(api_source="unknown_source")
        assert collector.adapter is not None
        assert collector.adapter.get_source_name() == "Simulated"
    
    def test_collector_falls_back_to_simulated_on_missing_config(self):
        """Test that collector falls back to simulated when config file is missing."""
        collector = HRVCollector(
            api_source="fitbit",
            config_file="nonexistent_config.json"
        )
        assert collector.adapter is not None
        assert collector.adapter.get_source_name() == "Simulated"
    
    def test_fetch_hrv_data_returns_value(self):
        """Test that fetch_hrv_data returns a value using adapter."""
        collector = HRVCollector(api_source="simulated")
        hrv = collector.fetch_hrv_data()
        assert hrv is not None
        assert isinstance(hrv, float)
        assert 40.0 <= hrv <= 100.0
    
    def test_fetch_hrv_data_uses_cache(self):
        """Test that fetch_hrv_data uses cached value when available."""
        collector = HRVCollector(api_source="simulated")
        
        # First fetch
        hrv1 = collector.fetch_hrv_data()
        
        # Second fetch should use cache (same value)
        hrv2 = collector.fetch_hrv_data()
        
        assert hrv1 == hrv2
    
    def test_adapter_fallback_on_api_failure(self):
        """Test that collector falls back to simulated when API fails."""
        # Create config with invalid token
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {"fitbit": {"access_token": "invalid_token"}}
            json.dump(config, f)
            config_file = f.name
        
        try:
            collector = HRVCollector(
                api_source="fitbit",
                config_file=config_file
            )
            
            # Force cache to expire
            collector.cache_timestamp = None
            
            # Fetch should fall back to simulated
            hrv = collector.fetch_hrv_data()
            assert hrv is not None
            assert isinstance(hrv, float)
        finally:
            Path(config_file).unlink()
            # Clean up cache file if created
            if collector.cache_file_path.exists():
                collector.cache_file_path.unlink()


class TestMultiSourceSupport:
    """Test multi-source HRV collection with fallback."""
    
    def test_collector_initializes_with_multiple_sources(self):
        """Test that collector initializes with multiple sources."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "fitbit": {"access_token": "test_token"},
                "oura": {"access_token": "test_token"}
            }
            json.dump(config, f)
            config_file = f.name
        
        try:
            collector = HRVCollector(
                sources=["fitbit", "oura", "simulated"],
                config_file=config_file
            )
            assert len(collector.adapters) == 3
            assert collector.adapters[0].get_source_name() == "Fitbit"
            assert collector.adapters[1].get_source_name() == "Oura Ring"
            assert collector.adapters[2].get_source_name() == "Simulated"
            assert collector.api_source == "fitbit"  # Primary source
        finally:
            Path(config_file).unlink()
    
    def test_collector_falls_back_through_sources(self):
        """Test that collector tries sources in order until one succeeds."""
        # Create config with invalid tokens (will fail)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "fitbit": {"access_token": "invalid_token"},
                "oura": {"access_token": "invalid_token"}
            }
            json.dump(config, f)
            config_file = f.name
        
        try:
            collector = HRVCollector(
                sources=["fitbit", "oura", "simulated"],
                config_file=config_file
            )
            
            # Force cache to expire
            collector.cache_timestamp = None
            
            # Fetch should fall back to simulated (third source)
            hrv = collector.fetch_hrv_data()
            assert hrv is not None
            assert isinstance(hrv, float)
            assert 40.0 <= hrv <= 100.0
        finally:
            Path(config_file).unlink()
            # Clean up cache file if created
            if collector.cache_file_path.exists():
                collector.cache_file_path.unlink()
    
    def test_collector_with_single_source_via_sources_param(self):
        """Test that collector works with single source via sources parameter."""
        collector = HRVCollector(sources=["simulated"])
        assert len(collector.adapters) == 1
        assert collector.adapter.get_source_name() == "Simulated"
        assert collector.api_source == "simulated"
    
    def test_sources_parameter_overrides_api_source(self):
        """Test that sources parameter takes precedence over api_source."""
        collector = HRVCollector(
            api_source="fitbit",
            sources=["simulated"]
        )
        assert collector.api_source == "simulated"
        assert len(collector.adapters) == 1
        assert collector.adapter.get_source_name() == "Simulated"
    
    def test_cache_stores_source_information(self):
        """Test that cache stores which source provided the data."""
        collector = HRVCollector(sources=["simulated"])
        
        # Fetch data
        hrv = collector.fetch_hrv_data()
        
        # Check cache file contains source info
        assert collector.cache_file_path.exists()
        with open(collector.cache_file_path, 'r') as f:
            cache_data = json.load(f)
        
        assert 'source' in cache_data
        assert cache_data['source'] == 'simulated'
        
        # Clean up
        collector.cache_file_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
