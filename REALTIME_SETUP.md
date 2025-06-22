# Real-Time Basketball Analysis Setup Guide

This guide will help you set up the real-time basketball analysis system that connects your frontend webcam directly to the existing `person_ball_detection.py` file.

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- A webcam for live video capture
- Basketball and YOLO pose detection models (included in the project)

## Backend Setup

### 1. Install Python Dependencies

Navigate to the backend directory and install the required packages:

```bash
cd backend
pip3 install -r requirements.txt
```

### 2. Verify Model Files

Make sure the following model files are present in the `backend/opencv-test/` directory:
- `basketballmodel.pt` - Basketball detection model
- `yolov8s-pose.pt` - Human pose detection model

### 3. Start the Backend Servers

You need to run two servers:

#### Terminal 1 - Flask Authentication Server:
```bash
cd backend
python3 start_flask_server.py
```

#### Terminal 2 - OpenCV Analysis Server:
```bash
cd backend
python3 start_opencv_server.py
```

You should see output like:
```
INFO - Starting Flask Authentication Server...
INFO - Server will be available at http://localhost:5002
INFO - Starting OpenCV Basketball Analysis Server...
INFO - Server will be available at ws://localhost:8765
INFO - This server integrates with person_ball_detection.py
```

## Frontend Setup

### 1. Install Frontend Dependencies

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm install
```

### 2. Start the Frontend Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Complete System Architecture

```
Frontend (React + TypeScript) - Port 5173
    ↓ HTTP Requests (Authentication)
Flask Server (Authentication) - Port 5002
    ↓ WebSocket Connection (Real-time)
OpenCV Server (person_ball_detection.py) - Port 8765
    ↓ YOLO Models
Basketball & Pose Detection Models
```

## How It Works

1. **Frontend Webcam**: Captures live video frames from your webcam
2. **Frame Transmission**: Frames are sent via WebSocket to the OpenCV server
3. **person_ball_detection.py Integration**: The server uses your existing detection logic
4. **Real-time Analysis**: Basketball events, violations, and player tracking are detected
5. **Live Feedback**: Results are sent back to the frontend for display

## Usage

### 1. Access the Application

1. Open your browser and go to `http://localhost:5173`
2. Sign up or log in using the authentication system
3. Navigate to the Webcam Analysis page
4. Click "Start Recording" to begin live analysis

### 2. Real-Time Analysis Features

The system provides real-time analysis using your existing `person_ball_detection.py` logic:
- **Ball Detection**: Identifies basketballs in the video feed
- **Player Detection**: Detects and tracks human poses
- **Ball Possession**: Determines which player is holding the ball
- **Traveling Detection**: Identifies traveling violations
- **Live Events**: Displays real-time basketball events and violations

### 3. Analysis Results

The interface shows:
- **Live Video Feed**: Your webcam stream
- **Connection Status**: WebSocket connection to the OpenCV backend
- **Real-Time Stats**: Current detection status
- **Live Events**: Basketball events and violations as they occur
- **Session Stats**: Summary of all detected events

## Troubleshooting

### Common Issues

1. **CORS Error (Access to fetch blocked)**
   - Ensure the Flask server is running on port 5002
   - Check that CORS is properly configured in `backend/user.py`
   - Verify the frontend is making requests to `http://localhost:5002`

2. **WebSocket Connection Failed**
   - Ensure the OpenCV server is running on port 8765
   - Check firewall settings
   - Verify no other service is using port 8765

3. **Model Loading Errors**
   - Verify model files are in the correct directory (`backend/opencv-test/`)
   - Check file permissions
   - Ensure sufficient disk space

4. **Webcam Access Issues**
   - Allow browser access to webcam
   - Check webcam permissions
   - Try refreshing the page

5. **Authentication Issues**
   - Ensure the Flask server is running
   - Check MongoDB connection (if using database)
   - Verify JWT token configuration

### Performance Optimization

- **Frame Rate**: The system processes frames at ~10-15 FPS for optimal performance
- **Resolution**: Recommended video resolution is 1280x720
- **Lighting**: Ensure good lighting for better detection accuracy

## Development

### Backend Development

- **Flask Server**: `backend/user.py` - Handles authentication and API endpoints
- **OpenCV Server**: `backend/opencv_server.py` - Integrates with `person_ball_detection.py`
- **Core Detection**: `backend/opencv-test/person_ball_detection.py` - Your existing detection logic
- **Startup Scripts**: 
  - `backend/start_flask_server.py` - Starts Flask server
  - `backend/start_opencv_server.py` - Starts OpenCV server

### Frontend Development

The webcam interface is in `frontend/src/pages/WebcamAnalysisPage.tsx`:
- WebSocket connection management
- Video frame capture and transmission
- Real-time event display

### Modifying Detection Logic

To modify the detection logic:
1. Edit `backend/opencv-test/person_ball_detection.py` directly
2. The changes will be automatically used by the OpenCV server
3. Restart the OpenCV server to apply changes

## Security Considerations

- The Flask server runs on localhost only
- The OpenCV server runs on localhost only
- No video data is stored permanently
- All processing happens locally on your machine
- JWT tokens are used for authentication

## Support

For issues or questions:
1. Check the console logs for error messages
2. Verify all dependencies are installed correctly
3. Ensure model files are present and accessible
4. Test with different lighting conditions
5. Check that both servers are running on the correct ports

## Performance Notes

- **CPU Usage**: The system uses significant CPU for real-time analysis
- **Memory**: YOLO models require ~2-4GB RAM
- **GPU**: CUDA acceleration is supported if available
- **Network**: All communication is local only

## Future Enhancements

Potential improvements:
- Multiple camera support
- Advanced violation detection
- Player identification
- Game statistics tracking
- Export analysis results
- Mobile app support 