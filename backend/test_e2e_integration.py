"""
End-to-End Integration Tests for Real Data Collection
Tests the complete flow from data collectors through backend to ensure all components work together.

This test suite verifies:
1. Ambient noise collector captures and sends data correctly
2. Notification counter tracks and sends data correctly
3. HRV collector fetches and sends data correctly
4. All data appears correctly in dashboard (via backend API)
5. FQS calculations are accurate with real data
6. Graceful degradation when collectors fail

Requirements: Task 19 - Checkpoint for real data integration
"""

import pytest
import time
import threading
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import collectors with optional dependency handling
try:
    from noise_collector import NoiseCollector
    NOISE_AVAILABLE = True
except ImportError:
    NOISE_AVAILABLE = False
    NoiseCollector = None

try:
    from notification_counter import NotificationCounter
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False
    NotificationCounter = None

try:
    from hrv_collector import HRVCollector
    HRV_AVAILABLE = True
except ImportError:
    HRV_AVAILABLE = False
    HRVCollector = None

try:
    from data_collector_orchestrator import DataCollectorOrchestrator, DataAggregator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    DataCollectorOrchestrator = None
    DataAggregator = None

# Import backend components
import sys
sys.path.insert(0, str(Path(__file__).parent))
from main import app, calculate_fqs
from fastapi.testclient import TestClient


