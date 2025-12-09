# Flow State Tax Monitor - Frontend

React-based dashboard for the Flow State Tax Monitor application. This frontend connects to the backend via WebSocket to receive real-time focus data and displays Focus Quality Scores (FQS) in an interactive time-series chart.

## Features

- **Real-time Updates**: WebSocket connection for live data streaming
- **Interactive Chart**: Time-series visualization using Chart.js
- **Connection Status**: Visual indicator for WebSocket connection state
- **Error Handling**: Graceful handling of connection issues and invalid data
- **Responsive Design**: Works on desktop and mobile devices
- **History Management**: Maintains last 1000 FQS entries to prevent memory issues

## Prerequisites

- Node.js 16 or higher
- npm or yarn package manager
- Backend server running (see [backend README](../backend/README.md))

## Installation

1. Install dependencies:
```bash
npm install
```

Or with yarn:
```bash
yarn install
```

## Configuration

Create a `.env` file:
```bash
cp .env.example .env
```

Environment variables:
```bash
# Backend API URL
VITE_BACKEND_URL=http://localhost:8000
```

Update `VITE_BACKEND_URL` if your backend is running on a different host or port.

## Running the Application

### Development Mode
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Production Build
```bash
npm run build
```

Build output will be in the `dist/` directory.

### Preview Production Build
```bash
npm run preview
```

## Application Structure

```
frontend/
├── src/
│   ├── Dashboard.jsx         # Main dashboard component
│   ├── App.jsx              # Root application component
│   ├── App.css              # Application styles
│   ├── index.css            # Global styles
│   └── main.jsx             # Application entry point
├── public/                  # Static assets
├── package.json             # Dependencies and scripts
├── vite.config.js           # Vite configuration
├── .env.example            # Environment variable template
└── README.md               # This file
```

## Components

### Dashboard Component

The main dashboard component (`Dashboard.jsx`) handles:

- **Socket.IO Connection**: Establishes and maintains WebSocket connection
- **FQS Calculation**: Computes Focus Quality Score from received data
- **State Management**: Maintains history of FQS entries
- **Chart Rendering**: Displays time-series visualization
- **Error Handling**: Manages connection errors and invalid data

### FQS Calculation

The frontend calculates FQS using the same algorithm as the backend:

```javascript
function calculateFQS(hrv, notifications, noise) {
  // HRV Component (50% weight) - higher is better
  const hrvScore = ((hrv - 40) / 60) * 50;
  
  // Notification Component (30% weight) - lower is better
  const notificationScore = (1 - notifications / 5) * 30;
  
  // Noise Component (20% weight) - lower is better
  const noiseScore = (1 - noise / 10) * 20;
  
  // Total FQS (clamped to 0-100)
  const fqs = Math.max(0, Math.min(100, hrvScore + notificationScore + noiseScore));
  return fqs;
}
```

## WebSocket Connection

The application connects to the backend Socket.IO server:

```javascript
const socket = io('http://localhost:8000', {
  transports: ['websocket'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: Infinity
});

socket.on('focus_data', (data) => {
  // Process received focus data
  const fqs = calculateFQS(data.hrv_rmssd, data.notification_count, data.ambient_noise);
  // Update state and chart
});
```

## Chart Configuration

The dashboard uses Chart.js for visualization:

- **Chart Type**: Line chart
- **X-axis**: Time (timestamps)
- **Y-axis**: FQS Score (0-100)
- **Features**:
  - Smooth animations
  - Hover tooltips with detailed data
  - Responsive sizing
  - Real-time updates

## Connection States

The dashboard displays different connection states:

- **Connecting**: Initial connection attempt
- **Connected**: Successfully connected to backend
- **Disconnected**: Connection lost
- **Reconnecting**: Attempting to reconnect
- **Error**: Connection error occurred

## Error Handling

The application handles various error scenarios:

- **Invalid Data**: Validates received data before processing
- **Connection Errors**: Automatic reconnection with exponential backoff
- **Missing Fields**: Gracefully handles incomplete data
- **NaN/Infinity Values**: Filters out invalid numeric values

## Styling

The application uses CSS for styling with:

- Modern, clean design
- Responsive layout
- Color-coded connection status
- Smooth transitions and animations
- Accessible color contrast

## Dependencies

### Core Dependencies
- **react**: UI library
- **react-dom**: React DOM renderer
- **socket.io-client**: WebSocket client for real-time communication
- **chart.js**: Charting library
- **react-chartjs-2**: React wrapper for Chart.js

### Development Dependencies
- **vite**: Build tool and dev server
- **@vitejs/plugin-react**: React plugin for Vite
- **eslint**: Code linting
- **eslint-plugin-react-hooks**: React Hooks linting rules

## Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run preview`: Preview production build
- `npm run lint`: Run ESLint

## Troubleshooting

### Cannot connect to backend

**Issue**: Dashboard shows "Disconnected" or "Connection Error"

**Solutions**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `VITE_BACKEND_URL` in `.env` file
3. Ensure CORS is configured correctly in backend
4. Check browser console for error messages

### Chart not updating

**Issue**: Chart displays but doesn't update with new data

**Solutions**:
1. Check Socket.IO connection status in dashboard
2. Verify demo data generator is running
3. Check browser console for JavaScript errors
4. Ensure backend is emitting data on `/focus_update` namespace

### Build errors

**Issue**: `npm run build` fails

**Solutions**:
1. Delete `node_modules` and reinstall:
   ```bash
   rm -rf node_modules
   npm install
   ```
2. Clear Vite cache:
   ```bash
   rm -rf node_modules/.vite
   ```
3. Update dependencies:
   ```bash
   npm update
   ```

### Port already in use

**Issue**: Port 5173 is already in use

**Solution**: Specify a different port:
```bash
npm run dev -- --port 3000
```

## Browser Compatibility

The application works in modern browsers that support:
- ES6+ JavaScript
- WebSocket API
- CSS Grid and Flexbox

Tested browsers:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Considerations

- **History Limit**: FQS history is limited to 1000 entries to prevent memory growth
- **Chart Updates**: Chart.js efficiently handles real-time updates
- **WebSocket**: Reduces overhead compared to HTTP polling
- **Lazy Loading**: Components load on demand

## Development Tips

### Hot Module Replacement (HMR)

Vite provides fast HMR for instant feedback during development. Changes to React components will update without full page reload.

### Debugging WebSocket

Use browser DevTools to inspect WebSocket messages:
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by WS (WebSocket)
4. Click on the WebSocket connection to see messages

### React DevTools

Install React DevTools browser extension for component inspection and profiling.

## Related Documentation

- [Main README](../README.md) - Project overview and full setup guide
- [Backend README](../backend/README.md) - Backend API documentation
- [Requirements](../.kiro/specs/flow-state-tax-monitor/requirements.md) - Feature requirements
- [Design](../.kiro/specs/flow-state-tax-monitor/design.md) - System architecture

## Technology Stack

- **React 18+**: Modern React with Hooks
- **Vite**: Next-generation frontend tooling
- **Socket.IO Client**: Real-time bidirectional communication
- **Chart.js**: Simple yet flexible JavaScript charting
- **ES6+ JavaScript**: Modern JavaScript features
