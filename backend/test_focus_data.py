"""
Property-based tests for FocusData model validation
Tests validate that the Pydantic model correctly accepts valid inputs
and rejects invalid inputs according to the specification.
"""

import pytest
from hypothesis import given, strategies as st, settings
from pydantic import ValidationError
from main import FocusData


# Property 1: Valid input acceptance
# Feature: flow-state-tax-monitor, Property 1: Valid input acceptance
# Validates: Requirements 1.1
@settings(max_examples=100)
@given(
    hrv_rmssd=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    notification_count=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    ambient_noise=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_property_valid_input_acceptance(hrv_rmssd, notification_count, ambient_noise):
    """
    Property 1: Valid input acceptance
    
    For any FocusData payload with valid float values for hrv_rmssd, 
    notification_count, and ambient_noise, the model should accept 
    the input and create a valid FocusData instance.
    
    Validates: Requirements 1.1
    """
    # Create FocusData with valid float inputs
    focus_data = FocusData(
        hrv_rmssd=hrv_rmssd,
        notification_count=notification_count,
        ambient_noise=ambient_noise
    )
    
    # Verify the model accepted the input and stored values correctly
    assert isinstance(focus_data.hrv_rmssd, float)
    assert isinstance(focus_data.notification_count, float)
    assert isinstance(focus_data.ambient_noise, float)
    assert focus_data.hrv_rmssd == hrv_rmssd
    assert focus_data.notification_count == notification_count
    assert focus_data.ambient_noise == ambient_noise


# Property 2: Invalid input rejection
# Feature: flow-state-tax-monitor, Property 2: Invalid input rejection
# Validates: Requirements 1.2
@settings(max_examples=100)
@given(
    data=st.one_of(
        # Missing fields - provide only partial data
        st.fixed_dictionaries({
            'hrv_rmssd': st.floats(allow_nan=False, allow_infinity=False)
        }),
        st.fixed_dictionaries({
            'notification_count': st.floats(allow_nan=False, allow_infinity=False)
        }),
        st.fixed_dictionaries({
            'ambient_noise': st.floats(allow_nan=False, allow_infinity=False)
        }),
        # Wrong types - non-numeric strings that cannot be coerced to floats
        st.fixed_dictionaries({
            'hrv_rmssd': st.text(alphabet=st.characters(blacklist_categories=('Nd',)), min_size=1).filter(lambda x: not x.replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit()),
            'notification_count': st.floats(allow_nan=False, allow_infinity=False),
            'ambient_noise': st.floats(allow_nan=False, allow_infinity=False)
        }),
        st.fixed_dictionaries({
            'hrv_rmssd': st.floats(allow_nan=False, allow_infinity=False),
            'notification_count': st.text(alphabet=st.characters(blacklist_categories=('Nd',)), min_size=1).filter(lambda x: not x.replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit()),
            'ambient_noise': st.floats(allow_nan=False, allow_infinity=False)
        }),
        st.fixed_dictionaries({
            'hrv_rmssd': st.floats(allow_nan=False, allow_infinity=False),
            'notification_count': st.floats(allow_nan=False, allow_infinity=False),
            'ambient_noise': st.text(alphabet=st.characters(blacklist_categories=('Nd',)), min_size=1).filter(lambda x: not x.replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit())
        }),
        # None values
        st.fixed_dictionaries({
            'hrv_rmssd': st.none(),
            'notification_count': st.floats(allow_nan=False, allow_infinity=False),
            'ambient_noise': st.floats(allow_nan=False, allow_infinity=False)
        }),
        # Lists/arrays - truly invalid types
        st.fixed_dictionaries({
            'hrv_rmssd': st.lists(st.integers()),
            'notification_count': st.floats(allow_nan=False, allow_infinity=False),
            'ambient_noise': st.floats(allow_nan=False, allow_infinity=False)
        }),
        # Dictionaries - truly invalid types
        st.fixed_dictionaries({
            'hrv_rmssd': st.floats(allow_nan=False, allow_infinity=False),
            'notification_count': st.dictionaries(st.text(), st.integers()),
            'ambient_noise': st.floats(allow_nan=False, allow_infinity=False)
        }),
    )
)
def test_property_invalid_input_rejection(data):
    """
    Property 2: Invalid input rejection
    
    For any payload with invalid data types (non-float values, missing fields),
    the model should reject the input and raise a ValidationError.
    
    Validates: Requirements 1.2
    """
    # Attempt to create FocusData with invalid input
    with pytest.raises(ValidationError) as exc_info:
        FocusData(**data)
    
    # Verify that a validation error was raised
    assert exc_info.value.errors()
    # Verify that the error contains details about the validation failure
    assert len(exc_info.value.errors()) > 0



# Property 6: FQS output range invariant
# Feature: flow-state-tax-monitor, Property 6: FQS output range invariant
# Validates: Requirements 3.1
@settings(max_examples=100)
@given(
    hrv=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    notifications=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    noise_level=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_property_fqs_output_range_invariant(hrv, notifications, noise_level):
    """
    Property 6: FQS output range invariant
    
    For any combination of HRV, notification count, and noise level inputs
    (regardless of whether they are within expected ranges), the calculated
    FQS should always be a float value between 0 and 100 (inclusive).
    
    Validates: Requirements 3.1
    """
    from main import calculate_fqs
    
    # Calculate FQS with any inputs
    fqs = calculate_fqs(hrv, notifications, noise_level)
    
    # Verify output is a float
    assert isinstance(fqs, float)
    
    # Verify output is within 0-100 range (inclusive)
    assert 0.0 <= fqs <= 100.0



# Property 7: FQS monotonicity with respect to HRV
# Feature: flow-state-tax-monitor, Property 7: FQS monotonicity with respect to HRV
# Validates: Requirements 3.3
@settings(max_examples=100)
@given(
    hrv1=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    hrv2=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    notifications=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    noise_level=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_property_fqs_monotonicity_hrv(hrv1, hrv2, notifications, noise_level):
    """
    Property 7: FQS monotonicity with respect to HRV
    
    For any two HRV values h1 and h2 where h1 < h2, and holding notification
    count and noise level constant, the FQS calculated with h1 should be less
    than or equal to the FQS calculated with h2 (higher HRV should not decrease FQS).
    
    Validates: Requirements 3.3
    """
    from main import calculate_fqs
    
    # Only test when hrv1 < hrv2
    if hrv1 >= hrv2:
        return
    
    # Calculate FQS for both HRV values with same notifications and noise
    fqs1 = calculate_fqs(hrv1, notifications, noise_level)
    fqs2 = calculate_fqs(hrv2, notifications, noise_level)
    
    # Verify monotonicity: higher HRV should yield higher or equal FQS
    assert fqs1 <= fqs2, f"FQS decreased when HRV increased: FQS({hrv1})={fqs1} > FQS({hrv2})={fqs2}"



# Property 8: FQS monotonicity with respect to notifications
# Feature: flow-state-tax-monitor, Property 8: FQS monotonicity with respect to notifications
# Validates: Requirements 3.2
@settings(max_examples=100)
@given(
    hrv=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    notifications1=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    notifications2=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    noise_level=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_property_fqs_monotonicity_notifications(hrv, notifications1, notifications2, noise_level):
    """
    Property 8: FQS monotonicity with respect to notifications
    
    For any two notification count values n1 and n2 where n1 < n2, and holding
    HRV and noise level constant, the FQS calculated with n1 should be greater
    than or equal to the FQS calculated with n2 (more notifications should not increase FQS).
    
    Validates: Requirements 3.2
    """
    from main import calculate_fqs
    
    # Only test when notifications1 < notifications2
    if notifications1 >= notifications2:
        return
    
    # Calculate FQS for both notification values with same HRV and noise
    fqs1 = calculate_fqs(hrv, notifications1, noise_level)
    fqs2 = calculate_fqs(hrv, notifications2, noise_level)
    
    # Verify monotonicity: more notifications should yield lower or equal FQS
    assert fqs1 >= fqs2, f"FQS increased when notifications increased: FQS({notifications1})={fqs1} < FQS({notifications2})={fqs2}"



# Property 9: FQS monotonicity with respect to noise
# Feature: flow-state-tax-monitor, Property 9: FQS monotonicity with respect to noise
# Validates: Requirements 3.4
@settings(max_examples=100)
@given(
    hrv=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    notifications=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    noise1=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    noise2=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_property_fqs_monotonicity_noise(hrv, notifications, noise1, noise2):
    """
    Property 9: FQS monotonicity with respect to noise
    
    For any two noise level values noise1 and noise2 where noise1 < noise2,
    and holding HRV and notification count constant, the FQS calculated with
    noise1 should be greater than or equal to the FQS calculated with noise2
    (higher noise should not increase FQS).
    
    Validates: Requirements 3.4
    """
    from main import calculate_fqs
    
    # Only test when noise1 < noise2
    if noise1 >= noise2:
        return
    
    # Calculate FQS for both noise values with same HRV and notifications
    fqs1 = calculate_fqs(hrv, notifications, noise1)
    fqs2 = calculate_fqs(hrv, notifications, noise2)
    
    # Verify monotonicity: higher noise should yield lower or equal FQS
    assert fqs1 >= fqs2, f"FQS increased when noise increased: FQS({noise1})={fqs1} < FQS({noise2})={fqs2}"



# Unit test for optimal inputs edge case
# Validates: Requirements 3.5
def test_optimal_inputs_yield_high_score():
    """
    Unit test for optimal inputs edge case
    
    Test that optimal inputs (high HRV, zero notifications, low noise)
    yield a score near 100.
    
    Validates: Requirements 3.5
    """
    from main import calculate_fqs
    
    # Optimal conditions: high HRV (100), zero notifications (0), low noise (0)
    fqs = calculate_fqs(hrv=100.0, notifications=0.0, noise_level=0.0)
    
    # Score should be near 100 (allowing for small floating point differences)
    # With optimal inputs: HRV=100 gives 50 points, notifications=0 gives 30 points, noise=0 gives 20 points
    # Total = 100 points
    assert fqs >= 99.0, f"Optimal inputs should yield score near 100, got {fqs}"
    assert fqs <= 100.0, f"Score should not exceed 100, got {fqs}"
    
    # Test another optimal case with HRV at expected max (100)
    fqs2 = calculate_fqs(hrv=100.0, notifications=0.0, noise_level=0.0)
    assert fqs2 == 100.0, f"Perfect optimal inputs should yield exactly 100, got {fqs2}"


# API Endpoint Tests
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json


# Property 3: WebSocket data emission
# Feature: flow-state-tax-monitor, Property 3: WebSocket data emission
# Validates: Requirements 2.1
@settings(max_examples=100)
@given(
    hrv_rmssd=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    notification_count=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    ambient_noise=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_property_websocket_data_emission(hrv_rmssd, notification_count, ambient_noise):
    """
    Property 3: WebSocket data emission
    
    For any valid FocusData received at the /data endpoint, the data should be
    emitted to the /focus_update Socket.IO channel immediately after validation.
    
    Validates: Requirements 2.1
    """
    from main import app, sio
    
    client = TestClient(app)
    
    # Mock the Socket.IO emit method to track calls
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        # Send valid FocusData to the endpoint
        response = client.post(
            "/data",
            json={
                "hrv_rmssd": hrv_rmssd,
                "notification_count": notification_count,
                "ambient_noise": ambient_noise
            }
        )
        
        # Verify the endpoint accepted the data
        assert response.status_code == 200
        
        # Verify Socket.IO emit was called
        mock_emit.assert_called_once()
        
        # Verify emit was called with correct event name and namespace
        call_args = mock_emit.call_args
        assert call_args[0][0] == 'focus_data'  # Event name
        assert call_args[1]['namespace'] == '/focus_update'  # Namespace


# Property 4: Data field preservation
# Feature: flow-state-tax-monitor, Property 4: Data field preservation
# Validates: Requirements 2.3
@settings(max_examples=100)
@given(
    hrv_rmssd=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    notification_count=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    ambient_noise=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_property_data_field_preservation(hrv_rmssd, notification_count, ambient_noise):
    """
    Property 4: Data field preservation
    
    For any FocusData payload received at the /data endpoint, the emitted
    WebSocket message should contain all three original fields (hrv_rmssd,
    notification_count, ambient_noise) with their original values preserved.
    
    Validates: Requirements 2.3
    """
    from main import app, sio
    
    client = TestClient(app)
    
    # Mock the Socket.IO emit method to capture emitted data
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        # Send valid FocusData to the endpoint
        response = client.post(
            "/data",
            json={
                "hrv_rmssd": hrv_rmssd,
                "notification_count": notification_count,
                "ambient_noise": ambient_noise
            }
        )
        
        # Verify the endpoint accepted the data
        assert response.status_code == 200
        
        # Get the emitted data
        call_args = mock_emit.call_args
        emitted_data = call_args[0][1]  # Second positional argument is the data
        
        # Verify all original fields are preserved
        assert 'hrv_rmssd' in emitted_data
        assert 'notification_count' in emitted_data
        assert 'ambient_noise' in emitted_data
        
        # Verify values are preserved
        assert emitted_data['hrv_rmssd'] == hrv_rmssd
        assert emitted_data['notification_count'] == notification_count
        assert emitted_data['ambient_noise'] == ambient_noise
        
        # Verify timestamp was added
        assert 'timestamp' in emitted_data


# Property 5: Broadcast consistency
# Feature: flow-state-tax-monitor, Property 5: Broadcast consistency
# Validates: Requirements 2.4
@settings(max_examples=100)
@given(
    hrv_rmssd=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    notification_count=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    ambient_noise=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_property_broadcast_consistency(hrv_rmssd, notification_count, ambient_noise):
    """
    Property 5: Broadcast consistency
    
    For any focus data emission, all connected Socket.IO clients should receive
    identical data payloads simultaneously. This test verifies that the emit
    call uses broadcast mode (no specific room or sid targeting).
    
    Validates: Requirements 2.4
    """
    from main import app, sio
    
    client = TestClient(app)
    
    # Mock the Socket.IO emit method to verify broadcast behavior
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        # Send valid FocusData to the endpoint
        response = client.post(
            "/data",
            json={
                "hrv_rmssd": hrv_rmssd,
                "notification_count": notification_count,
                "ambient_noise": ambient_noise
            }
        )
        
        # Verify the endpoint accepted the data
        assert response.status_code == 200
        
        # Verify emit was called
        mock_emit.assert_called_once()
        
        # Get the call arguments
        call_args = mock_emit.call_args
        call_kwargs = call_args[1]
        
        # Verify broadcast behavior: no 'room' or 'to' parameter should be specified
        # This ensures all connected clients receive the data
        assert 'room' not in call_kwargs or call_kwargs.get('room') is None
        assert 'to' not in call_kwargs or call_kwargs.get('to') is None
        
        # Verify the data is consistent (same data would be sent to all clients)
        emitted_data = call_args[0][1]
        assert emitted_data['hrv_rmssd'] == hrv_rmssd
        assert emitted_data['notification_count'] == notification_count
        assert emitted_data['ambient_noise'] == ambient_noise


# Unit test for CORS headers
# Validates: Requirements 1.4
def test_cors_headers_present():
    """
    Unit test for CORS headers
    
    Test that CORS headers are present in API responses to allow
    cross-origin requests from the Frontend Dashboard.
    
    Validates: Requirements 1.4
    """
    from main import app
    
    client = TestClient(app)
    
    # Send a request with Origin header to trigger CORS
    response = client.post(
        "/data",
        json={
            "hrv_rmssd": 75.0,
            "notification_count": 2.0,
            "ambient_noise": 5.0
        },
        headers={"Origin": "http://localhost:3000"}
    )
    
    # Verify CORS headers are present
    assert 'access-control-allow-origin' in response.headers
    assert response.headers['access-control-allow-origin'] == '*'
    
    # Test OPTIONS request (preflight) with proper headers
    options_response = client.options(
        "/data",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    assert 'access-control-allow-methods' in options_response.headers
    # Verify methods include POST
    assert 'POST' in options_response.headers['access-control-allow-methods']
