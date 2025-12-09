# Implementation Plan

- [x] 1. Set up backend project structure and dependencies
  - Create Python project directory with main application file
  - Install FastAPI, python-socketio, uvicorn, pydantic, and python-dotenv
  - Configure CORS middleware for development
  - Set up basic FastAPI application with health check endpoint
  - _Requirements: 1.4_

- [x] 2. Implement FocusData model and validation
  - Create Pydantic model for FocusData with three float fields: hrv_rmssd, notification_count, ambient_noise
  - Add field validation to ensure all fields are required floats
  - _Requirements: 1.1, 1.3_

- [x] 2.1 Write property test for FocusData validation
  - **Property 1: Valid input acceptance**
  - **Validates: Requirements 1.1**

- [x] 2.2 Write property test for invalid input rejection
  - **Property 2: Invalid input rejection**
  - **Validates: Requirements 1.2**

- [x] 3. Implement FQS calculation function
  - Create calculate_fqs function that takes hrv, notifications, and noise_level as parameters
  - Implement normalization logic for each input according to the data normalization table
  - Apply weighted scoring: HRV (50%), Notifications (30%), Noise (20%)
  - Clamp output to 0-100 range
  - Add inline comments documenting each factor's contribution percentage
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 3.1 Write property test for FQS output range invariant
  - **Property 6: FQS output range invariant**
  - **Validates: Requirements 3.1**

- [x] 3.2 Write property test for FQS monotonicity with HRV
  - **Property 7: FQS monotonicity with respect to HRV**
  - **Validates: Requirements 3.3**

- [x] 3.3 Write property test for FQS monotonicity with notifications
  - **Property 8: FQS monotonicity with respect to notifications**
  - **Validates: Requirements 3.2**

- [x] 3.4 Write property test for FQS monotonicity with noise
  - **Property 9: FQS monotonicity with respect to noise**
  - **Validates: Requirements 3.4**

- [x] 3.5 Write unit test for optimal inputs edge case
  - Test that optimal inputs (high HRV, zero notifications, low noise) yield score near 100
  - _Requirements: 3.5_

- [x] 4. Implement POST /data endpoint with Socket.IO integration
  - Create POST endpoint that accepts FocusData payload
  - Validate incoming data using Pydantic model
  - Add timestamp to the data payload (ISO 8601 format)
  - Emit validated data to Socket.IO /focus_update channel using 'focus_data' event
  - Return success response with status message
  - Handle validation errors with appropriate error responses
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3_

- [x] 4.1 Write property test for WebSocket data emission
  - **Property 3: WebSocket data emission**
  - **Validates: Requirements 2.1**

- [x] 4.2 Write property test for data field preservation
  - **Property 4: Data field preservation**
  - **Validates: Requirements 2.3**

- [x] 4.3 Write property test for broadcast consistency
  - **Property 5: Broadcast consistency**
  - **Validates: Requirements 2.4**

- [x] 4.4 Write unit test for CORS headers
  - Test that CORS headers are present in API responses
  - _Requirements: 1.4_

- [x] 5. Checkpoint - Ensure backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Set up frontend project structure
  - Create React application using Vite
  - Install dependencies: socket.io-client, chart.js, react-chartjs-2
  - Set up basic component structure (App.jsx, Dashboard component)
  - Configure environment variables for backend URL
  - _Requirements: 4.1_

- [x] 7. Implement Socket.IO client connection and FQS calculation
  - Create Socket.IO client instance with backend URL
  - Configure websocket transport and reconnection settings
  - Initialize connection on component mount
  - Set up connection status handling
  - Create calculateFQS function matching backend algorithm
  - Implement same normalization and weighting logic
  - Clamp output to 0-100 range
  - _Requirements: 4.1, 4.2, 2.2_

- [ ]* 7.1 Write property test for frontend FQS calculation consistency
  - **Property 10: Frontend FQS calculation consistency**
  - **Validates: Requirements 4.2**

- [x] 8. Implement fqsHistory state management
  - Create React state for fqsHistory array
  - Implement Socket.IO event listener for 'focus_data' events
  - Calculate FQS from received data
  - Append new entry with timestamp and score to fqsHistory
  - Limit history size to last 1000 entries to prevent memory issues
  - _Requirements: 4.2, 4.3, 4.5_

- [ ]* 8.1 Write property test for history state growth
  - **Property 11: History state growth**
  - **Validates: Requirements 4.3**

- [ ]* 8.2 Write property test for history entry structure
  - **Property 12: History entry structure**
  - **Validates: Requirements 4.5**

- [x] 9. Implement Chart.js visualization component
  - Create chart component using react-chartjs-2
  - Configure line chart with time-series data
  - Set x-axis to display timestamps
  - Set y-axis to display FQS scores (0-100 range)
  - Pass fqsHistory data to chart
  - Configure chart styling and animations
  - Make chart responsive
  - _Requirements: 5.1, 5.3_

