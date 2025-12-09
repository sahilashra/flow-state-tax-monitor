"""
Ambient Noise Collector
Captures ambient noise from system microphone and sends normalized levels to the backend API.

This script:
1. Accesses the system microphone using PyAudio
2. Calculates RMS (Root Mean Square) amplitude from audio samples
3. Normalizes the audio level to a 0-10 scale (0 = silent, 10 = very loud)
4. Sends noise level data to the backend /data endpoint every 5 seconds

Requirements: 1.1, 3.4
"""

import pyaudio
import numpy as np
import time
import requests
import json
import sys
from typing import Optional
import argparse


class NoiseCollector:
    """Collects ambient noise data from microphone and sends to backend API."""
    
    # Audio configuration
    CHUNK = 1024  # Number of audio samples per frame
    FORMAT = pyaudio.paInt16  # 16-bit audio
    CHANNELS = 1  # Mono audio
    RATE = 44100  # Sample rate (Hz)
    
    # Normalization parameters
    # These values are calibrated to map typical ambient noise levels to 0-10 scale
    # RMS values below MIN_RMS map to 0 (silent)
    # RMS values above MAX_RMS map to 10 (very loud)
    MIN_RMS = 100  # Minimum RMS for noise floor (silent environment)
    MAX_RMS = 5000  # Maximum RMS for very loud environment
    
    def __init__(self, backend_url: str = "http://localhost:8000", 
                 device_index: Optional[int] = None,
                 interval: int = 5):
        """
        Initialize the noise collector.
        
        Args:
            backend_url: URL of the backend API
            device_index: Microphone device index (None for default)
            interval: Interval in seconds between measurements
        """
        self.backend_url = backend_url.rstrip('/')
        self.device_index = device_index
        self.interval = interval
        self.audio = None
        self.stream = None
        
    def list_audio_devices(self):
        """List all available audio input devices."""
        try:
            p = pyaudio.PyAudio()
            print("\nAvailable audio input devices:")
            print("-" * 60)
            
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:  # Only show input devices
                    print(f"Device {i}: {info['name']}")
                    print(f"  Channels: {info['maxInputChannels']}")
                    print(f"  Sample Rate: {info['defaultSampleRate']}")
                    print()
            
            p.terminate()
        except Exception as e:
            print(f"Error listing audio devices: {e}")
    
    def initialize_audio(self) -> bool:
        """
        Initialize PyAudio and open audio stream.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.audio = pyaudio.PyAudio()
            
            # Get device info if specific device is requested
            if self.device_index is not None:
                device_info = self.audio.get_device_info_by_index(self.device_index)
                print(f"Using device: {device_info['name']}")
            else:
                print("Using default microphone")
            
            # Open audio stream
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.CHUNK
            )
            
            print("Microphone initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error initializing microphone: {e}")
            print("\nTroubleshooting:")
            print("1. Check that your microphone is connected")
            print("2. Check microphone permissions in your system settings")
            print("3. Try listing devices with --list-devices flag")
            print("4. Try specifying a different device with --device flag")
            return False
    
    def calculate_rms(self, audio_data: bytes) -> float:
        """
        Calculate RMS (Root Mean Square) amplitude from audio samples.
        
        Args:
            audio_data: Raw audio data bytes
            
        Returns:
            float: RMS amplitude value
        """
        # Convert bytes to numpy array of 16-bit integers
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Calculate RMS: sqrt(mean(x^2))
        rms = np.sqrt(np.mean(audio_array.astype(np.float64) ** 2))
        
        return rms
    
    def normalize_noise_level(self, rms: float) -> float:
        """
        Normalize RMS amplitude to 0-10 scale.
        
        Args:
            rms: RMS amplitude value
            
        Returns:
            float: Normalized noise level (0-10)
        """
        # Linear normalization from MIN_RMS-MAX_RMS to 0-10
        if rms <= self.MIN_RMS:
            return 0.0
        elif rms >= self.MAX_RMS:
            return 10.0
        else:
            # Linear interpolation
            normalized = ((rms - self.MIN_RMS) / (self.MAX_RMS - self.MIN_RMS)) * 10.0
            return round(normalized, 2)
    
    def capture_noise_sample(self) -> Optional[float]:
        """
        Capture a single noise sample from the microphone.
        
        Returns:
            Optional[float]: Normalized noise level (0-10), or None if error
        """
        try:
            # Read audio data from stream
            audio_data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            
            # Calculate RMS amplitude
            rms = self.calculate_rms(audio_data)
            
            # Normalize to 0-10 scale
            noise_level = self.normalize_noise_level(rms)
            
            return noise_level
            
        except Exception as e:
            print(f"Error capturing audio sample: {e}")
            return None
    
    def send_to_backend(self, noise_level: float, hrv: float = 70.0, 
                       notifications: float = 0.0) -> bool:
        """
        Send noise level data to backend API.
        
        Args:
            noise_level: Normalized noise level (0-10)
            hrv: HRV value (default: 70.0 - neutral value)
            notifications: Notification count (default: 0.0)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payload = {
                "hrv_rmssd": hrv,
                "notification_count": notifications,
                "ambient_noise": noise_level
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
        """Main loop: capture noise and send to backend at regular intervals."""
        if not self.initialize_audio():
            return
        
        print(f"\nStarting noise collection...")
        print(f"Sending data to: {self.backend_url}/data")
        print(f"Interval: {self.interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Capture noise sample
                noise_level = self.capture_noise_sample()
                
                if noise_level is not None:
                    print(f"Noise level: {noise_level:.2f}/10 ", end="")
                    
                    # Send to backend
                    success = self.send_to_backend(noise_level)
                    
                    if success:
                        print("✓ Sent to backend")
                    else:
                        print("✗ Failed to send")
                
                # Wait for next interval
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping noise collector...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up audio resources."""
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio is not None:
            self.audio.terminate()
        print("Cleanup complete")


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Ambient Noise Collector - Captures microphone input and sends to backend"
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Microphone device index (use --list-devices to see options)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Interval in seconds between measurements (default: 5)"
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit"
    )
    
    args = parser.parse_args()
    
    # List devices if requested
    if args.list_devices:
        collector = NoiseCollector()
        collector.list_audio_devices()
        return
    
    # Create and run collector
    collector = NoiseCollector(
        backend_url=args.backend_url,
        device_index=args.device,
        interval=args.interval
    )
    
    collector.run()


if __name__ == "__main__":
    main()
