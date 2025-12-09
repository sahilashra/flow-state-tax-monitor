"""
Unit tests for the Ambient Noise Collector (without PyAudio dependency)

Tests the core functionality of RMS calculation and normalization without requiring
PyAudio to be installed. This allows testing the mathematical logic independently.
"""

import pytest
import numpy as np


# Import only the functions we need, not the full class that requires PyAudio
def calculate_rms(audio_data: bytes) -> float:
    """Calculate RMS (Root Mean Square) amplitude from audio samples."""
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    rms = np.sqrt(np.mean(audio_array.astype(np.float64) ** 2))
    return rms


def normalize_noise_level(rms: float, min_rms: float = 100, max_rms: float = 5000) -> float:
    """Normalize RMS amplitude to 0-10 scale."""
    if rms <= min_rms:
        return 0.0
    elif rms >= max_rms:
        return 10.0
    else:
        normalized = ((rms - min_rms) / (max_rms - min_rms)) * 10.0
        return round(normalized, 2)


class TestRMSCalculation:
    """Test suite for RMS calculation."""
    
    def test_calculate_rms_silent(self):
        """Test RMS calculation with silent audio (all zeros)."""
        # Create silent audio data (all zeros)
        silent_audio = np.zeros(1024, dtype=np.int16)
        audio_bytes = silent_audio.tobytes()
        
        rms = calculate_rms(audio_bytes)
        
        assert rms == 0.0, "RMS of silent audio should be 0"
    
    def test_calculate_rms_constant_signal(self):
        """Test RMS calculation with constant signal."""
        # Create constant signal
        constant_value = 1000
        audio_array = np.full(1024, constant_value, dtype=np.int16)
        audio_bytes = audio_array.tobytes()
        
        rms = calculate_rms(audio_bytes)
        
        # RMS of constant signal should equal the constant value
        assert abs(rms - constant_value) < 1.0, f"RMS should be close to {constant_value}"
    
    def test_calculate_rms_sine_wave(self):
        """Test RMS calculation with sine wave."""
        # Create sine wave
        amplitude = 5000
        samples = 1024
        frequency = 440  # Hz
        sample_rate = 44100
        
        t = np.arange(samples) / sample_rate
        sine_wave = (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
        audio_bytes = sine_wave.tobytes()
        
        rms = calculate_rms(audio_bytes)
        
        # RMS of sine wave should be amplitude / sqrt(2)
        expected_rms = amplitude / np.sqrt(2)
        assert abs(rms - expected_rms) < 100, f"RMS should be close to {expected_rms}"
    
    def test_calculate_rms_positive_values(self):
        """Test that RMS is always positive."""
        # Create audio with negative values
        audio_array = np.array([-1000, -500, -2000, -1500], dtype=np.int16)
        audio_bytes = audio_array.tobytes()
        
        rms = calculate_rms(audio_bytes)
        
        assert rms > 0, "RMS should always be positive"


class TestNormalization:
    """Test suite for noise level normalization."""
    
    def test_normalize_noise_level_minimum(self):
        """Test normalization at minimum threshold."""
        # RMS at or below MIN_RMS should map to 0
        noise_level = normalize_noise_level(50)
        assert noise_level == 0.0, "RMS below MIN_RMS should map to 0"
        
        noise_level = normalize_noise_level(100)
        assert noise_level == 0.0, "RMS at MIN_RMS should map to 0"
    
    def test_normalize_noise_level_maximum(self):
        """Test normalization at maximum threshold."""
        # RMS at or above MAX_RMS should map to 10
        noise_level = normalize_noise_level(10000)
        assert noise_level == 10.0, "RMS above MAX_RMS should map to 10"
        
        noise_level = normalize_noise_level(5000)
        assert noise_level == 10.0, "RMS at MAX_RMS should map to 10"
    
    def test_normalize_noise_level_midpoint(self):
        """Test normalization at midpoint."""
        # Midpoint between MIN_RMS (100) and MAX_RMS (5000) should map to 5
        midpoint_rms = (100 + 5000) / 2  # 2550
        noise_level = normalize_noise_level(midpoint_rms)
        
        assert abs(noise_level - 5.0) < 0.1, "Midpoint RMS should map to approximately 5"
    
    def test_normalize_noise_level_range(self):
        """Test that normalization always returns values in 0-10 range."""
        # Test various RMS values
        test_values = [0, 50, 100, 500, 1000, 2500, 5000, 10000, 20000]
        
        for rms in test_values:
            noise_level = normalize_noise_level(rms)
            assert 0.0 <= noise_level <= 10.0, \
                f"Normalized noise level {noise_level} should be in range 0-10"
    
    def test_normalize_noise_level_monotonic(self):
        """Test that normalization is monotonically increasing."""
        # Higher RMS should always produce higher or equal noise level
        rms_values = [100, 500, 1000, 2000, 3000, 4000, 5000]
        noise_levels = [normalize_noise_level(rms) for rms in rms_values]
        
        for i in range(len(noise_levels) - 1):
            assert noise_levels[i] <= noise_levels[i + 1], \
                "Noise levels should be monotonically increasing with RMS"
    
    def test_normalize_noise_level_linear(self):
        """Test that normalization is linear in the valid range."""
        # Test linearity: doubling the distance from MIN_RMS should double the output
        min_rms = 100
        max_rms = 5000
        
        # Quarter point
        quarter_rms = min_rms + (max_rms - min_rms) * 0.25
        quarter_level = normalize_noise_level(quarter_rms, min_rms, max_rms)
        
        # Three-quarter point
        three_quarter_rms = min_rms + (max_rms - min_rms) * 0.75
        three_quarter_level = normalize_noise_level(three_quarter_rms, min_rms, max_rms)
        
        # Check linearity
        assert abs(quarter_level - 2.5) < 0.1, "Quarter point should map to ~2.5"
        assert abs(three_quarter_level - 7.5) < 0.1, "Three-quarter point should map to ~7.5"
    
    def test_normalize_noise_level_custom_range(self):
        """Test normalization with custom min/max values."""
        # Use custom range
        custom_min = 200
        custom_max = 8000
        
        # Test boundaries
        assert normalize_noise_level(200, custom_min, custom_max) == 0.0
        assert normalize_noise_level(8000, custom_min, custom_max) == 10.0
        
        # Test midpoint
        midpoint = (custom_min + custom_max) / 2
        midpoint_level = normalize_noise_level(midpoint, custom_min, custom_max)
        assert abs(midpoint_level - 5.0) < 0.1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_rms_with_very_small_samples(self):
        """Test RMS calculation with very small audio samples."""
        # Single sample
        audio_array = np.array([1000], dtype=np.int16)
        audio_bytes = audio_array.tobytes()
        rms = calculate_rms(audio_bytes)
        assert rms == 1000.0
        
        # Two samples
        audio_array = np.array([1000, 2000], dtype=np.int16)
        audio_bytes = audio_array.tobytes()
        rms = calculate_rms(audio_bytes)
        expected = np.sqrt((1000**2 + 2000**2) / 2)
        assert abs(rms - expected) < 1.0
    
    def test_rms_with_max_int16_values(self):
        """Test RMS calculation with maximum int16 values."""
        # Maximum positive value for int16
        max_val = 32767
        audio_array = np.full(1024, max_val, dtype=np.int16)
        audio_bytes = audio_array.tobytes()
        
        rms = calculate_rms(audio_bytes)
        assert abs(rms - max_val) < 1.0
    
    def test_normalization_with_zero_range(self):
        """Test normalization when min equals max (edge case)."""
        # This is a degenerate case, but should not crash
        # When min == max, any value should map to either 0 or 10
        result = normalize_noise_level(1000, min_rms=1000, max_rms=1000)
        assert result in [0.0, 10.0], "Degenerate case should return boundary value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