@pytest.mark.skipif(not NOISE_AVAILABLE, reason="Noise collector dependencies not available")
class TestNoiseCollectorIntegration:
    """Test ambient noise collector end-to-end functionality."""
    
    def test_noise_collector_captures_and_normalizes(self):
        """Verify noise collector can capture audio and normalize to 0-10 scale."""
        collector = NoiseCollector()
        
        # Test with simulated audio data
        import numpy as np
        
        # Silent audio
        silent_audio = np.zeros(1024, dtype=np.int16).tobytes()
        rms = collector.calculate_rms(silent_audio)
        noise_level = collector.normalize_noise_level(rms)
        
        assert noise_level == 0.0, "Silent audio should produce noise level 0"
        
        # Loud audio
        loud_audio = np.full(1024, 10000, dtype=np.int16).tobytes()
        rms = collector.calculate_rms(loud_audio)
        noise_level = collector.normalize_noise_level(rms)
        
        assert 0 <= noise_level <= 10.0, f"Noise level {noise_level} should be in range 0-10"
        assert noise_level > 5.0, "Loud audio should produce high noise level"
    
    def test_noise_collector_sends_to_backend(self):
        """Verify noise collector can send data to backend API."""
        client = TestClient(app)
        collector = NoiseCollector(backend_url="http://testserver")
        
        # Mock the requests.post to use TestClient
        with patch('noise_collector.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            success = collector.send_to_backend(noise_level=7.5, hrv=75.0, notifications=2.0)
            
            assert success, "Should successfully send data to backend"
            mock_post.assert_called_once()
            
            # Verify payload structure
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload['ambient_noise'] == 7.5
            assert payload['hrv_rmssd'] == 75.0
            assert payload['notification_count'] == 2.0


@pytest.mark.skipif(not NOTIFICATION_AVAILABLE, reason="Notification counter dependencies not available")
class TestNotificationCounterIntegration:
    """Test notification counter end-to-end functionality."""
    
    def test_notification_counter_tracks_rolling_window(self):
        """Verify notification counter maintains rolling 5-minute window."""
        counter = NotificationCounter()
        
        # Add some notifications
        counter.add_notification("app")
        counter.add_notification("system")
        counter.add_notification("app")
        
        count = counter.get_notification_count()
        assert count == 3, "Should track 3 notifications"
        
        # Test normalization
        normalized = counter.normalize_notification_count(count)
        assert 0 <= normalized <= 5.0, f"Normalized count {normalized} should be in range 0-5"
    
    def test_notification_counter_normalization(self):
        """Verify notification count normalization to 0-5 scale."""
        counter = NotificationCounter()
        
        # Test boundary values
        assert counter.normalize_notification_count(0) == 0.0
        assert counter.normalize_notification_count(20) == 5.0
        assert counter.normalize_notification_count(25) == 5.0  # Clamped
        
        # Test mid-range
        normalized = counter.normalize_notification_count(10)
        assert 2.0 <= normalized <= 3.0, "10 notifications should map to ~2.5"
    
    def test_notification_counter_sends_to_backend(self):
        """Verify notification counter can send data to backend API."""
        counter = NotificationCounter(backend_url="http://testserver")
        
        with patch('notification_counter.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            success = counter.send_to_backend(notification_count=3.5, hrv=70.0, noise=5.0)
            
            assert success, "Should successfully send data to backend"
            
            # Verify payload
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload['notification_count'] == 3.5
            assert payload['hrv_rmssd'] == 70.0
            assert payload['ambient_noise'] == 5.0


@pytest.mark.skipif(not HRV_AVAILABLE, reason="HRV collector dependencies not available")
class TestHRVCollectorIntegration:
    """Test HRV collector end-to-end functionality."""
    
    def test_hrv_collector_fetches_simulated_data(self):
        """Verify HRV collector can fetch simulated data."""
        collector = HRVCollector(api_source="simulated")
        
        hrv = collector.fetch_hrv_data()
        
        assert hrv is not None, "Should fetch HRV data"
        assert 40 <= hrv <= 100, f"HRV {hrv} should be in typical range 40-100"
    
    def test_hrv_collector_caching(self):
        """Verify HRV collector caches data to minimize API calls."""
        collector = HRVCollector(api_source="simulated")
        
        # First fetch
        hrv1 = collector.fetch_hrv_data()
        assert hrv1 is not None
        
        # Second fetch should use cache
        hrv2 = collector.fetch_hrv_data()
        assert hrv2 == hrv1, "Should return cached value"
        
        # Verify cache file exists
        assert collector.cache_file_path.exists(), "Cache file should exist"
        
        # Cleanup
        if collector.cache_file_path.exists():
            collector.cache_file_path.unlink()
    
    def test_hrv_collector_sends_to_backend(self):
        """Verify HRV collector can send data to backend API."""
        collector = HRVCollector(api_source="simulated", backend_url="http://testserver")
        
        with patch('hrv_collector.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            success = collector.send_to_backend(hrv=85.5, notifications=1.0, noise=4.0)
            
            assert success, "Should successfully send data to backend"
            
            # Verify payload
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload['hrv_rmssd'] == 85.5
            assert payload['notification_count'] == 1.0
            assert payload['ambient_noise'] == 4.0
    
    def test_hrv_collector_multi_source_fallback(self):
        """Verify HRV collector falls back through multiple sources."""
        # Create config with multiple sources
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "fitbit": {"access_token": "invalid_token"},
                "oura": {"access_token": "invalid_token"},
                "simulated": {}
            }
            json.dump(config, f)
            config_file = f.name
        
        try:
            collector = HRVCollector(
                sources=["fitbit", "oura", "simulated"],
                config_file=config_file
            )
            
            # Should fall back to simulated
            hrv = collector.fetch_hrv_data()
            assert hrv is not None, "Should fall back to simulated data"
            assert 40 <= hrv <= 100
            
            # Cleanup cache
            if collector.cache_file_path.exists():
                collector.cache_file_path.unlink()
        finally:
            Path(config_file).unlink()


class TestBackendAPIIntegration:
    """Test backend API receives and processes data correctly."""
    
    def test_backend_receives_complete_data(self):
        """Verify backend API accepts complete FocusData payload."""
        client = TestClient(app)
        
        payload = {
            "hrv_rmssd": 75.5,
            "notification_count": 2.5,
            "ambient_noise": 6.0
        }
        
        response = client.post("/data", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data['status'] == 'success'
    
    def test_backend_validates_data_types(self):
        """Verify backend validates data types correctly."""
        client = TestClient(app)
        
        # Invalid payload (string instead of float)
        invalid_payload = {
            "hrv_rmssd": "not_a_number",
            "notification_count": 2.5,
            "ambient_noise": 6.0
        }
        
        response = client.post("/data", json=invalid_payload)
        assert response.status_code == 422, "Should reject invalid data types"
    
    def test_fqs_calculation_with_real_data(self):
        """Verify FQS calculation produces correct results with realistic data."""
        # Optimal conditions
        fqs_optimal = calculate_fqs(hrv=90.0, notifications=0.0, noise_level=2.0)
        assert 80 <= fqs_optimal <= 100, f"Optimal FQS {fqs_optimal} should be high"
        
        # Poor conditions
        fqs_poor = calculate_fqs(hrv=45.0, notifications=5.0, noise_level=10.0)
        assert 0 <= fqs_poor <= 30, f"Poor FQS {fqs_poor} should be low"
        
        # Medium conditions
        fqs_medium = calculate_fqs(hrv=70.0, notifications=2.5, noise_level=5.0)
        assert 40 <= fqs_medium <= 70, f"Medium FQS {fqs_medium} should be mid-range"
    
    def test_fqs_calculation_accuracy(self):
        """Verify FQS calculation matches expected formula."""
        # Test case: HRV=80, Notifications=2, Noise=4
        hrv = 80.0
        notifications = 2.0
        noise = 4.0
        
        fqs = calculate_fqs(hrv, notifications, noise)
        
        # Manual calculation based on actual formula
        # HRV component: ((80 - 40) / 60) * 50 = (40/60) * 50 = 33.33
        # Notification component: (1 - 2/5) * 30 = 0.6 * 30 = 18
        # Noise component: (1 - 4/10) * 20 = 0.6 * 20 = 12
        # Total: 33.33 + 18 + 12 = 63.33
        expected_fqs = 63.33
        
        assert abs(fqs - expected_fqs) < 0.1, f"FQS {fqs} should be close to {expected_fqs}"


@pytest.mark.skipif(not ORCHESTRATOR_AVAILABLE, reason="Orchestrator dependencies not available")
class TestDataAggregatorIntegration:
    """Test data aggregator combines data from multiple sources."""
    
    def test_aggregator_combines_all_sources(self):
        """Verify aggregator correctly combines data from all collectors."""
        aggregator = DataAggregator()
        
        # Update from different sources
        aggregator.update_hrv(85.0)
        aggregator.update_notifications(3.0)
        aggregator.update_noise(7.5)
        
        # Get aggregated data
        data = aggregator.get_aggregated_data()
        
        assert data['hrv_rmssd'] == 85.0
        assert data['notification_count'] == 3.0
        assert data['ambient_noise'] == 7.5
    
    def test_aggregator_thread_safety(self):
        """Verify aggregator is thread-safe for concurrent updates."""
        aggregator = DataAggregator()
        
        def update_hrv():
            for i in range(100):
                aggregator.update_hrv(float(i))
        
        def update_notifications():
            for i in range(100):
                aggregator.update_notifications(float(i))
        
        # Run updates concurrently
        t1 = threading.Thread(target=update_hrv)
        t2 = threading.Thread(target=update_notifications)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # Should not crash and should have valid data
        data = aggregator.get_aggregated_data()
        assert 0 <= data['hrv_rmssd'] <= 100
        assert 0 <= data['notification_count'] <= 100
    
    def test_aggregator_status_tracking(self):
        """Verify aggregator tracks status of each collector."""
        aggregator = DataAggregator()
        
        # Initially not started
        status = aggregator.get_status()
        assert status['hrv']['status'] == 'not_started'
        
        # After update, should be active
        aggregator.update_hrv(75.0)
        status = aggregator.get_status()
        assert status['hrv']['status'] == 'active'
        assert status['hrv']['value'] == 75.0
        assert status['hrv']['last_update'] is not None
        
        # Mark as failed
        aggregator.mark_collector_failed('hrv')
        status = aggregator.get_status()
        assert status['hrv']['status'] == 'failed'


@pytest.mark.skipif(not ORCHESTRATOR_AVAILABLE, reason="Orchestrator dependencies not available")
class TestGracefulDegradation:
    """Test system handles collector failures gracefully."""
    
    def test_orchestrator_continues_with_partial_data(self):
        """Verify orchestrator continues working when one collector fails."""
        # Create config with only simulated HRV enabled
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "backend_url": "http://localhost:8000",
                "send_interval": 1,
                "collectors": {
                    "hrv": {"enabled": True, "source": "simulated", "interval": 1},
                    "notifications": {"enabled": False},
                    "noise": {"enabled": False}
                },
                "graceful_degradation": True
            }
            json.dump(config, f)
            config_file = f.name
        
        try:
            orchestrator = DataCollectorOrchestrator(config_file=config_file)
            
            # Aggregator should have default values for disabled collectors
            data = orchestrator.aggregator.get_aggregated_data()
            assert data['hrv_rmssd'] == 70.0  # Default
            assert data['notification_count'] == 0.0  # Default
            assert data['ambient_noise'] == 5.0  # Default
        finally:
            Path(config_file).unlink()
    
    @pytest.mark.skipif(not ORCHESTRATOR_AVAILABLE, reason="Orchestrator dependencies not available")
    def test_aggregator_uses_defaults_for_failed_collectors(self):
        """Verify aggregator uses default values when collectors fail."""
        aggregator = DataAggregator()
        
        # Mark HRV as failed
        aggregator.mark_collector_failed('hrv')
        
        # Should still return default value
        data = aggregator.get_aggregated_data()
        assert data['hrv_rmssd'] == 70.0  # Default neutral value
    
    def test_backend_accepts_partial_data(self):
        """Verify backend accepts data even if some values are defaults."""
        client = TestClient(app)
        
        # Payload with default values (simulating failed collectors)
        payload = {
            "hrv_rmssd": 70.0,  # Default
            "notification_count": 0.0,  # Default
            "ambient_noise": 5.0  # Default
        }
        
        response = client.post("/data", json=payload)
        assert response.status_code == 200
        
        # FQS should still be calculated
        fqs = calculate_fqs(70.0, 0.0, 5.0)
        assert 0 <= fqs <= 100


class TestEndToEndFlow:
    """Test complete end-to-end flow from collectors to backend."""
    
    @pytest.mark.skipif(not ORCHESTRATOR_AVAILABLE, reason="Orchestrator dependencies not available")
    def test_complete_data_flow(self):
        """Verify complete flow: collectors -> aggregator -> backend."""
        client = TestClient(app)
        aggregator = DataAggregator()
        
        # Simulate collector updates
        aggregator.update_hrv(82.5)
        aggregator.update_notifications(1.5)
        aggregator.update_noise(4.2)
        
        # Get aggregated data
        data = aggregator.get_aggregated_data()
        
        # Send to backend
        response = client.post("/data", json=data)
        assert response.status_code == 200
        
        # Verify FQS calculation
        fqs = calculate_fqs(
            data['hrv_rmssd'],
            data['notification_count'],
            data['ambient_noise']
        )
        assert 0 <= fqs <= 100
        assert fqs > 50, "Good conditions should produce FQS > 50"
    
    def test_realistic_scenario_high_focus(self):
        """Test realistic scenario: user in high focus state."""
        client = TestClient(app)
        
        # High focus: good HRV, no notifications, quiet environment
        payload = {
            "hrv_rmssd": 88.0,
            "notification_count": 0.0,
            "ambient_noise": 2.5
        }
        
        response = client.post("/data", json=payload)
        assert response.status_code == 200
        
        fqs = calculate_fqs(88.0, 0.0, 2.5)
        assert fqs >= 75, f"High focus should produce FQS >= 75, got {fqs}"
    
    def test_realistic_scenario_interrupted_focus(self):
        """Test realistic scenario: user experiencing interruptions."""
        client = TestClient(app)
        
        # Interrupted: moderate HRV, many notifications, noisy environment
        payload = {
            "hrv_rmssd": 65.0,
            "notification_count": 4.5,
            "ambient_noise": 8.0
        }
        
        response = client.post("/data", json=payload)
        assert response.status_code == 200
        
        fqs = calculate_fqs(65.0, 4.5, 8.0)
        assert fqs <= 40, f"Interrupted focus should produce FQS <= 40, got {fqs}"
    
    def test_realistic_scenario_recovering_focus(self):
        """Test realistic scenario: user recovering focus after interruption."""
        client = TestClient(app)
        
        # Recovering: improving HRV, fewer notifications, quieter
        payload = {
            "hrv_rmssd": 75.0,
            "notification_count": 1.0,
            "ambient_noise": 4.0
        }
        
        response = client.post("/data", json=payload)
        assert response.status_code == 200
        
        fqs = calculate_fqs(75.0, 1.0, 4.0)
        assert 50 <= fqs <= 75, f"Recovering focus should produce FQS 50-75, got {fqs}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
