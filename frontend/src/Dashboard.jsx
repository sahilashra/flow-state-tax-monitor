import { useState, useEffect } from 'react';
import io from 'socket.io-client';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

// Get backend URL from environment variable
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

/**
 * Calculate Focus Quality Score (FQS) from physiological and environmental metrics.
 * 
 * The FQS is a composite score ranging from 0-100 that represents focus quality.
 * Higher scores indicate better focus conditions.
 * 
 * Algorithm matches backend implementation:
 * - HRV contributes 50% of the score (higher is better)
 * - Notifications contribute 30% penalty (more is worse)
 * - Noise contributes 20% penalty (higher is worse)
 * 
 * @param {number} hrv - Heart Rate Variability in milliseconds (expected range: 40-100)
 * @param {number} notifications - Number of notifications (expected range: 0-5)
 * @param {number} noise - Ambient noise level (expected range: 0-10)
 * @returns {number} FQS score clamped to 0-100 range
 */
function calculateFQS(hrv, notifications, noise) {
  // HRV Component (50% weight)
  // Higher HRV indicates better focus
  // Normalize HRV from expected range 40-100 to 0-1, then scale to 50 points
  const hrvNormalized = (hrv - 40) / 60; // Maps 40-100 to 0-1
  const hrvScore = hrvNormalized * 50; // 50% contribution
  
  // Notification Component (30% weight)
  // More notifications reduce focus
  // Normalize from expected range 0-5 (inverse relationship)
  const notificationNormalized = notifications / 5; // Maps 0-5 to 0-1
  const notificationScore = (1 - notificationNormalized) * 30; // 30% contribution (inverted)
  
  // Noise Component (20% weight)
  // Higher noise reduces focus
  // Normalize from expected range 0-10 (inverse relationship)
  const noiseNormalized = noise / 10; // Maps 0-10 to 0-1
  const noiseScore = (1 - noiseNormalized) * 20; // 20% contribution (inverted)
  
  // Calculate total FQS
  let fqs = hrvScore + notificationScore + noiseScore;
  
  // Clamp output to 0-100 range
  fqs = Math.max(0, Math.min(100, fqs));
  
  return fqs;
}

