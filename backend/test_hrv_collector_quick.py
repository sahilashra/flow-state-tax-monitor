"""Quick test script for HRV collector functionality."""

import sys
import time
from hrv_collector import HRVCollector

def test_simulated_hrv():
    """Test simulated HRV generation."""
    print("Testing simulated HRV generation...")
    collector = HRVCollector(
        backend_url="http://localhost:8000",
        interval=5,
        api_source="simulated"
    )
    
    # Generate a few HRV values using the adapter
    print("\nGenerating 5 simulated HRV values:")
    for i in range(5):
        hrv = collector.adapter.fetch_hrv()
        print(f"  {i+1}. HRV: {hrv:.1f} ms")
        assert 40.0 <= hrv <= 100.0, f"HRV out of range: {hrv}"
    
    print("✓ Simulated HRV generation works correctly")
    return True

def test_cache():
    """Test caching functionality."""
    print("\nTesting cache functionality...")
    collector = HRVCollector(
        backend_url="http://localhost:8000",
        interval=5,
        api_source="simulated"
    )
    
    # Save a value to cache
    test_hrv = 75.5
    collector.save_cache(test_hrv)
    print(f"  Saved HRV to cache: {test_hrv}")
    
    # Load from cache
    loaded = collector.load_cache()
    assert loaded, "Failed to load cache"
    assert collector.cached_hrv == test_hrv, f"Cache mismatch: {collector.cached_hrv} != {test_hrv}"
    print(f"  Loaded HRV from cache: {collector.cached_hrv}")
    
    print("✓ Cache functionality works correctly")
    return True

def test_backend_connection():
    """Test connection to backend."""
    print("\nTesting backend connection...")
    collector = HRVCollector(
        backend_url="http://localhost:8000",
        interval=5,
        api_source="simulated"
    )
    
    # Try to send data
    test_hrv = 70.0
    success = collector.send_to_backend(test_hrv)
    
    if success:
        print(f"  ✓ Successfully sent HRV ({test_hrv}) to backend")
    else:
        print(f"  ✗ Failed to send to backend (is the server running?)")
        return False
    
    return True

def test_fetch_hrv():
    """Test fetching HRV data."""
    print("\nTesting HRV data fetching...")
    collector = HRVCollector(
        backend_url="http://localhost:8000",
        interval=5,
        api_source="simulated"
    )
    
    # Fetch HRV data
    hrv = collector.fetch_hrv_data()
    assert hrv is not None, "Failed to fetch HRV data"
    assert 40.0 <= hrv <= 100.0, f"HRV out of range: {hrv}"
    print(f"  Fetched HRV: {hrv:.1f} ms")
    
    # Fetch again (should use cache)
    hrv2 = collector.fetch_hrv_data()
    assert hrv2 == hrv, "Cache not working correctly"
    print(f"  Fetched HRV (cached): {hrv2:.1f} ms")
    
    print("✓ HRV fetching works correctly")
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("HRV Collector Quick Test")
    print("=" * 60)
    
    tests = [
        ("Simulated HRV Generation", test_simulated_hrv),
        ("Cache Functionality", test_cache),
        ("Backend Connection", test_backend_connection),
        ("HRV Data Fetching", test_fetch_hrv),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
