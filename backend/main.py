"""
Flow State Tax Monitor - Backend API
Main application file for the FastAPI server with Socket.IO integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import socketio

# Create FastAPI application
app = FastAPI(
    title="Flow State Tax Monitor",
    description="Real-time monitoring system for focus quality metrics",
    version="1.0.0"
)

# Configure CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

# Wrap FastAPI app with Socket.IO
socket_app = socketio.ASGIApp(sio, app)


# Data Models
class FocusData(BaseModel):
    """
    Focus data model containing physiological and environmental metrics.
    
    All fields are required floats representing:
    - hrv_rmssd: Heart Rate Variability in milliseconds (expected range: 40-100)
    - notification_count: Number of notifications (expected range: 0-5)
    - ambient_noise: Ambient noise level (expected range: 0-10)
    """
    hrv_rmssd: float
    notification_count: float
    ambient_noise: float


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Flow State Tax Monitor API"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Flow State Tax Monitor",
        "version": "1.0.0"
    }


@app.post("/data")
async def receive_focus_data(focus_data: FocusData):
    """
    Receive focus data and broadcast to connected clients via Socket.IO.
    
    Args:
        focus_data: FocusData payload containing hrv_rmssd, notification_count, and ambient_noise
    
    Returns:
        Success response with status message
    
    Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.3
    """
    from datetime import datetime
    
    # Add timestamp to the data payload (ISO 8601 format)
    data_with_timestamp = {
        "hrv_rmssd": focus_data.hrv_rmssd,
        "notification_count": focus_data.notification_count,
        "ambient_noise": focus_data.ambient_noise,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Emit validated data to Socket.IO /focus_update channel using 'focus_data' event
    await sio.emit('focus_data', data_with_timestamp, namespace='/focus_update')
    
    # Return success response with status message
    return {
        "status": "success",
        "message": "Data received and broadcasted"
    }


# Socket.IO event handlers for /focus_update namespace
@sio.event(namespace='/focus_update')
async def connect(sid, environ):
    """Handle client connection to /focus_update namespace"""
    print(f"Client connected to /focus_update: {sid}")


@sio.event(namespace='/focus_update')
async def disconnect(sid):
    """Handle client disconnection from /focus_update namespace"""
    print(f"Client disconnected from /focus_update: {sid}")


# FQS Calculation Function
def calculate_fqs(hrv: float, notifications: float, noise_level: float) -> float:
    """
    Calculate Focus Quality Score (FQS) from physiological and environmental metrics.
    
    The FQS is a composite score ranging from 0-100 that represents focus quality.
    Higher scores indicate better focus conditions.
    
    Args:
        hrv: Heart Rate Variability in milliseconds (expected range: 40-100)
        notifications: Number of notifications (expected range: 0-5)
        noise_level: Ambient noise level (expected range: 0-10)
    
    Returns:
        float: FQS score clamped to 0-100 range
    
    Algorithm:
        - HRV contributes 50% of the score (higher is better)
        - Notifications contribute 30% penalty (more is worse)
        - Noise contributes 20% penalty (higher is worse)
    """
    # HRV Component (50% weight)
    # Higher HRV indicates better focus
    # Normalize HRV from expected range 40-100 to 0-1, then scale to 50 points
    hrv_normalized = (hrv - 40) / 60  # Maps 40-100 to 0-1
    hrv_score = hrv_normalized * 50  # 50% contribution
    
    # Notification Component (30% weight)
    # More notifications reduce focus
    # Normalize from expected range 0-5 (inverse relationship)
    notification_normalized = notifications / 5  # Maps 0-5 to 0-1
    notification_score = (1 - notification_normalized) * 30  # 30% contribution (inverted)
    
    # Noise Component (20% weight)
    # Higher noise reduces focus
    # Normalize from expected range 0-10 (inverse relationship)
    noise_normalized = noise_level / 10  # Maps 0-10 to 0-1
    noise_score = (1 - noise_normalized) * 20  # 20% contribution (inverted)
    
    # Calculate total FQS
    fqs = hrv_score + notification_score + noise_score
    
    # Clamp output to 0-100 range
    fqs = max(0.0, min(100.0, fqs))
    
    return fqs
