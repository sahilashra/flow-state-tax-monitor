"""
Flow State Tax Monitor - Demo Data Generator

This script simulates realistic focus data and sends it to the backend API.
It generates HRV, notification, and ambient noise data at regular intervals,
including a "Focus Tax" event that demonstrates the impact of interruptions.
"""

import requests
import time
import random
from datetime import datetime


# Configuration
BACKEND_URL = "http://localhost:8000/data"
UPDATE_INTERVAL = 2  # seconds between updates
FOCUS_TAX_INTERVAL = 30  # seconds between Focus Tax events


def generate_hrv(base_hrv: float = 70.0, variation: float = 10.0) -> float:
    """
    Generate realistic HRV values in the 40-100 range.
    
    Args:
        base_hrv: Base HRV value to vary around
        variation: Maximum variation from base value
    
    Returns:
        float: HRV value in range 40-100
    """
    hrv = base_hrv + random.uniform(-variation, variation)
    # Clamp to realistic range
    return max(40.0, min(100.0, hrv))


def generate_notifications(base_rate: float = 1.0) -> float:
    """
    Generate notification count in the 0-5 range.
    
    Args:
        base_rate: Base notification rate (0-5)
    
    Returns:
        float: Notification count in range 0-5
    """
    # Use Poisson-like distribution for realistic notification patterns
    notifications = random.gauss(base_rate, 0.5)
    return max(0.0, min(5.0, notifications))


def generate_ambient_noise(base_noise: float = 3.0, variation: float = 2.0) -> float:
    """
    Generate ambient noise level in the 0-10 range.
    
    Args:
        base_noise: Base noise level
        variation: Maximum variation from base level
    
    Returns:
        float: Noise level in range 0-10
    """
    noise = base_noise + random.uniform(-variation, variation)
    return max(0.0, min(10.0, noise))


def simulate_focus_tax() -> dict:
    """
    Simulate a "Focus Tax" event with spike in notifications.
    
    Returns:
        dict: Focus data with high notification count
    """
    return {
        "hrv_rmssd": generate_hrv(base_hrv=55.0, variation=5.0),  # Lower HRV during stress
        "notification_count": random.uniform(4.0, 5.0),  # High notification spike
        "ambient_noise": generate_ambient_noise(base_noise=6.0, variation=2.0)  # Higher noise
    }


def generate_normal_data() -> dict:
    """
    Generate normal focus data with typical values.
    
    Returns:
        dict: Focus data with normal values
    """
    return {
        "hrv_rmssd": generate_hrv(base_hrv=70.0, variation=10.0),
        "notification_count": generate_notifications(base_rate=1.0),
        "ambient_noise": generate_ambient_noise(base_noise=3.0, variation=2.0)
    }


def send_focus_data(data: dict) -> bool:
    """
    Send focus data to the backend API.
    
    Args:
        data: Dictionary containing hrv_rmssd, notification_count, and ambient_noise
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = requests.post(BACKEND_URL, json=data, timeout=5)
        response.raise_for_status()
        
        # Calculate and display FQS for monitoring
        hrv = data["hrv_rmssd"]
        notifications = data["notification_count"]
        noise = data["ambient_noise"]
        
        # Calculate FQS (matching backend algorithm)
        hrv_score = ((hrv - 40) / 60) * 50
        notification_score = (1 - notifications / 5) * 30
        noise_score = (1 - noise / 10) * 20
        fqs = max(0.0, min(100.0, hrv_score + notification_score + noise_score))
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent data - "
              f"HRV: {hrv:.1f}, Notifications: {notifications:.1f}, "
              f"Noise: {noise:.1f} → FQS: {fqs:.1f}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending data: {e}")
        return False


def run_demo():
    """
    Run the demo data generator.
    
    Continuously generates and sends focus data to the backend,
    with periodic "Focus Tax" events to demonstrate FQS drops.
    """
    print("=" * 70)
    print("Flow State Tax Monitor - Demo Data Generator")
    print("=" * 70)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Update interval: {UPDATE_INTERVAL} seconds")
    print(f"Focus Tax events every ~{FOCUS_TAX_INTERVAL} seconds")
    print("=" * 70)
    print("\nStarting data generation... (Press Ctrl+C to stop)\n")
    
    start_time = time.time()
    last_focus_tax = start_time
    
    try:
        while True:
            current_time = time.time()
            elapsed = current_time - last_focus_tax
            
            # Trigger Focus Tax event periodically
            if elapsed >= FOCUS_TAX_INTERVAL:
                print("\n" + "!" * 70)
                print("🚨 FOCUS TAX EVENT - Notification spike detected!")
                print("!" * 70)
                data = simulate_focus_tax()
                last_focus_tax = current_time
            else:
                data = generate_normal_data()
            
            # Send data to backend
            send_focus_data(data)
            
            # Wait before next update
            time.sleep(UPDATE_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("Demo stopped by user")
        print("=" * 70)
    except Exception as e:
        print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    run_demo()
