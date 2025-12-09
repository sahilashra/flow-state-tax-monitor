"""
Windows Notification Counter
Monitors Windows notification center and sends normalized notification counts to the backend API.

This script:
1. Uses Windows API (win32gui/win32con) to track notification events
2. Counts notifications in a rolling 5-minute window
3. Normalizes the count to a 0-5 scale for API compatibility
4. Sends notification count to backend /data endpoint at regular intervals
5. Handles Windows API access errors gracefully
6. Provides option to filter notification types (system vs app notifications)

Requirements: 1.1, 3.2
"""

import time
import requests
import argparse
import sys
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, List, Dict
import threading

# Windows-specific imports
try:
    import win32gui
    import win32con
    import win32api
    import win32process
    import pywintypes
    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False
    print("Warning: Windows API libraries not available.")
    print("Install with: pip install pywin32")


class NotificationCounter:
    """Monitors Windows notifications and sends counts to backend API."""
    
    # Normalization parameters
    # Notifications are counted in a 5-minute rolling window
    # The count is then normalized to 0-5 scale
    MAX_NOTIFICATIONS = 20  # 20+ notifications in 5 minutes maps to 5.0
    WINDOW_DURATION = 300  # 5 minutes in seconds
    
    def __init__(self, backend_url: str = "http://localhost:8000",
                 interval: int = 5,
                 filter_system: bool = False,
                 filter_app: bool = False):
        """
        Initialize the notification counter.
        
        Args:
            backend_url: URL of the backend API
            interval: Interval in seconds between sending data to backend
            filter_system: If True, exclude system notifications
            filter_app: If True, exclude app notifications
        """
        self.backend_url = backend_url.rstrip('/')
        self.interval = interval
        self.filter_system = filter_system
        self.filter_app = filter_app
        
        # Rolling window of notification timestamps
        self.notification_times: deque = deque()
        
        # Lock for thread-safe access to notification_times
        self.lock = threading.Lock()
        
        # Notification tracking
        self.total_notifications = 0
        
    def check_windows_api(self) -> bool:
        """
        Check if Windows API is available.
        
        Returns:
            bool: True if available, False otherwise
        """
        if not WINDOWS_API_AVAILABLE:
            print("Error: Windows API (pywin32) is not installed")
            print("\nTo install:")
            print("  pip install pywin32")
            print("\nAfter installation, you may need to run:")
            print("  python -m pywin32_postinstall -install")
            return False
        
        if sys.platform != 'win32':
            print("Error: This script only works on Windows")
            return False
        
        return True
    
    def add_notification(self, notification_type: str = "app"):
        """
        Add a notification to the rolling window.
        
        Args:
            notification_type: Type of notification ("system" or "app")
        """
        # Apply filters
        if self.filter_system and notification_type == "system":
            return
        if self.filter_app and notification_type == "app":
            return
        
        with self.lock:
            current_time = datetime.now()
            self.notification_times.append(current_time)
            self.total_notifications += 1
    
    def clean_old_notifications(self):
        """Remove notifications older than the rolling window duration."""
        with self.lock:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(seconds=self.WINDOW_DURATION)
            
            # Remove old notifications from the left of the deque
            while self.notification_times and self.notification_times[0] < cutoff_time:
                self.notification_times.popleft()
    
    def get_notification_count(self) -> int:
        """
        Get the current notification count in the rolling window.
        
        Returns:
            int: Number of notifications in the last 5 minutes
        """
        self.clean_old_notifications()
        with self.lock:
            return len(self.notification_times)
    
    def normalize_notification_count(self, count: int) -> float:
        """
        Normalize notification count to 0-5 scale.
        
        Args:
            count: Raw notification count
            
        Returns:
            float: Normalized count (0-5)
        """
        if count <= 0:
            return 0.0
        elif count >= self.MAX_NOTIFICATIONS:
            return 5.0
        else:
            # Linear interpolation from 0-MAX_NOTIFICATIONS to 0-5
            normalized = (count / self.MAX_NOTIFICATIONS) * 5.0
            return round(normalized, 2)
    
    def monitor_notifications_polling(self):
        """
        Monitor notifications using polling method.
        
        This is a simplified approach that checks for notification-related windows.
        Note: This is a basic implementation. For production use, consider using
        Windows notification APIs or monitoring the notification database.
        """
        print("Starting notification monitoring (polling mode)...")
        print("Note: This is a simplified implementation that may not catch all notifications.")
        print("For more accurate tracking, consider using Windows notification APIs.\n")
        
        # Track known notification windows
        known_windows = set()
        
        def enum_windows_callback(hwnd, results):
            """Callback for enumerating windows."""
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                # Look for notification-related windows
                # Windows 10/11 notification windows typically have specific class names
                notification_classes = [
                    'Windows.UI.Core.CoreWindow',  # Windows 10/11 notifications
                    'NotifyIcon',
                    'ToastNotification'
                ]
                
                if any(nc in class_name for nc in notification_classes):
                    window_id = (hwnd, window_text, class_name)
                    if window_id not in known_windows:
                        known_windows.add(window_id)
                        
                        # Determine notification type
                        notification_type = "system" if "System" in window_text else "app"
                        self.add_notification(notification_type)
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Detected notification: {window_text or class_name}")
        
        try:
            while True:
                try:
                    win32gui.EnumWindows(enum_windows_callback, None)
                except pywintypes.error as e:
                    print(f"Warning: Windows API error: {e}")
                
                time.sleep(1)  # Poll every second
                
        except KeyboardInterrupt:
            print("\nStopping notification monitoring...")
    
    def simulate_notifications(self):
        """
        Simulate notifications for testing purposes.
        This generates random notifications to test the system.
        """
        import random
        
        print("Running in SIMULATION mode - generating random notifications")
        print("This is for testing only. Use on Windows for real notification tracking.\n")
        
        try:
            while True:
                # Randomly generate notifications (0-3 per interval)
                num_notifications = random.randint(0, 3)
                
                for _ in range(num_notifications):
                    notification_type = random.choice(["app", "system"])
                    self.add_notification(notification_type)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Simulated {notification_type} notification")
                
                time.sleep(random.uniform(5, 15))  # Random interval between 5-15 seconds
                
        except KeyboardInterrupt:
            print("\nStopping simulation...")
    
    def send_to_backend(self, notification_count: float, hrv: float = 70.0,
                       noise: float = 5.0) -> bool:
        """
        Send notification count to backend API.
        
        Args:
            notification_count: Normalized notification count (0-5)
            hrv: HRV value (default: 70.0 - neutral value)
            noise: Noise level (default: 5.0 - neutral value)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payload = {
                "hrv_rmssd": hrv,
                "notification_count": notification_count,
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
    
    def run(self, simulate: bool = False):
        """
        Main loop: monitor notifications and send counts to backend.
        
        Args:
            simulate: If True, run in simulation mode for testing
        """
        if not simulate and not self.check_windows_api():
            print("\nFalling back to simulation mode...")
            simulate = True
        
        # Start notification monitoring in a separate thread
        if simulate:
            monitor_thread = threading.Thread(target=self.simulate_notifications, daemon=True)
        else:
            monitor_thread = threading.Thread(target=self.monitor_notifications_polling, daemon=True)
        
        monitor_thread.start()
        
        print(f"\nStarting notification counter...")
        print(f"Sending data to: {self.backend_url}/data")
        print(f"Interval: {self.interval} seconds")
        print(f"Rolling window: {self.WINDOW_DURATION} seconds (5 minutes)")
        
        if self.filter_system:
            print("Filtering: Excluding system notifications")
        if self.filter_app:
            print("Filtering: Excluding app notifications")
        
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Get current notification count
                raw_count = self.get_notification_count()
                normalized_count = self.normalize_notification_count(raw_count)
                
                print(f"Notifications (5min): {raw_count} -> {normalized_count:.2f}/5 ", end="")
                print(f"(Total: {self.total_notifications}) ", end="")
                
                # Send to backend
                success = self.send_to_backend(normalized_count)
                
                if success:
                    print("✓ Sent to backend")
                else:
                    print("✗ Failed to send")
                
                # Wait for next interval
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping notification counter...")
        finally:
            print("Cleanup complete")


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Windows Notification Counter - Monitors notifications and sends to backend"
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Interval in seconds between sending data (default: 5)"
    )
    parser.add_argument(
        "--filter-system",
        action="store_true",
        help="Exclude system notifications from count"
    )
    parser.add_argument(
        "--filter-app",
        action="store_true",
        help="Exclude app notifications from count"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run in simulation mode (for testing without Windows API)"
    )
    
    args = parser.parse_args()
    
    # Create and run counter
    counter = NotificationCounter(
        backend_url=args.backend_url,
        interval=args.interval,
        filter_system=args.filter_system,
        filter_app=args.filter_app
    )
    
    counter.run(simulate=args.simulate)


if __name__ == "__main__":
    main()
