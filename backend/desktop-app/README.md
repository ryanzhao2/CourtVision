# Basketball Analysis Desktop App

This is the desktop application for real-time basketball analysis using OpenCV and YOLO models.

## Features

- Real-time basketball detection
- Player pose estimation
- Traveling violation detection
- Ball possession tracking
- Visual overlays with bounding boxes and keypoints

## Usage

1. Click "Launch Desktop App" in the web interface
2. The desktop app will open in a new window
3. Press 'q' to quit the application

## Requirements

- Python 3.8+
- OpenCV
- Ultralytics YOLO
- NumPy

## Installation

```bash
pip install -r requirements.txt
```

## Models

- `basketballmodel.pt` - Basketball detection model
- `yolov8s-pose.pt` - Human pose estimation model

## Controls

- Press 'q' to quit the application
- The app will automatically detect basketballs and players
- Visual indicators show ball possession and traveling violations 