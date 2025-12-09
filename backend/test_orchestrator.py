"""
Quick test for the data collector orchestrator.
Tests initialization, configuration, and data aggregation.
"""

import unittest
import json
import os
from pathlib import Path
from data_collector_orchestrator import DataCollectorOrchestrator, DataAggregator


class TestDataAggregator(unittest.TestCase):
    """Test the DataAggregator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.aggregator = DataAggregator()
    
    def test_initialization(self):
        """Test that aggregator initializes with default values."""
        self.assertEqual(self.aggregator.hrv_value, 70.0)
        self.assertEqual(self.aggregator.notification_count, 0.0)
        self.assertEqual(self.aggregator.noise_level, 5.0)
        self.assertIsNone(self.aggregator.hrv_timestamp)
        self.assertIsNone(self.aggregator.notification_timestamp)
        self.assertIsNone(self.aggregator.noise_timestamp)
    
    def test_update_hrv(self):
        """Test updating HRV value."""
        self.aggregator.update_hrv(85.5)
        self.assertEqual(self.aggregator.hrv_value, 85.5)
        self.assertIsNotNone(self.aggregator.hrv_timestamp)
        self.assertEqual(self.aggregator.hrv_status, "active")
    
    def test_update_notifications(self):
        """Test updating notification count."""
        self.aggregator.update_notifications(3.5)
        self.assertEqual(self.aggregator.notification_count, 3.5)
        self.assertIsNotNone(self.aggregator.notification_timestamp)
        self.assertEqual(self.aggregator.notification_status, "active")
    
    def test_update_noise(self):
        """Test updating noise level."""
        self.aggregator.update_noise(7.2)
        self.assertEqual(self.aggregator.noise_level, 7.2)
        self.assertIsNotNone(self.aggregator.noise_timestamp)
        self.assertEqual(self.aggregator.noise_status, "active")
    
    def test_get_aggregated_data(self):
        """Test getting aggregated data."""
        self.aggregator.update_hrv(80.0)
        self.aggregator.update_notifications(2.0)
        self.aggregator.update_noise(4.0)
        
        data = self.aggregator.get_aggregated_data()
        
        self.assertEqual(data["hrv_rmssd"], 80.0)
        self.assertEqual(data["notification_count"], 2.0)
        self.assertEqual(data["ambient_noise"], 4.0)
    
    def test_get_status(self):
        """Test getting collector status."""
        self.aggregator.update_hrv(75.0)
        
        status = self.aggregator.get_status()
        
        self.assertIn("hrv", status)
        self.assertIn("notifications", status)
        self.assertIn("noise", status)
        self.assertEqual(status["hrv"]["status"], "active")
        self.assertEqual(status["hrv"]["value"], 75.0)
    
    def test_mark_collector_failed(self):
        """Test marking a collector as failed."""
        self.aggregator.mark_collector_failed("hrv")
        self.assertEqual(self.aggregator.hrv_status, "failed")
        
        self.aggregator.mark_collector_failed("notifications")
        self.assertEqual(self.aggregator.notification_status, "failed")
        
        self.aggregator.mark_collector_failed("noise")
        self.assertEqual(self.aggregator.noise_status, "failed")


class TestDataCollectorOrchestrator(unittest.TestCase):
    """Test the DataCollectorOrchestrator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config_file = "test_collector_config.json"
        
        # Clean up any existing test config
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        
        # Clean up logs directory if empty
        log_dir = Path("logs")
        if log_dir.exists() and not any(log_dir.iterdir()):
            log_dir.rmdir()
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = DataCollectorOrchestrator(
            config_file=self.test_config_file,
            backend_url="http://localhost:8000"
        )
        
        self.assertEqual(orchestrator.backend_url, "http://localhost:8000")
        self.assertIsNotNone(orchestrator.aggregator)
        self.assertIsNotNone(orchestrator.config)
    
    def test_default_config(self):
        """Test default configuration generation."""
        orchestrator = DataCollectorOrchestrator(
            config_file=self.test_config_file,
            backend_url="http://localhost:8000"
        )
        
        config = orchestrator.get_default_config()
        
        self.assertIn("backend_url", config)
        self.assertIn("send_interval", config)
        self.assertIn("collectors", config)
        self.assertIn("hrv", config["collectors"])
        self.assertIn("notifications", config["collectors"])
        self.assertIn("noise", config["collectors"])
    
    def test_config_save_and_load(self):
        """Test saving and loading configuration."""
        orchestrator = DataCollectorOrchestrator(
            config_file=self.test_config_file,
            backend_url="http://localhost:8000"
        )
        
        # Save config
        orchestrator.save_config()
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.test_config_file))
        
        # Load config
        with open(self.test_config_file, 'r') as f:
            loaded_config = json.load(f)
        
        self.assertEqual(loaded_config["backend_url"], "http://localhost:8000")
        self.assertIn("collectors", loaded_config)
    
    def test_aggregator_integration(self):
        """Test that orchestrator has a working aggregator."""
        orchestrator = DataCollectorOrchestrator(
            config_file=self.test_config_file,
            backend_url="http://localhost:8000"
        )
        
        # Update aggregator values
        orchestrator.aggregator.update_hrv(90.0)
        orchestrator.aggregator.update_notifications(1.5)
        orchestrator.aggregator.update_noise(3.0)
        
        # Get aggregated data
        data = orchestrator.aggregator.get_aggregated_data()
        
        self.assertEqual(data["hrv_rmssd"], 90.0)
        self.assertEqual(data["notification_count"], 1.5)
        self.assertEqual(data["ambient_noise"], 3.0)


if __name__ == "__main__":
    unittest.main()