function Dashboard() {
  const [fqsHistory, setFqsHistory] = useState([]);
  const [currentFQS, setCurrentFQS] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [errorMessage, setErrorMessage] = useState(null);
  const [currentMetrics, setCurrentMetrics] = useState({
    hrv: null,
    notifications: null,
    noise: null
  });
  const [statistics, setStatistics] = useState({
    avgFQS: null,
    minFQS: null,
    maxFQS: null,
    focusTaxEvents: 0
  });

  // Initialize Socket.IO connection on component mount
  useEffect(() => {
    // Create Socket.IO client instance with backend URL
    // Connect to /focus_update namespace to receive focus_data events
    const socketInstance = io(BACKEND_URL + '/focus_update', {
      // Configure websocket transport
      transports: ['websocket'],
      // Configure reconnection settings
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity
    });

    // Set up connection status handling
    socketInstance.on('connect', () => {
      console.log('Connected to backend:', socketInstance.id);
      setConnectionStatus('connected');
    });

    socketInstance.on('disconnect', () => {
      console.log('Disconnected from backend');
      setConnectionStatus('disconnected');
    });

    socketInstance.on('connect_error', (error) => {
      console.error('Connection error:', error);
      setConnectionStatus('error');
    });

    socketInstance.on('reconnect', (attemptNumber) => {
      console.log('Reconnected after', attemptNumber, 'attempts');
      setConnectionStatus('connected');
    });

    socketInstance.on('reconnecting', (attemptNumber) => {
      console.log('Reconnecting... attempt', attemptNumber);
      setConnectionStatus('reconnecting');
    });

    // Set up Socket.IO event listener for 'focus_data' events
    socketInstance.on('focus_data', (data) => {
      console.log('Received focus data:', data);
      
      // Handle missing or invalid data from WebSocket gracefully
      try {
        // Validate that required fields are present and are numbers
        if (!data || 
            typeof data.hrv_rmssd !== 'number' || 
            typeof data.notification_count !== 'number' || 
            typeof data.ambient_noise !== 'number') {
          console.error('Invalid data received:', data);
          setErrorMessage('Received invalid data from server. Some fields may be missing or incorrect.');
          return;
        }
        
        // Check for NaN or Infinity values
        if (!isFinite(data.hrv_rmssd) || 
            !isFinite(data.notification_count) || 
            !isFinite(data.ambient_noise)) {
          console.error('Invalid numeric values received:', data);
          setErrorMessage('Received invalid numeric values from server.');
          return;
        }
        
        // Clear any previous error messages
        setErrorMessage(null);
        
        // Calculate FQS from received data
        const fqs = calculateFQS(
          data.hrv_rmssd,
          data.notification_count,
          data.ambient_noise
        );
        
        // Update current FQS display
        setCurrentFQS(fqs);
        
        // Update current metrics
        setCurrentMetrics({
          hrv: data.hrv_rmssd,
          notifications: data.notification_count,
          noise: data.ambient_noise
        });
        
        // Create new entry with timestamp and score
        const newEntry = {
          timestamp: data.timestamp || new Date().toISOString(),
          score: fqs,
          hrv: data.hrv_rmssd,
          notifications: data.notification_count,
          noise: data.ambient_noise
        };
        
        // Append new entry to fqsHistory and limit to last 1000 entries
        setFqsHistory(prevHistory => {
          const updatedHistory = [...prevHistory, newEntry];
          // Limit history size to last 1000 entries to prevent memory issues
          if (updatedHistory.length > 1000) {
            return updatedHistory.slice(-1000);
          }
          
          // Calculate statistics
          if (updatedHistory.length > 0) {
            const scores = updatedHistory.map(e => e.score);
            const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
            const min = Math.min(...scores);
            const max = Math.max(...scores);
            
            // Detect "Focus Tax" events (drops of 15+ points)
            let taxEvents = 0;
            for (let i = 1; i < updatedHistory.length; i++) {
              if (updatedHistory[i-1].score - updatedHistory[i].score >= 15) {
                taxEvents++;
              }
            }
            
            setStatistics({
              avgFQS: avg,
              minFQS: min,
              maxFQS: max,
              focusTaxEvents: taxEvents
            });
          }
          
          return updatedHistory;
        });
      } catch (error) {
        console.error('Error processing focus data:', error);
        setErrorMessage(`Error processing data: ${error.message}`);
      }
    });

    // Cleanup on component unmount
    return () => {
      socketInstance.disconnect();
    };
  }, []);

  // Helper function to get connection status display text
  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      case 'connecting':
        return 'Connecting...';
      case 'reconnecting':
        return 'Reconnecting...';
      case 'error':
        return 'Connection Error';
      default:
        return connectionStatus;
    }
  };

  return (
    <div className="dashboard">
      <header>
        <h1>Flow State Tax Monitor</h1>
        <div className={`connection-status status-${connectionStatus}`}>
          <span className="status-indicator"></span>
          <span className="status-text">{getConnectionStatusText()}</span>
        </div>
      </header>
      
      <main>
        {/* Display error messages to user when appropriate */}
        {errorMessage && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <span className="error-text">{errorMessage}</span>
            <button 
              className="error-dismiss" 
              onClick={() => setErrorMessage(null)}
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

        <div className="metrics-grid">
          {/* Main FQS Score */}
          <div className="metric-card main-score">
            <h2>Current Focus Quality Score</h2>
            <div className="score-display">
              {currentFQS !== null ? currentFQS.toFixed(1) : '--'}
            </div>
            {currentFQS !== null && (
              <div className="score-description">
                {currentFQS >= 80 ? '🟢 Excellent Focus' :
                 currentFQS >= 60 ? '🟡 Good Focus' :
                 currentFQS >= 40 ? '🟠 Moderate Focus' :
                 '🔴 Poor Focus'}
              </div>
            )}
          </div>

          {/* Individual Metrics */}
          <div className="metric-card">
            <h3>❤️ Heart Rate Variability</h3>
            <div className="metric-value">
              {currentMetrics.hrv !== null ? currentMetrics.hrv.toFixed(1) : '--'}
              <span className="metric-unit">ms</span>
            </div>
            <div className="metric-label">RMSSD</div>
            <div className="metric-contribution">50% of FQS</div>
          </div>

          <div className="metric-card">
            <h3>🔔 Notifications</h3>
            <div className="metric-value">
              {currentMetrics.notifications !== null ? currentMetrics.notifications.toFixed(1) : '--'}
            </div>
            <div className="metric-label">Last 5 minutes</div>
            <div className="metric-contribution">30% of FQS</div>
          </div>

          <div className="metric-card">
            <h3>🔊 Ambient Noise</h3>
            <div className="metric-value">
              {currentMetrics.noise !== null ? currentMetrics.noise.toFixed(1) : '--'}
              <span className="metric-unit">/10</span>
            </div>
            <div className="metric-label">Noise Level</div>
            <div className="metric-contribution">20% of FQS</div>
          </div>
        </div>

        {/* Statistics Cards */}
        {fqsHistory.length > 0 && (
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">📊</div>
              <div className="stat-value">{statistics.avgFQS !== null ? statistics.avgFQS.toFixed(1) : '--'}</div>
              <div className="stat-label">Average FQS</div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">📈</div>
              <div className="stat-value">{statistics.maxFQS !== null ? statistics.maxFQS.toFixed(1) : '--'}</div>
              <div className="stat-label">Peak Focus</div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">📉</div>
              <div className="stat-value">{statistics.minFQS !== null ? statistics.minFQS.toFixed(1) : '--'}</div>
              <div className="stat-label">Lowest Focus</div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">⚠️</div>
              <div className="stat-value">{statistics.focusTaxEvents}</div>
              <div className="stat-label">Focus Tax Events</div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">📝</div>
              <div className="stat-value">{fqsHistory.length}</div>
              <div className="stat-label">Data Points</div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">⏱️</div>
              <div className="stat-value">
                {fqsHistory.length > 0 ? 
                  Math.floor((new Date(fqsHistory[fqsHistory.length - 1].timestamp) - new Date(fqsHistory[0].timestamp)) / 60000) 
                  : 0}
              </div>
              <div className="stat-label">Minutes Tracked</div>
            </div>
          </div>
        )}

        <div className="chart-container">
          <h2>FQS History</h2>
          {fqsHistory.length === 0 ? (
            <div className="placeholder">
              <p>Waiting for data...</p>
              {connectionStatus === 'connected' && (
                <p className="placeholder-hint">Connected to server. Data will appear here once received.</p>
              )}
              {connectionStatus === 'disconnected' && (
                <p className="placeholder-hint">Disconnected from server. Attempting to reconnect...</p>
              )}
            </div>
          ) : (
            <Line 
              data={{
                labels: fqsHistory.map(entry => {
                  // Format timestamp for display
                  const date = new Date(entry.timestamp);
                  return date.toLocaleTimeString();
                }),
                datasets: [{
                  label: 'Focus Quality Score',
                  data: fqsHistory.map(entry => entry.score),
                  borderColor: 'rgb(75, 192, 192)',
                  backgroundColor: 'rgba(75, 192, 192, 0.2)',
                  tension: 0.1,
                  fill: true,
                  pointRadius: 3,
                  pointHoverRadius: 5,
                  borderWidth: 2
                }]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                  duration: 750,
                  easing: 'easeInOutQuart'
                },
                scales: {
                  x: {
                    title: {
                      display: true,
                      text: 'Time',
                      font: {
                        size: 14,
                        weight: 'bold'
                      }
                    },
                    ticks: {
                      maxRotation: 45,
                      minRotation: 45
                    }
                  },
                  y: {
                    title: {
                      display: true,
                      text: 'FQS Score',
                      font: {
                        size: 14,
                        weight: 'bold'
                      }
                    },
                    min: 0,
                    max: 100,
                    ticks: {
                      stepSize: 10
                    }
                  }
                },
                plugins: {
                  legend: {
                    display: true,
                    position: 'top'
                  },
                  tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                      label: function(context) {
                        const entry = fqsHistory[context.dataIndex];
                        return [
                          `FQS: ${entry.score.toFixed(1)}`,
                          `HRV: ${entry.hrv.toFixed(1)}`,
                          `Notifications: ${entry.notifications.toFixed(1)}`,
                          `Noise: ${entry.noise.toFixed(1)}`
                        ];
                      }
                    }
                  }
                }
              }}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
