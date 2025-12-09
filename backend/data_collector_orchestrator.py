"""
Unified Real Data Collector Orchestrator
Runs all data collectors (HRV, notifications, noise) concurrently and aggregates data.

This script:
1. Runs all data collectors concurrently using threading
2. Aggregates data from all three sources (HRV, notifications, noise)
3. Sends combined data payload to backend /data endpoint
4. Implements graceful degradation if one collector fails
5. Provides logging for debugging collector issues
6. Supports configuration file for collector settings

Requirements: 1.1, 2.1
"""

import threading
import time
import requests
import argparse
import json
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from collections import deque

# Import collector classes
try:
    from hrv_collector import HRVCollector
    HRV_AVAILABLE = True
except ImportError:
    HRV_AVAILABLE = False
    logging.warning("HRV collector not available")

try:
    from noise_collector import NoiseCollector
    NOISE_AVAILABLE = True
except ImportError:
    NOISE_AVAILABLE = False
    logging.warning("Noise collector not available")

try:
    from notification_counter import NotificationCounter
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False
    logging.warning("Notification counter not available")


class DataAggregator:
    """Aggregates data from multiple collectors and manages shared state."""
    
    def __init__(self):
        """Initialize the data aggregator with default values."""
        self.hrv_value: float = 70.0  # Default neutral HRV
        self.notification_count: float = 0.0  # Default no notifications
        self.noise_level: float = 5.0  # Default neutral noise
        
        # Timestamps for each data source
        self.hrv_timestamp: Optional[datetime] = None
        self.notification_timestamp: Optional[datetime] = None
        self.noise_timestamp: Optional[datetime] = None
        
        # Thread locks for thread-safe access
        self.hrv_lock = threading.Lock()
        self.notification_lock = threading.Lock()
        self.noise_lock = threading.Lock()
        
        # Status tracking
        self.hrv_status: str = "not_started"
        self.notification_status: str = "not_started"
        self.noise_status: str = "not_started"
    
    def update_hrv(self, value: float):
        """Update HRV value in a thread-safe manner."""
        with self.hrv_lock:
            self.hrv_value = value
            self.hrv_timestamp = datetime.now()
            self.hrv_status = "active"
    
    def update_notifications(self, value: float):
        """Update notification count in a thread-safe manner."""
        with self.notification_lock:
            self.notification_count = value
            self.notification_timestamp = datetime.now()
            self.notification_status = "active"
    
    def update_noise(self, value: float):
        """Update noise level in a thread-safe manner."""
        with self.noise_lock:
            self.noise_level = value
            self.noise_timestamp = datetime.now()
            self.noise_status = "active"
    
    def get_aggregated_data(self) -> Dict[str, float]:
        """
        Get current aggregated data from all sources.
        
        Returns:
            Dict with hrv_rmssd, notification_count, and ambient_noise
        """
        with self.hrv_lock, self.notification_lock, self.noise_lock:
            return {
                "hrv_rmssd": self.hrv_value,
                "notification_count": self.notification_count,
                "ambient_noise": self.noise_level
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all collectors."""
        return {
            "hrv": {
                "status": self.hrv_status,
                "value": self.hrv_value,
                "last_update": self.hrv_timestamp.isoformat() if self.hrv_timestamp else None
            },
            "notifications": {
                "status": self.notification_status,
                "value": self.notification_count,
                "last_update": self.notification_timestamp.isoformat() if self.notification_timestamp else None
            },
            "noise": {
                "status": self.noise_status,
                "value": self.noise_level,
                "last_update": self.noise_timestamp.isoformat() if self.noise_timestamp else None
            }
        }
    
    def mark_collector_failed(self, collector_name: str):
        """Mark a collector as failed."""
        if collector_name == "hrv":
            self.hrv_status = "failed"
        elif collector_name == "notifications":
            self.notification_status = "failed"
        elif collector_name == "noise":
            self.noise_status = "failed"


class DataCollectorOrchestrator:
    """Orchestrates multiple data collectors and sends aggregated data to backend."""
    
    def __init__(self, config_file: str = "collector_config.json",
                 backend_url: str = "http://localhost:8000"):
        """
        Initialize the orchestrator.
        
        Args:
            config_file: Path to configuration file
            backend_url: URL of the backend API
        """
        self.config_file = config_file
        self.backend_url = backend_url.rstrip('/')
        self.config: Dict[str, Any] = {}
        self.aggregator = DataAggregator()
        
        # Collector threads
        self.threads: list = []
        self.stop_event = threading.Event()
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.load_config()
    
    def setup_logging(self):
        """Configure logging for the orchestrator."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        log_level = logging.INFO
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging to both file and console
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_dir / "collector_orchestrator.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger("Orchestrator")
    
    def load_config(self):
        """Load configuration from JSON file."""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Loaded configuration from {self.config_file}")
            else:
                self.logger.warning(f"Configuration file not found: {self.config_file}")
                self.logger.info("Using default configuration")
                self.config = self.get_default_config()
                self.save_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            self.logger.info("Using default configuration")
            self.config = self.get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "backend_url": "http://localhost:8000",
            "send_interval": 5,
            "collectors": {
                "hrv": {
                    "enabled": True,
                    "source": "simulated",
                    "sources": ["simulated"],
                    "interval": 60,
                    "config_file": "hrv_config.json"
                },
                "notifications": {
                    "enabled": True,
                    "interval": 5,
                    "simulate": True,
                    "filter_system": False,
                    "filter_app": False
                },
                "noise": {
                    "enabled": True,
                    "interval": 5,
                    "device_index": None
                }
            },
            "graceful_degradation": True,
            "log_level": "INFO"
        }
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def run_hrv_collector(self):
        """Run HRV collector in a separate thread."""
        if not HRV_AVAILABLE:
            self.logger.error("HRV collector not available")
            self.aggregator.mark_collector_failed("hrv")
            return
        
        try:
            hrv_config = self.config.get("collectors", {}).get("hrv", {})
            
            if not hrv_config.get("enabled", True):
                self.logger.info("HRV collector disabled in configuration")
                return
            
            self.logger.info("Starting HRV collector...")
            
            # Create HRV collector instance
            collector = HRVCollector(
                backend_url=self.backend_url,
                interval=hrv_config.get("interval", 60),
                api_source=hrv_config.get("source", "simulated"),
                config_file=hrv_config.get("config_file"),
                sources=hrv_config.get("sources")
            )
            
            # Run collector loop
            while not self.stop_event.is_set():
                try:
                    hrv = collector.fetch_hrv_data()
                    if hrv is not None:
                        self.aggregator.update_hrv(hrv)
                        self.logger.debug(f"HRV updated: {hrv:.1f}")
                    else:
                        self.logger.warning("Failed to fetch HRV data")
                    
                    # Wait for next interval
                    self.stop_event.wait(timeout=collector.interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in HRV collector loop: {e}")
                    if not self.config.get("graceful_degradation", True):
                        raise
                    time.sleep(5)  # Wait before retrying
            
        except Exception as e:
            self.logger.error(f"HRV collector failed: {e}")
            self.aggregator.mark_collector_failed("hrv")
            if not self.config.get("graceful_degradation", True):
                raise
    
    def run_notification_counter(self):
        """Run notification counter in a separate thread."""
        if not NOTIFICATION_AVAILABLE:
            self.logger.error("Notification counter not available")
            self.aggregator.mark_collector_failed("notifications")
            return
        
        try:
            notif_config = self.config.get("collectors", {}).get("notifications", {})
            
            if not notif_config.get("enabled", True):
                self.logger.info("Notification counter disabled in configuration")
                return
            
            self.logger.info("Starting notification counter...")
            
            # Create notification counter instance
            counter = NotificationCounter(
                backend_url=self.backend_url,
                interval=notif_config.get("interval", 5),
                filter_system=notif_config.get("filter_system", False),
                filter_app=notif_config.get("filter_app", False)
            )
            
            # Start monitoring in background
            simulate = notif_config.get("simulate", False)
            if simulate or not counter.check_windows_api():
                monitor_thread = threading.Thread(
                    target=counter.simulate_notifications,
                    daemon=True
                )
            else:
                monitor_thread = threading.Thread(
                    target=counter.monitor_notifications_polling,
                    daemon=True
                )
            monitor_thread.start()
            
            # Update aggregator loop
            while not self.stop_event.is_set():
                try:
                    raw_count = counter.get_notification_count()
                    normalized_count = counter.normalize_notification_count(raw_count)
                    self.aggregator.update_notifications(normalized_count)
                    self.logger.debug(f"Notifications updated: {normalized_count:.2f}")
                    
                    # Wait for next interval
                    self.stop_event.wait(timeout=counter.interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in notification counter loop: {e}")
                    if not self.config.get("graceful_degradation", True):
                        raise
                    time.sleep(5)  # Wait before retrying
            
        except Exception as e:
            self.logger.error(f"Notification counter failed: {e}")
            self.aggregator.mark_collector_failed("notifications")
            if not self.config.get("graceful_degradation", True):
                raise
    
    def run_noise_collector(self):
        """Run noise collector in a separate thread."""
        if not NOISE_AVAILABLE:
            self.logger.error("Noise collector not available")
            self.aggregator.mark_collector_failed("noise")
            return
        
        try:
            noise_config = self.config.get("collectors", {}).get("noise", {})
            
            if not noise_config.get("enabled", True):
                self.logger.info("Noise collector disabled in configuration")
                return
            
            self.logger.info("Starting noise collector...")
            
            # Create noise collector instance
            collector = NoiseCollector(
                backend_url=self.backend_url,
                device_index=noise_config.get("device_index"),
                interval=noise_config.get("interval", 5)
            )
            
            # Initialize audio
            if not collector.initialize_audio():
                self.logger.error("Failed to initialize audio for noise collector")
                self.aggregator.mark_collector_failed("noise")
                return
            
            # Run collector loop
            while not self.stop_event.is_set():
                try:
                    noise_level = collector.capture_noise_sample()
                    if noise_level is not None:
                        self.aggregator.update_noise(noise_level)
                        self.logger.debug(f"Noise updated: {noise_level:.2f}")
                    else:
                        self.logger.warning("Failed to capture noise sample")
                    
                    # Wait for next interval
                    self.stop_event.wait(timeout=collector.interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in noise collector loop: {e}")
                    if not self.config.get("graceful_degradation", True):
                        raise
                    time.sleep(5)  # Wait before retrying
            
            # Cleanup
            collector.cleanup()
            
        except Exception as e:
            self.logger.error(f"Noise collector failed: {e}")
            self.aggregator.mark_collector_failed("noise")
            if not self.config.get("graceful_degradation", True):
                raise
    
    def send_aggregated_data(self) -> bool:
        """
        Send aggregated data to backend API.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = self.aggregator.get_aggregated_data()
            
            response = requests.post(
                f"{self.backend_url}/data",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"Backend returned status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Cannot connect to backend at {self.backend_url}")
            return False
        except requests.exceptions.Timeout:
            self.logger.error("Request to backend timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error sending data to backend: {e}")
            return False
    
    def run(self):
        """Main orchestrator loop."""
        self.logger.info("=" * 60)
        self.logger.info("Data Collector Orchestrator Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"Backend URL: {self.backend_url}")
        self.logger.info(f"Send interval: {self.config.get('send_interval', 5)} seconds")
        self.logger.info(f"Graceful degradation: {self.config.get('graceful_degradation', True)}")
        
        # Start collector threads
        collectors_config = self.config.get("collectors", {})
        
        if collectors_config.get("hrv", {}).get("enabled", True):
            hrv_thread = threading.Thread(target=self.run_hrv_collector, daemon=True)
            hrv_thread.start()
            self.threads.append(("HRV", hrv_thread))
        
        if collectors_config.get("notifications", {}).get("enabled", True):
            notif_thread = threading.Thread(target=self.run_notification_counter, daemon=True)
            notif_thread.start()
            self.threads.append(("Notifications", notif_thread))
        
        if collectors_config.get("noise", {}).get("enabled", True):
            noise_thread = threading.Thread(target=self.run_noise_collector, daemon=True)
            noise_thread.start()
            self.threads.append(("Noise", noise_thread))
        
        if not self.threads:
            self.logger.error("No collectors enabled!")
            return
        
        self.logger.info(f"Started {len(self.threads)} collector threads")
        self.logger.info("Press Ctrl+C to stop\n")
        
        # Give collectors time to initialize
        time.sleep(2)
        
        # Main loop: send aggregated data at regular intervals
        send_interval = self.config.get("send_interval", 5)
        
        try:
            while not self.stop_event.is_set():
                # Get aggregated data
                data = self.aggregator.get_aggregated_data()
                
                # Log current values
                self.logger.info(
                    f"HRV: {data['hrv_rmssd']:.1f} | "
                    f"Notifications: {data['notification_count']:.2f} | "
                    f"Noise: {data['ambient_noise']:.2f}"
                )
                
                # Send to backend
                success = self.send_aggregated_data()
                
                if success:
                    self.logger.info("✓ Data sent to backend")
                else:
                    self.logger.warning("✗ Failed to send data to backend")
                
                # Wait for next interval
                self.stop_event.wait(timeout=send_interval)
                
        except KeyboardInterrupt:
            self.logger.info("\n\nStopping orchestrator...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop all collector threads."""
        self.logger.info("Stopping all collectors...")
        self.stop_event.set()
        
        # Wait for threads to finish (with timeout)
        for name, thread in self.threads:
            thread.join(timeout=2)
            if thread.is_alive():
                self.logger.warning(f"{name} thread did not stop gracefully")
            else:
                self.logger.info(f"{name} collector stopped")
        
        self.logger.info("Orchestrator stopped")
    
    def print_status(self):
        """Print status of all collectors."""
        status = self.aggregator.get_status()
        
        print("\n" + "=" * 60)
        print("Collector Status")
        print("=" * 60)
        
        for collector_name, collector_status in status.items():
            print(f"\n{collector_name.upper()}:")
            print(f"  Status: {collector_status['status']}")
            print(f"  Value: {collector_status['value']}")
            print(f"  Last Update: {collector_status['last_update'] or 'Never'}")
        
        print("\n" + "=" * 60)


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Data Collector Orchestrator - Runs all collectors and aggregates data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  python data_collector_orchestrator.py
  
  # Run with custom configuration file
  python data_collector_orchestrator.py --config my_config.json
  
  # Run with custom backend URL
  python data_collector_orchestrator.py --backend-url http://192.168.1.100:8000
  
  # Generate default configuration file
  python data_collector_orchestrator.py --generate-config
  
  # Print collector status
  python data_collector_orchestrator.py --status

Configuration File Format (JSON):
  See collector_config.example.json for a complete example.
        """
    )
    parser.add_argument(
        "--config",
        default="collector_config.json",
        help="Path to configuration file (default: collector_config.json)"
    )
    parser.add_argument(
        "--backend-url",
        help="Backend API URL (overrides config file)"
    )
    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="Generate default configuration file and exit"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print collector status and exit"
    )
    
    args = parser.parse_args()
    
    # Generate config if requested
    if args.generate_config:
        orchestrator = DataCollectorOrchestrator(config_file=args.config)
        orchestrator.save_config()
        print(f"Generated default configuration: {args.config}")
        return
    
    # Create orchestrator
    backend_url = args.backend_url or "http://localhost:8000"
    orchestrator = DataCollectorOrchestrator(
        config_file=args.config,
        backend_url=backend_url
    )
    
    # Print status if requested
    if args.status:
        orchestrator.print_status()
        return
    
    # Run orchestrator
    orchestrator.run()


if __name__ == "__main__":
    main()
