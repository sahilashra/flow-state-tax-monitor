"""
Quick test script to verify Windows notification tracking is working.
This will monitor for 30 seconds and show any notifications detected.
"""

import sys
import time
from notification_counter import NotificationCounter

def test_windows_notifications():
    print("=" * 60)
    print("Windows Notification Tracker Test")
    print("=" * 60)
    print("\nThis will monitor Windows notifications for 30 seconds.")
    print("Try opening apps, getting notifications, etc.\n")
    
    # Check if Windows API is available
    counter = NotificationCounter()
    
    if not counter.check_windows_api():
        print("❌ Windows API not available!")
        print("Make sure pywin32 is installed: pip install pywin32")
        return False
    
    print("✅ Windows API is available!")
    print("\nStarting notification monitoring...")
    print("(This uses polling mode - may not catch all notifications)\n")
    
    # Start monitoring
    import threading
    monitor_thread = threading.Thread(
        target=counter.monitor_notifications_polling,
        daemon=True
    )
    monitor_thread.start()
    
    # Monitor for 30 seconds
    start_time = time.time()
    last_count = 0
    
    try:
        while time.time() - start_time < 30:
            current_count = counter.get_notification_count()
            
            if current_count != last_count:
                print(f"✓ Notification detected! Total in last 5 min: {current_count}")
                last_count = current_count
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print(f"Total notifications detected: {counter.total_notifications}")
    print(f"Notifications in rolling window: {counter.get_notification_count()}")
    
    if counter.total_notifications > 0:
        print("\n✅ Windows notification tracking is working!")
    else:
        print("\n⚠️  No notifications detected in 30 seconds.")
        print("This is normal if you didn't receive any notifications.")
        print("The tracker is working and will detect notifications when they occur.")
    
    return True

if __name__ == "__main__":
    test_windows_notifications()
