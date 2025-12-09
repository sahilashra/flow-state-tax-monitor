"""
Integration test for multi-source HRV collection.

Tests the complete multi-source workflow with fallback behavior.
"""

import pytest
import json
import tempfile
from pathlib import Path
from hrv_collector import HRVCollector


class TestMultiSourceIntegration:
    """Integration tests for multi-source HRV collection."""
    
    def test_multi_source_initialization(self):
        """Test that collector properly initializes with multiple sources."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "fitbit": {"access_token": "test_fitbit_token"},
                "oura": {"access_token": "test_oura_token"},
                "simulated": {}
            }
            json.dump(config, f)
            config_file = f.name
        
        try:
            collector = HRVCollector(
                sources=["fitbit", "oura", "simulated"],
                config_file=config_file
            )
            
            # Verify all adapters are initialized
            assert len(collector.adapters) == 3
            assert len(collector.sources) == 3
            
            # Verify primary source
            assert collector.api_source == "fitbit"
            assert collector.adapter.get_source_name() == "Fitbit"
            
            # Verify source order
            assert collector.sources == ["fitbit", "oura", "simulated"]
            
        finally:
            Path(config_file).unlink()
    
    def test_multi_source_fallback_chain(self):
        """Test that collector falls back through sources in order."""
        # Create config with invalid tokens (will fail for real APIs)
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
            
            # Clear cache to force fresh fetch
            collector.cache_timestamp = None
            
            # Fetch should fall back to simulated (third in chain)
            hrv = collector.fetch_hrv_data()
            
            # Verify we got valid HRV data
            assert hrv is not None
            assert isinstance(hrv, float)
            assert 40.0 <= hrv <= 100.0
            
            # Verify cache was updated with simulated source
            assert collector.cache_source == "simulated"
            
        finally:
            Path(config_file).unlink()
            if collector.cache_file_path.exists():
                collector.cache_file_path.unlink()
    
    def test_multi_source_with_only_simulated(self):
        """Test multi-source with only simulated data works."""
        collector = HRVCollector(sources=["simulated"])
        
        assert len(collector.adapters) == 1
        assert collector.api_source == "simulated"
        
        # Fetch data
        hrv = collector.fetch_hrv_data()
        assert hrv is not None
        assert 40.0 <= hrv <= 100.0
        
        # Clean up
        if collector.cache_file_path.exists():
            collector.cache_file_path.unlink()
    
    def test_multi_source_cache_includes_source(self):
        """Test that cache file includes source information."""
        collector = HRVCollector(sources=["simulated"])
        
        # Fetch data to populate cache
        hrv = collector.fetch_hrv_data()
        
        # Verify cache file exists and contains source
        assert collector.cache_file_path.exists()
        
        with open(collector.cache_file_path, 'r') as f:
            cache_data = json.load(f)
        
        assert 'source' in cache_data
        assert cache_data['source'] == 'simulated'
        assert cache_data['hrv'] == hrv
        
        # Clean up
        collector.cache_file_path.unlink()
    
    def test_multi_source_respects_cache(self):
        """Test that multi-source respects cache and doesn't retry sources."""
        collector = HRVCollector(sources=["simulated"])
        
        # First fetch
        hrv1 = collector.fetch_hrv_data()
        
        # Second fetch should use cache (same value)
        hrv2 = collector.fetch_hrv_data()
        
        assert hrv1 == hrv2
        
        # Clean up
        if collector.cache_file_path.exists():
            collector.cache_file_path.unlink()
    
    def test_sources_parameter_case_insensitive(self):
        """Test that source names are case-insensitive in multi-source mode."""
        collector = HRVCollector(sources=["SIMULATED", "Fitbit"])
        
        # Should normalize to lowercase
        assert "simulated" in collector.sources
        
        # Clean up
        if collector.cache_file_path.exists():
            collector.cache_file_path.unlink()
    
    def test_empty_sources_list_falls_back_to_simulated(self):
        """Test that empty sources list falls back to simulated."""
        collector = HRVCollector(sources=[])
        
        # Should have at least simulated adapter
        assert len(collector.adapters) >= 1
        
        # Should be able to fetch data
        hrv = collector.fetch_hrv_data()
        assert hrv is not None
        
        # Clean up
        if collector.cache_file_path.exists():
            collector.cache_file_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
