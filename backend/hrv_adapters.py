"""
HRV Data Source Adapters
Implements the adapter pattern for different fitness tracker APIs.

This module provides a unified interface for fetching HRV data from various sources:
- Fitbit API
- Garmin Connect API
- Oura Ring API
- Apple HealthKit (macOS/iOS only)
- Simulated data (for testing)

Each adapter implements the HRVAdapter interface and handles:
- Authentication
- API requests
- Data parsing
- Error handling
- Rate limiting

Requirements: 1.1, 3.3
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import requests
import random
from datetime import datetime


class HRVAdapter(ABC):
    """Abstract base class for HRV data source adapters."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the adapter with configuration.
        
        Args:
            config: Configuration dictionary specific to this adapter
        """
        self.config = config
    
    @abstractmethod
    def fetch_hrv(self) -> Optional[float]:
        """
        Fetch HRV (RMSSD) data from the source.
        
        Returns:
            Optional[float]: HRV value in milliseconds, or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Get the name of this data source.
        
        Returns:
            str: Human-readable name of the data source
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Validate that the configuration contains required fields.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        return True


class FitbitAdapter(HRVAdapter):
    """Adapter for Fitbit API."""
    
    def get_source_name(self) -> str:
        return "Fitbit"
    
    def validate_config(self) -> bool:
        """Validate Fitbit configuration."""
        return 'access_token' in self.config
    
    def fetch_hrv(self) -> Optional[float]:
        """
        Fetch HRV data from Fitbit API.
        
        Requires OAuth 2.0 authentication with access token in config.
        
        Returns:
            Optional[float]: HRV value (RMSSD) or None if error
        """
        try:
            access_token = self.config.get('access_token')
            if not access_token:
                print("Error: Fitbit access token not found in configuration")
                return None
            
            # Fitbit HRV API endpoint
            # Get HRV data for today
            date_str = datetime.now().strftime('%Y-%m-%d')
            url = f"https://api.fitbit.com/1/user/-/hrv/date/{date_str}.json"
            
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                print("Error: Fitbit access token expired or invalid")
                print("Please refresh your access token")
                return None
            
            if response.status_code == 429:
                print("Error: Fitbit API rate limit exceeded")
                print("Will retry later")
                return None
            
            if response.status_code != 200:
                print(f"Error: Fitbit API returned status {response.status_code}")
                return None
            
            data = response.json()
            
            # Extract HRV RMSSD value
            # Fitbit returns HRV data in the 'hrv' array
            if 'hrv' in data and len(data['hrv']) > 0:
                # Get the most recent HRV reading
                latest_hrv = data['hrv'][0]
                
                # Fitbit provides daily RMSSD in the 'value' field
                if 'value' in latest_hrv and 'dailyRmssd' in latest_hrv['value']:
                    rmssd = latest_hrv['value']['dailyRmssd']
                    print(f"Fetched HRV from Fitbit: {rmssd:.1f}")
                    return float(rmssd)
            
            print("Warning: No HRV data available from Fitbit")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Fitbit data: {e}")
            return None
        except Exception as e:
            print(f"Error processing Fitbit data: {e}")
            return None


class GarminAdapter(HRVAdapter):
    """Adapter for Garmin Connect API."""
    
    def get_source_name(self) -> str:
        return "Garmin Connect"
    
    def validate_config(self) -> bool:
        """Validate Garmin configuration."""
        required_fields = ['consumer_key', 'consumer_secret', 'access_token', 'access_token_secret']
        return all(field in self.config for field in required_fields)
    
    def fetch_hrv(self) -> Optional[float]:
        """
        Fetch HRV data from Garmin Connect API.
        
        Note: Garmin Connect API requires OAuth 1.0 authentication.
        This is a placeholder implementation that would need the garth library
        or similar OAuth 1.0 implementation.
        
        Returns:
            Optional[float]: HRV value (RMSSD) or None if error
        """
        print("Warning: Garmin Connect API integration requires OAuth 1.0")
        print("Consider using the 'garth' library for Garmin authentication")
        print("Placeholder implementation - returning None")
        
        # TODO: Implement Garmin OAuth 1.0 authentication
        # This would require:
        # 1. OAuth 1.0 signature generation
        # 2. Request token exchange
        # 3. API endpoint calls to Garmin Health API
        # 4. Parsing Garmin's HRV data format
        
        return None


