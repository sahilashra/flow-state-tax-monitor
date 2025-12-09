# Requirements Document

## Introduction

The Flow State Tax Monitor is a real-time monitoring system designed to quantify and visualize the cognitive cost of digital distractions. The system correlates digital interruption data (notifications, app switching) with physiological and environmental stress indicators (HRV, ambient noise) to produce a composite Focus Quality Score (FQS). The primary goal is to demonstrate the measurable impact of interruptions on focus quality through a live dashboard that displays real-time data and historical trends.

## Glossary

- **FQS (Focus Quality Score)**: A composite metric ranging from 0 to 100 that represents the current quality of a user's focus state, calculated from HRV, notification count, and ambient noise level
- **Focus Tax**: The quantifiable drop in FQS that occurs when a major interruption event happens
- **HRV (Heart Rate Variability)**: A physiological measure (RMSSD) indicating stress levels, typically ranging from 40-100ms
- **Backend System**: The Python/FastAPI server responsible for data processing, FQS calculation, and real-time streaming
- **Frontend Dashboard**: The React-based web interface that displays real-time FQS data and historical trends
- **Interruption Data**: Digital distraction metrics including notification counts and app switching rates
- **WebSocket Channel**: The Socket.IO communication channel named `/focus_update` used for real-time data streaming

## Requirements

### Requirement 1

**User Story:** As a developer, I want to receive and process focus data through a REST API, so that the system can accept data from multiple sources.

#### Acceptance Criteria

1. WHEN the Backend System receives a POST request at `/data` endpoint with valid FocusData payload, THEN the Backend System SHALL accept and parse the payload containing `hrv_rmssd`, `notification_count`, and `ambient_noise` fields
2. WHEN the Backend System receives a POST request with invalid data types, THEN the Backend System SHALL reject the request and return a validation error response
3. WHEN the Backend System processes a valid FocusData payload, THEN the Backend System SHALL validate that `hrv_rmssd` is a float, `notification_count` is a float, and `ambient_noise` is a float
4. WHEN the Backend System starts, THEN the Backend System SHALL enable CORS headers to allow cross-origin requests from the Frontend Dashboard

### Requirement 2

**User Story:** As a user, I want my focus data to be streamed in real-time to the dashboard, so that I can see immediate feedback on my focus state.

#### Acceptance Criteria

1. WHEN the Backend System receives valid FocusData at the `/data` endpoint, THEN the Backend System SHALL emit the data immediately via Socket.IO to the `/focus_update` channel
2. WHEN the Frontend Dashboard connects to the WebSocket Channel, THEN the Backend System SHALL establish a Socket.IO connection and maintain it for real-time updates
3. WHEN the Backend System emits data to the `/focus_update` channel, THEN the Backend System SHALL include all fields from the original FocusData payload in the emitted message
4. WHEN multiple clients connect to the WebSocket Channel, THEN the Backend System SHALL broadcast focus updates to all connected clients simultaneously

### Requirement 3

**User Story:** As a user, I want the system to calculate a Focus Quality Score from my data, so that I can understand my current focus state with a single metric.

#### Acceptance Criteria

1. WHEN the Backend System calculates FQS with given HRV, notification count, and noise level inputs, THEN the Backend System SHALL return a single float value between 0 and 100
2. WHEN the Backend System calculates FQS with high notification count values, THEN the Backend System SHALL apply a penalty that reduces the FQS proportionally
3. WHEN the Backend System calculates FQS with low HRV values, THEN the Backend System SHALL apply a penalty that reduces the FQS proportionally
4. WHEN the Backend System calculates FQS with high ambient noise values, THEN the Backend System SHALL apply a penalty that reduces the FQS proportionally
5. WHEN the Backend System calculates FQS with optimal inputs (high HRV, zero notifications, low noise), THEN the Backend System SHALL return a score approaching 100

### Requirement 4

**User Story:** As a user, I want to see my Focus Quality Score displayed in real-time on a dashboard, so that I can monitor my focus state continuously.

#### Acceptance Criteria

1. WHEN the Frontend Dashboard initializes, THEN the Frontend Dashboard SHALL establish a Socket.IO connection to the Backend System on the `/focus_update` channel
2. WHEN the Frontend Dashboard receives focus data from the WebSocket Channel, THEN the Frontend Dashboard SHALL calculate the FQS using the received HRV, notification count, and noise level values
3. WHEN the Frontend Dashboard calculates a new FQS value, THEN the Frontend Dashboard SHALL append the score with a timestamp to the `fqsHistory` state array
4. WHEN the `fqsHistory` state updates, THEN the Frontend Dashboard SHALL trigger a re-render to display the updated data
5. WHEN the Frontend Dashboard maintains the `fqsHistory` state, THEN the Frontend Dashboard SHALL store entries as objects containing both timestamp and score fields

### Requirement 5

**User Story:** As a user, I want to see a real-time graph of my Focus Quality Score over time, so that I can visualize trends and identify when interruptions impact my focus.

#### Acceptance Criteria

1. WHEN the Frontend Dashboard renders the chart component, THEN the Frontend Dashboard SHALL display the `fqsHistory` data as a time-series line graph
2. WHEN new FQS data is added to `fqsHistory`, THEN the Frontend Dashboard SHALL update the chart visualization in real-time without full page refresh
3. WHEN the chart displays FQS values, THEN the Frontend Dashboard SHALL show timestamps on the x-axis and FQS scores (0-100) on the y-axis
4. WHEN a Focus Tax event occurs (significant FQS drop), THEN the Frontend Dashboard SHALL visually represent the drop in the chart as a downward trend line

### Requirement 6

**User Story:** As a developer, I want the FQS calculation logic to be transparent and documented, so that I can understand and adjust how each factor contributes to the final score.

#### Acceptance Criteria

1. WHEN the FQS calculation function is implemented, THEN the Backend System SHALL include inline comments explaining the contribution percentage of each input factor
2. WHEN the FQS calculation processes HRV input, THEN the Backend System SHALL document that HRV contributes a specific weighted percentage to the final score
3. WHEN the FQS calculation processes notification count input, THEN the Backend System SHALL document that notifications contribute a specific weighted percentage to the final score
4. WHEN the FQS calculation processes ambient noise input, THEN the Backend System SHALL document that noise level contributes a specific weighted percentage to the final score
5. WHEN the FQS calculation normalizes inputs, THEN the Backend System SHALL document the expected input ranges (HRV: 40-100, Notifications: 0-5, Noise: 0-10)
