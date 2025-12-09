"""
HRV Data Collector with Fitness Tracker Integration
Fetches HRV (RMSSD) data from fitness tracker APIs and sends to the backend API.

This script:
1. Authenticates with chosen fitness API (Fitbit, Garmin, Oura, Apple HealthKit, etc.)
2. Fetches latest HRV (RMSSD) data from API using adapter pattern
3. Handles API rate limits and authentication token refresh
4. Caches HRV data locally to minimize API calls
5. Sends HRV data to backend /data endpoint when new data is available
6. Falls back to simulated data if API is unavailable

Supported APIs (via adapter pattern):
- Fitbit API (requires OAuth 2.0 setup)
- Garmin Connect API (requires OAuth 1.0 setup)
- Oura Ring API (requires Personal Access Token)
- Apple HealthKit (requires macOS/iOS)
- Simulated data (for testing)

Requirements: 1.1, 3.3
"""

import time
import requests
import argparse
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from hrv_adapters import HRVAdapter, AdapterFactory


class HRVCollector:
    """Collects HRV data from fitness tracker APIs and sends to backend API using adapter pattern."""
    
    # Cache configuration
    CACHE_FILE = "hrv_cache.json"
    CACHE_DURATION = 300  # 5 minutes - minimum time between API calls
    
    def __init__(self, backend_url: str = "http://localhost:8000",
                 interval: int = 60,
                 api_source: str = "simulated",
                 config_file: Optional[str] = None,
                 sources: Optional[list] = None):
        """
        Initialize the HRV collector.
        
        Args:
            backend_url: URL of the backend API
            interval: Interval in seconds between sending data to backend
            api_source: Primary data source ("fitbit", "garmin", "oura", "apple_healthkit", "simulated")
            config_file: Path to API configuration file (JSON)
            sources: List of data sources in priority order (overrides api_source if provided)
        """
        self.backend_url = backend_url.rstrip('/')
        self.interval = interval
        self.config_file = config_file
        
        # API configuration
        self.api_config: Dict[str, Any] = {}
        
        # Support for multiple sources with priority order
        if sources:
            self.sources = [s.lower() for s in sources]
            self.api_source = self.sources[0]  # Primary source
        else:
            self.api_source = api_source.lower()
            self.sources = [self.api_source]
        
        # HRV adapters (multiple adapters for fallback support)
        self.adapters: list = []
        self.adapter: Optional[HRVAdapter] = None  # Primary adapter
        
        # Cache for HRV data
        self.cache_file_path = Path(self.CACHE_FILE)
        self.cached_hrv: Optional[float] = None
        self.cache_timestamp: Optional[datetime] = None
        self.cache_source: Optional[str] = None
        
        # Load configuration and initialize adapters
        if self.config_file:
            self.load_config()
        
        self._initialize_adapters()
    
    def load_config(self):
        """Load API configuration from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                self.api_config = json.load(f)
            print(f"Loaded configuration from {self.config_file}")
        except FileNotFoundError:
            print(f"Warning: Configuration file not found: {self.config_file}")
            print("Falling back to simulated data")
            self.api_source = "simulated"
            self.sources = ["simulated"]
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in configuration file: {e}")
            print("Falling back to simulated data")
            self.api_source = "simulated"
            self.sources = ["simulated"]
    
    def _initialize_adapters(self):
        """Initialize HRV adapters for all configured sources."""
        self.adapters = []
        
        for source in self.sources:
            try:
                # Get configuration for this source
                source_config = self.api_config.get(source, {})
                
                # Create adapter using factory
                adapter = AdapterFactory.create_adapter(source, source_config)
                self.adapters.append(adapter)
                
                print(f"Initialized {adapter.get_source_name()} adapter")
                
            except ValueError as e:
                print(f"Warning: Could not initialize {source} adapter: {e}")
                continue
        
        # If no adapters were initialized, fall back to simulated
        if not self.adapters:
            print("No adapters initialized, falling back to simulated data")
            self.adapters.append(AdapterFactory.create_adapter("simulated", {}))
            self.sources = ["simulated"]
        
        # Set primary adapter
        self.adapter = self.adapters[0]
        self.api_source = self.sources[0]
    
    def load_cache(self) -> bool:
        """
        Load cached HRV data from file.
        
        Returns:
            bool: True if valid cache was loaded, False otherwise
        """
        try:
            if not self.cache_file_path.exists():
                return False
            
            with open(self.cache_file_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            age = (datetime.now() - cache_time).total_seconds()
            
            if age < self.CACHE_DURATION:
                self.cached_hrv = cache_data['hrv']
                self.cache_timestamp = cache_time
                print(f"Loaded cached HRV: {self.cached_hrv:.1f} (age: {age:.0f}s)")
                return True
            else:
                print(f"Cache expired (age: {age:.0f}s)")
                return False
                
        except Exception as e:
            print(f"Error loading cache: {e}")
            return False
    
    def save_cache(self, hrv: float, source: str = None):
        """
        Save HRV data to cache file.
        
        Args:
            hrv: HRV value to cache
            source: Source name that provided the data
        """
        try:
            cache_data = {
                'hrv': hrv,
                'timestamp': datetime.now().isoformat(),
                'source': source or self.api_source
            }
            
            with open(self.cache_file_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            self.cached_hrv = hrv
            self.cache_timestamp = datetime.now()
            self.cache_source = source or self.api_source
            
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def should_fetch_new_data(self) -> bool:
        """
        Determine if new data should be fetched from API.
        
        Returns:
            bool: True if new data should be fetched, False if cache is valid
        """
        if self.cache_timestamp is None:
            return True
        
        age = (datetime.now() - self.cache_timestamp).total_seconds()
        return age >= self.CACHE_DURATION


    
    def fetch_hrv_data(self) -> Optional[float]:
        """
        Fetch HRV data from configured sources using adapter pattern with fallback.
        Tries each source in priority order until one succeeds.
        
        Returns:
            Optional[float]: HRV value (RMSSD) or None if all sources fail
        """
        # Check if we should use cached data
        if not self.should_fetch_new_data():
            source_name = self.cache_source or self.api_source
            print(f"Using cached HRV: {self.cached_hrv:.1f} (from {source_name})")
            return self.cached_hrv
        
        # Try each adapter in priority order
        for i, adapter in enumerate(self.adapters):
            source_name = self.sources[i] if i < len(self.sources) else "unknown"
            print(f"Fetching HRV data from {adapter.get_source_name()}...")
            
            hrv = adapter.fetch_hrv()
            
            if hrv is not None:
                # Success! Cache and return
                self.save_cache(hrv, source_name)
                return hrv
            else:
                print(f"  ✗ {adapter.get_source_name()} failed")
                # Try next adapter in the list
        
        # All adapters failed
        print("✗ All HRV sources failed")
        
        # Last resort: try simulated if not already in the list
        if "simulated" not in self.sources:
            print("Falling back to simulated data as last resort")
            fallback_adapter = AdapterFactory.create_adapter("simulated", {})
            hrv = fallback_adapter.fetch_hrv()
            if hrv is not None:
                self.save_cache(hrv, "simulated")
            return hrv
        
        return None
    
    def send_to_backend(self, hrv: float, notifications: float = 0.0,
                       noise: float = 5.0) -> bool:
        """
        Send HRV data to backend API.
        
        Args:
            hrv: HRV value (RMSSD)
            notifications: Notification count (default: 0.0)
            noise: Noise level (default: 5.0 - neutral value)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payload = {
                "hrv_rmssd": hrv,
                "notification_count": notifications,
                "ambient_noise": noise
            }
            
            response = requests.post(
                f"{self.backend_url}/data",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"Backend returned status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"Error: Cannot connect to backend at {self.backend_url}")
            print("Make sure the backend server is running")
            return False
        except requests.exceptions.Timeout:
            print("Error: Request to backend timed out")
            return False
        except Exception as e:
            print(f"Error sending data to backend: {e}")
            return False
    
    def run(self):
        """Main loop: fetch HRV data and send to backend at regular intervals."""
        print(f"\nHRV Data Collector")
        print(f"==================")
        
        if len(self.sources) > 1:
            print(f"Data sources (priority order): {', '.join(self.sources)}")
            print(f"Primary source: {self.api_source}")
        else:
            print(f"Data source: {self.api_source}")
        
        print(f"Backend URL: {self.backend_url}/data")
        print(f"Interval: {self.interval} seconds")
        print(f"Cache duration: {self.CACHE_DURATION} seconds")
        
        if self.api_source == "simulated":
            print("\n⚠️  Running in SIMULATION mode")
            print("For real HRV data, configure a fitness tracker API")
        
        print("\nPress Ctrl+C to stop\n")
        
        # Try to load cached data
        self.load_cache()
        
        try:
            while True:
                # Fetch HRV data
                hrv = self.fetch_hrv_data()
                
                if hrv is not None:
                    print(f"HRV: {hrv:.1f} ms ", end="")
                    
                    # Send to backend
                    success = self.send_to_backend(hrv)
                    
                    if success:
                        print("✓ Sent to backend")
                    else:
                        print("✗ Failed to send")
                else:
                    print("✗ Failed to fetch HRV data")
                
                # Wait for next interval
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping HRV collector...")
        finally:
            print("Cleanup complete")


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="HRV Data Collector - Fetches HRV from fitness trackers and sends to backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with simulated data (default)
  python hrv_collector.py
  
  # Run with Fitbit API
  python hrv_collector.py --source fitbit --config hrv_config.json
  
  # Run with Oura Ring API
  python hrv_collector.py --source oura --config hrv_config.json
  
  # Run with Garmin Connect API
  python hrv_collector.py --source garmin --config hrv_config.json
  
  # Run with Apple HealthKit (macOS/iOS only)
  python hrv_collector.py --source apple_healthkit --config hrv_config.json
  
  # Run with multiple sources (fallback chain)
  python hrv_collector.py --sources fitbit oura simulated --config hrv_config.json
  
  # Custom backend and interval
  python hrv_collector.py --backend-url http://192.168.1.100:8000 --interval 120

Configuration File Format (JSON):
  {
    "fitbit": {
      "access_token": "your_fitbit_access_token_here"
    },
    "oura": {
      "access_token": "your_oura_access_token_here"
    },
    "garmin": {
      "consumer_key": "your_garmin_consumer_key",
      "consumer_secret": "your_garmin_consumer_secret",
      "access_token": "your_garmin_access_token",
      "access_token_secret": "your_garmin_access_token_secret"
    },
    "apple_healthkit": {}
  }

Note: Use the provided hrv_config.example.json as a template.
        """
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds between sending data (default: 60)"
    )
    parser.add_argument(
        "--source",
        choices=["fitbit", "garmin", "oura", "apple_healthkit", "healthkit", "simulated"],
        default="simulated",
        help="Primary HRV data source (default: simulated)"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        help="Multiple HRV data sources in priority order (e.g., --sources fitbit oura simulated)"
    )
    parser.add_argument(
        "--config",
        help="Path to API configuration file (JSON)"
    )
    
    args = parser.parse_args()
    
    # Create and run collector
    collector = HRVCollector(
        backend_url=args.backend_url,
        interval=args.interval,
        api_source=args.source,
        config_file=args.config,
        sources=args.sources
    )
    
    collector.run()


if __name__ == "__main__":
    main()
