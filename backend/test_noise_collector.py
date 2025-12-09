"""
Unit tests for the Ambient Noise Collector

Tests the core functionality of noise collection, RMS calculation, and normalization.
"""

import pytest
import numpy as np
from noise_collector import NoiseCollector


class TestNoiseCollector:
    """Test suite for NoiseCollector class."""
    
    def test_calculate_rms_silent(self):
        """Test RMS calculation with silent audio (all zeros)."""
        collector = NoiseCollector()
        
        # Create silent audio data (all zeros)
        silent_audio = np.zeros(1024, dtype=np.int16)
        audio_bytes = silent_audio.tobytes()
        
        rms = collector.calculate_rms(audio_bytes)
        
        assert rms == 0.0, "RMS of silent audio should be 0"
    
    def test_calculate_rms_constant_signal(self):
        """Test RMS calculation with constant signal."""
        collector = NoiseCollector()
        
        # Create constant signal
        constant_value = 1000
        audio_array = np.full(1024, constant_value, dtype=np.int16)
        audio_bytes = audio_array.tobytes()
        
        rms = collector.calculate_rms(audio_bytes)
        
        # RMS of constant signal should equal the constant value
        assert abs(rms - constant_value) < 1.0, f"RMS should be close to {constant_value}"
    
    def test_calculate_rms_sine_wave(self):
        """Test RMS calculation with sine wave."""
        collector = NoiseCollector()
        
        # Create sine wave
        amplitude = 5000
        samples = 1024
        frequency = 440  # Hz
        sample_rate = 44100
        
        t = np.arange(samples) / sample_rate
        sine_wave = (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
        audio_bytes = sine_wave.tobytes()
        
        rms = collector.calculate_rms(audio_bytes)
        
        # RMS of sine wave should be amplitude / sqrt(2)
        expected_rms = amplitude / np.sqrt(2)
        assert abs(rms - expected_rms) < 100, f"RMS should be close to {expected_rms}"
    
    def test_normalize_noise_level_minimum(self):
        """Test normalization at minimum threshold."""
        collector = NoiseCollector()
        
        # RMS at or below MIN_RMS should map to 0
        noise_level = collector.normalize_noise_level(50)
        assert noise_level == 0.0, "RMS below MIN_RMS should map to 0"
        
        noise_level = collector.normalize_noise_level(collector.MIN_RMS)
        assert noise_level == 0.0, "RMS at MIN_RMS should map to 0"
    
    def test_normalize_noise_level_maximum(self):
        """Test normalization at maximum threshold."""
        collector = NoiseCollector()
        
        # RMS at or above MAX_RMS should map to 10
        noise_level = collector.normalize_noise_level(10000)
        assert noise_level == 10.0, "RMS above MAX_RMS should map to 10"
        
        noise_level = collector.normalize_noise_level(collector.MAX_RMS)
        assert noise_level == 10.0, "RMS at MAX_RMS should map to 10"
    
    def test_normalize_noise_level_midpoint(self):
        """Test normalization at midpoint."""
        collector = NoiseCollector()
        
        # Midpoint between MIN_RMS and MAX_RMS should map to 5
        midpoint_rms = (collector.MIN_RMS + collector.MAX_RMS) / 2
        noise_level = collector.normalize_noise_level(midpoint_rms)
        
        assert abs(noise_level - 5.0) < 0.1, "Midpoint RMS should map to approximately 5"
    
    def test_normalize_noise_level_range(self):
        """Test that normalization always returns values in 0-10 range."""
        collector = NoiseCollector()
        
        # Test various RMS values
        test_values = [0, 50, 100, 500, 1000, 2500, 5000, 10000, 20000]
        
        for rms in test_values:
            noise_level = collector.normalize_noise_level(rms)
            assert 0.0 <= noise_level <= 10.0, \
                f"Normalized noise level {noise_level} should be in range 0-10"
    
    def test_normalize_noise_level_monotonic(self):
        """Test that normalization is monotonically increasing."""
        collector = NoiseCollector()
        
        # Higher RMS should always produce higher or equal noise level
        rms_values = [100, 500, 1000, 2000, 3000, 4000, 5000]
        noise_levels = [collector.normalize_noise_level(rms) for rms in rms_values]
        
        for i in range(len(noise_levels) - 1):
            assert noise_levels[i] <= noise_levels[i + 1], \
                "Noise levels should be monotonically increasing with RMS"
    
    def test_initialization_defaults(self):
        """Test NoiseCollector initialization with default values."""
        collector = NoiseCollector()
        
        assert collector.backend_url == "http://localhost:8000"
        assert collector.device_index is None
        assert collector.interval == 5
    
    def test_initialization_custom_values(self):
        """Test NoiseCollector initialization with custom values."""
        collector = NoiseCollector(
            backend_url="http://example.com:9000",
            device_index=2,
            interval=10
        )
        
        assert collector.backend_url == "http://example.com:9000"
        assert collector.device_index == 2
        assert collector.interval == 10
    
    def test_backend_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from backend URL."""
        collector = NoiseCollector(backend_url="http://localhost:8000/")
        
        assert collector.backend_url == "http://localhost:8000"
        assert not collector.backend_url.endswith("/")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
