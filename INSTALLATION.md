# Basketball Analysis System - Installation Guide

This guide will help you set up both the backend and frontend components of the Basketball Analysis System.

## Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **npm** or **yarn** (for frontend package management)
- **MongoDB** (optional - system will fall back to in-memory storage if not available)

## Backend Setup

### 1. Navigate to Backend Directory
```bash
cd backend
```

### 2. Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Setup
Create a `.env` file in the backend directory:
```bash
# Optional: MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/basketball_analysis
MONGODB_DB_NAME=basketball_analysis

# JWT Secret (generate a secure random string)
JWT_SECRET=your-secret-key-here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### 5. Download YOLO Model
The system uses YOLOv8 for object detection. The model file should be placed in the project root:
```bash
# Download YOLOv8n model (if not already present)
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### 6. Start Backend Server
```bash
python3 start_backend.py
```
The backend will run on `http://localhost:5002`

## Frontend Setup

### 1. Navigate to Frontend Directory
```bash
cd frontend
```

### 2. Install Node.js Dependencies
```bash
npm install
# or
yarn install
```

### 3. Start Development Server
```bash
npm run dev
# or
yarn dev
```
The frontend will run on `http://localhost:5173`

## Complete Requirements Files

### Backend Requirements (`backend/requirements.txt`)
```
# Core Web Framework
Flask==2.3.3
Werkzeug==3.0.1
flask-cors==4.0.0

# Authentication & Security
PyJWT==2.8.0
python-dotenv==1.0.0

# Database
pymongo==4.6.0

# Computer Vision & AI
opencv-python==4.8.1.78
ultralytics==8.0.196
supervision==0.18.0

# Data Processing
numpy==1.24.3
pandas==2.0.3
Pillow==10.0.1

# System & Utilities
psutil==5.9.5
websockets==12.0

# Additional ML/AI Dependencies
torch>=2.0.0
torchvision>=0.15.0

# File Processing
python-multipart==0.0.6

# Development & Testing (optional)
pytest==7.4.0
pytest-flask==1.2.0
```

### Frontend Dependencies (`frontend/package.json`)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.1",
    "lucide-react": "^0.263.1",
    "clsx": "^2.0.0",
    "tailwind-merge": "^1.14.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.3",
    "autoprefixer": "^10.4.14",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.3",
    "postcss": "^8.4.27",
    "tailwindcss": "^3.3.3",
    "typescript": "^5.0.2",
    "vite": "^4.4.5"
  }
}
```

## Quick Start Script

Create a `setup.sh` script for easy installation:

```bash
#!/bin/bash

echo "Setting up Basketball Analysis System..."

# Backend Setup
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Frontend Setup
echo "Setting up frontend..."
cd frontend
npm install
cd ..

echo "Setup complete!"
echo "To start backend: cd backend && python3 start_backend.py"
echo "To start frontend: cd frontend && npm run dev"
```

Make it executable:
```bash
chmod +x setup.sh
./setup.sh
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**: If ports 5002 or 5173 are in use, change them in the respective configuration files.

2. **MongoDB Connection**: If MongoDB is not available, the system will automatically fall back to in-memory storage.

3. **YOLO Model**: Ensure `yolov8n.pt` is in the project root directory.

4. **Python Version**: Ensure you're using Python 3.8 or higher.

5. **Node.js Version**: Ensure you're using Node.js 16 or higher.

### Verification

After setup, you should be able to:
1. Access the frontend at `http://localhost:5173`
2. Upload a video for analysis
3. View analysis results with video player and event timeline

## System Architecture

- **Backend**: Flask API with OpenCV and YOLO for video analysis
- **Frontend**: React/TypeScript with Tailwind CSS for UI
- **Database**: MongoDB (optional, with in-memory fallback)
- **AI Models**: YOLOv8 for object detection and tracking 