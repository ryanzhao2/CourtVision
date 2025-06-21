# Person Detection with YOLO and OpenCV

This program uses YOLO (You Only Look Once) pose estimation to detect and mark the torso, hands, and feet of a person using a webcam feed.

## Features

- Real-time person detection using webcam
- Detection of specific body parts: torso, hands, and feet
- Bounding box visualization with color-coded labels
- Uses YOLOv8 pose estimation model for accurate keypoint detection

## Requirements

- Python 3.8 or higher
- Webcam
- Internet connection (for downloading YOLO model on first run)

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the main program:

```bash
python person_detector.py
```

2. The program will:
   - Automatically download the YOLOv8 pose estimation model on first run
   - Open your webcam
   - Display real-time detection with bounding boxes
   - Green boxes: Torso (shoulders and hips)
   - Blue boxes: Hands (wrists)
   - Red boxes: Feet (ankles)

3. Press 'q' to quit the program

## How it Works

The program uses the YOLOv8 pose estimation model to detect 17 keypoints on a person's body:

- **Torso Detection**: Uses shoulder and hip keypoints to create a bounding box around the torso
- **Hand Detection**: Uses wrist keypoints to detect hands
- **Foot Detection**: Uses ankle keypoints to detect feet

The detection includes confidence thresholds to ensure reliable results.

## Customization

You can modify the program to:

- Change camera index (if you have multiple cameras)
- Adjust confidence thresholds
- Modify bounding box colors
- Add additional body part detection

## Troubleshooting

1. **Camera not found**: Make sure your webcam is connected and not being used by another application
2. **Model download issues**: Ensure you have a stable internet connection for the first run
3. **Performance issues**: The program works best with good lighting and when the person is clearly visible

## Dependencies

- `opencv-python`: Computer vision library
- `ultralytics`: YOLO implementation
- `numpy`: Numerical computing
- `torch`: PyTorch deep learning framework
- `torchvision`: Computer vision utilities for PyTorch
- `Pillow`: Image processing

## License

This project is open source and available under the MIT License. 