# Basketball Analysis System

A web-based interface to launch real-time basketball analysis using OpenCV and YOLO models.

## Features

- **Real-time Basketball Detection**: Detects basketballs using YOLO models
- **Player Pose Estimation**: Tracks player movements and body positions
- **Traveling Violation Detection**: Automatically detects traveling violations
- **Visual Overlays**: Shows bounding boxes, keypoints, and analysis results
- **Web Interface**: Simple React frontend to launch the analysis

## Architecture

- **Frontend**: React app that provides a button to launch the analysis
- **Backend**: Flask server that launches the `person_ball_detection.py` script
- **Analysis**: Desktop app using OpenCV and YOLO models with backend webcam

## Setup

### 1. Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt
pip install -r opencv-test/requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

### 2. Start the Backend

```bash
cd backend
python3 start_backend.py
```

The backend will be available at `http://localhost:5002`

### 3. Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. **Open the web interface** at `http://localhost:5173`
2. **Navigate to the Basketball Analysis page**
3. **Click "Start Analysis"** - this will launch the desktop app
4. **A new window will open** with real-time basketball analysis
5. **Press 'q'** in the analysis window to quit

## How It Works

1. The frontend sends a request to the backend API
2. The backend launches `person_ball_detection.py` as a subprocess
3. The desktop app opens with OpenCV window showing:
   - Real-time webcam feed
   - Basketball detection (green bounding boxes)
   - Player pose estimation (colored keypoints)
   - Traveling violation detection
   - Ball possession tracking
   - Visual overlays and status text

## Files Structure

```
├── backend/
│   ├── user.py                 # Flask API server
│   ├── start_backend.py        # Backend startup script
│   ├── opencv-test/
│   │   ├── person_ball_detection.py  # Main analysis script
│   │   ├── basketballmodel.pt        # Basketball detection model
│   │   ├── yolov8s-pose.pt           # Pose estimation model
│   │   └── requirements.txt          # Python dependencies
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── pages/
│   │       └── WebcamAnalysisPage.tsx  # Main analysis page
│   └── package.json
└── README.md
```

## API Endpoints

- `POST /api/launch-desktop-app` - Launches the basketball analysis desktop app
- `POST /api/kill-desktop-app` - Terminates the running basketball analysis process
- `GET /api/analysis-status` - Gets the current status of the analysis process

## Troubleshooting

- **Webcam not working**: Make sure your computer has a webcam and it's not being used by another application
- **Models not loading**: Check that the `.pt` files are in the `backend/opencv-test/` directory
- **Backend not starting**: Make sure port 5002 is not in use by another application
- **Frontend not connecting**: Ensure the backend is running on `http://localhost:5002`

## Controls

- **Press 'q'** in the analysis window to quit
- The app automatically detects basketballs and players
- Visual indicators show ball possession and violations
- Real-time analysis results are displayed on screen 