class OuraAdapter(HRVAdapter):
    """Adapter for Oura Ring API."""
    
    def get_source_name(self) -> str:
        return "Oura Ring"
    
    def validate_config(self) -> bool:
        """Validate Oura configuration."""
        return 'access_token' in self.config
    
    def fetch_hrv(self) -> Optional[float]:
        """
        Fetch HRV data from Oura Ring API.
        
        Requires Personal Access Token in config.
        
        Returns:
            Optional[float]: HRV value (RMSSD) or None if error
        """
        try:
            access_token = self.config.get('access_token')
            if not access_token:
                print("Error: Oura access token not found in configuration")
                return None
            
            # Oura API v2 endpoint for HRV data
            # Get sleep data which includes HRV
            date_str = datetime.now().strftime('%Y-%m-%d')
            url = f"https://api.ouraring.com/v2/usercollection/sleep"
            
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            params = {
                'start_date': date_str,
                'end_date': date_str
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 401:
                print("Error: Oura access token expired or invalid")
                return None
            
            if response.status_code == 429:
                print("Error: Oura API rate limit exceeded")
                return None
            
            if response.status_code != 200:
                print(f"Error: Oura API returned status {response.status_code}")
                return None
            
            data = response.json()
            
            # Extract HRV from sleep data
            if 'data' in data and len(data['data']) > 0:
                # Get the most recent sleep session
                latest_sleep = data['data'][0]
                
                # Oura provides HRV in the 'heart_rate' section
                if 'heart_rate' in latest_sleep:
                    hr_data = latest_sleep['heart_rate']
                    # Oura doesn't directly provide RMSSD, but provides average HRV
                    # We'll use the average as an approximation
                    if 'average' in hr_data:
                        # Note: This is an approximation
                        # Oura's HRV metrics may need conversion
                        hrv_value = hr_data.get('average', 70.0)
                        print(f"Fetched HRV from Oura: {hrv_value:.1f}")
                        return float(hrv_value)
            
            print("Warning: No HRV data available from Oura")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Oura data: {e}")
            return None
        except Exception as e:
            print(f"Error processing Oura data: {e}")
            return None


class AppleHealthKitAdapter(HRVAdapter):
    """
    Adapter for Apple HealthKit.
    
    Note: This requires macOS/iOS and the pyobjc library to access HealthKit.
    This is a placeholder implementation.
    """
    
    def get_source_name(self) -> str:
        return "Apple HealthKit"
    
    def validate_config(self) -> bool:
        """Validate Apple HealthKit configuration."""
        # HealthKit doesn't require API tokens, but needs system permissions
        return True
    
    def fetch_hrv(self) -> Optional[float]:
        """
        Fetch HRV data from Apple HealthKit.
        
        Requires macOS/iOS and pyobjc library.
        This is a placeholder implementation.
        
        Returns:
            Optional[float]: HRV value (RMSSD) or None if error
        """
        print("Warning: Apple HealthKit integration requires macOS/iOS")
        print("This requires the pyobjc library and HealthKit permissions")
        print("Placeholder implementation - returning None")
        
        # TODO: Implement HealthKit integration
        # This would require:
        # 1. pyobjc library installation
        # 2. HealthKit authorization request
        # 3. Query for HRV samples (HKQuantityTypeIdentifierHeartRateVariabilitySDNN)
        # 4. Convert to RMSSD format
        
        # Example pseudo-code:
        # from Foundation import NSDate
        # from HealthKit import HKHealthStore, HKQuantityType, HKQuery
        # 
        # health_store = HKHealthStore()
        # hrv_type = HKQuantityType.quantityTypeForIdentifier_("HKQuantityTypeIdentifierHeartRateVariabilitySDNN")
        # # Query for recent HRV samples
        # # Parse and return RMSSD value
        
        return None


class SimulatedAdapter(HRVAdapter):
    """Adapter for simulated HRV data (for testing)."""
    
    # HRV simulation parameters
    SIMULATED_HRV_MIN = 40.0
    SIMULATED_HRV_MAX = 100.0
    SIMULATED_HRV_MEAN = 70.0
    SIMULATED_HRV_STDDEV = 15.0
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.last_value: Optional[float] = None
    
    def get_source_name(self) -> str:
        return "Simulated"
    
    def fetch_hrv(self) -> Optional[float]:
        """
        Generate simulated HRV data for testing.
        
        Uses a random walk model to create realistic-looking HRV variations.
        
        Returns:
            float: Simulated HRV value (RMSSD)
        """
        # If we have a previous value, vary it slightly
        if self.last_value is not None:
            # Random walk: small change from previous value
            change = random.gauss(0, 3)  # Small random change
            new_hrv = self.last_value + change
        else:
            # Generate initial value from normal distribution
            new_hrv = random.gauss(self.SIMULATED_HRV_MEAN, self.SIMULATED_HRV_STDDEV)
        
        # Clamp to realistic range
        new_hrv = max(self.SIMULATED_HRV_MIN, min(self.SIMULATED_HRV_MAX, new_hrv))
        new_hrv = round(new_hrv, 1)
        
        self.last_value = new_hrv
        return new_hrv


class AdapterFactory:
    """Factory for creating HRV adapters based on source type."""
    
    # Registry of available adapters
    _adapters = {
        'fitbit': FitbitAdapter,
        'garmin': GarminAdapter,
        'oura': OuraAdapter,
        'apple_healthkit': AppleHealthKitAdapter,
        'healthkit': AppleHealthKitAdapter,  # Alias
        'simulated': SimulatedAdapter,
    }
    
    @classmethod
    def create_adapter(cls, source: str, config: Dict[str, Any]) -> HRVAdapter:
        """
        Create an HRV adapter for the specified source.
        
        Args:
            source: Data source name (e.g., 'fitbit', 'oura', 'simulated')
            config: Configuration dictionary for the adapter
            
        Returns:
            HRVAdapter: Configured adapter instance
            
        Raises:
            ValueError: If source is not supported
        """
        source_lower = source.lower()
        
        if source_lower not in cls._adapters:
            available = ', '.join(cls._adapters.keys())
            raise ValueError(
                f"Unknown HRV source: {source}. "
                f"Available sources: {available}"
            )
        
        adapter_class = cls._adapters[source_lower]
        adapter = adapter_class(config)
        
        # Validate configuration
        if not adapter.validate_config():
            print(f"Warning: Invalid configuration for {adapter.get_source_name()}")
            print("Some features may not work correctly")
        
        return adapter
    
    @classmethod
    def get_available_sources(cls) -> list:
        """
        Get list of available HRV data sources.
        
        Returns:
            list: List of source names
        """
        return list(cls._adapters.keys())