- [x] 10. Implement dashboard layout and styling
  - Create main dashboard component
  - Add header with title "Flow State Tax Monitor"
  - Display current FQS score prominently
  - Display real-time chart
  - Add connection status indicator
  - Apply responsive styling
  - Handle empty fqsHistory state (show placeholder message)
  - Handle Socket.IO connection errors with reconnection logic
  - Handle missing or invalid data from WebSocket gracefully
  - Display error messages to user when appropriate
  - _Requirements: 5.1, 5.2, 5.4, 2.2_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Create demo data generator script
  - Create Python script to simulate focus data
  - Generate realistic HRV values (40-100 range)
  - Generate notification events (0-5 range)
  - Generate ambient noise levels (0-10 range)
  - Send data to backend /data endpoint at regular intervals
  - Include "Focus Tax" event simulation (spike in notifications causing FQS drop)
  - _Requirements: All (for demonstration purposes)_

- [x] 13. Create README with setup and usage instructions
  - Document backend setup and installation steps
  - Document frontend setup and installation steps
  - Document how to run the demo
  - Include architecture diagram
  - Document API endpoints
  - Document WebSocket events
  - Include example payloads
  - _Requirements: All (documentation)_


## Real Data Integration

- [x] 14. Implement ambient noise collector
  - Create Python script to capture ambient noise from system microphone
  - Use pyaudio library to access microphone input
  - Calculate RMS (Root Mean Square) amplitude from audio samples
  - Normalize audio level to 0-10 scale (0 = silent, 10 = very loud)
  - Send noise level data to backend /data endpoint at regular intervals (every 5 seconds)
  - Handle microphone access errors gracefully
  - Add configuration for microphone device selection
  - _Requirements: 1.1, 3.4_

- [x] 15. Implement Windows notification counter
  - Create Python script to monitor Windows notification center
  - Use Windows API (win32gui/win32con) to track notification events
  - Count notifications in rolling 5-minute window
  - Normalize count to 0-5 scale for API compatibility
  - Send notification count to backend /data endpoint at regular intervals
  - Handle Windows API access errors gracefully
  - Add option to filter notification types (system vs app notifications)
  - _Requirements: 1.1, 3.2_

- [ ]* 15.1 Implement macOS notification counter (alternative)
  - Create Python script using AppleScript to monitor macOS notifications
  - Track notification events from Notification Center
  - Count notifications in rolling 5-minute window
  - Normalize count to 0-5 scale
  - Send data to backend endpoint
  - _Requirements: 1.1, 3.2_

- [ ]* 15.2 Implement Linux notification counter (alternative)
  - Create Python script using D-Bus to monitor Linux notifications
  - Track notification events from desktop environment
  - Count notifications in rolling 5-minute window
  - Normalize count to 0-5 scale
  - Send data to backend endpoint
  - _Requirements: 1.1, 3.2_

- [x] 16. Implement HRV data collector with fitness tracker integration
  - Research and select HRV data source (Fitbit, Apple Health, Garmin, etc.)
  - Create Python script to authenticate with chosen fitness API
  - Fetch latest HRV (RMSSD) data from API
  - Handle API rate limits and authentication token refresh
  - Cache HRV data locally to minimize API calls
  - Send HRV data to backend /data endpoint when new data is available
  - Add fallback to simulated data if API is unavailable
  - Document API setup and authentication requirements
  - _Requirements: 1.1, 3.3_

- [x] 16.1 Add support for multiple HRV sources










  - Implement adapter pattern for different fitness APIs
  - Support Fitbit API integration
  - Support Apple HealthKit integration (requires macOS/iOS)
  - Support Garmin Connect API integration
  - Support Oura Ring API integration
  - Allow user to configure preferred data source
  - _Requirements: 1.1, 3.3_

- [x] 17. Create unified real data collector orchestrator




  - Create main Python script that runs all data collectors concurrently
  - Use threading or asyncio to run collectors in parallel
  - Aggregate data from all three sources (HRV, notifications, noise)
  - Send combined data payload to backend /data endpoint
  - Implement graceful degradation if one collector fails
  - Add logging for debugging collector issues
  - Add configuration file for collector settings (intervals, thresholds, etc.)
  - Create systemd service file (Linux) or Task Scheduler config (Windows) for auto-start
  - _Requirements: 1.1, 2.1_

- [ ]* 17.1 Add data validation and smoothing
  - Implement outlier detection for sensor readings
  - Apply moving average filter to reduce noise in data
  - Validate data ranges before sending to backend
  - Log anomalous readings for debugging
  - _Requirements: 1.2, 1.3_

- [x] 18. Update documentation for real data integration




  - Document how to set up each data collector
  - Add instructions for obtaining API keys for fitness trackers
  - Document microphone permissions setup for each OS
  - Add troubleshooting guide for common collector issues
  - Update README with real data collection architecture diagram
  - Document how to switch between demo and real data modes
  - _Requirements: All (documentation)_

- [x] 19. Checkpoint - Test real data integration end-to-end




  - Verify ambient noise collector captures and sends data correctly
  - Verify notification counter tracks and sends data correctly
  - Verify HRV collector fetches and sends data correctly
  - Verify all data appears correctly in dashboard
  - Verify FQS calculations are accurate with real data
  - Test graceful degradation when collectors fails
  - Ensure all tests pass, ask the user if questions arise.

