import cv2
import numpy as np
from hoop_detector import HoopDetector
import os

def test_hoop_detector():
    """Test the hoop detector with sample frames."""
    
    # Initialize detector
    model_path = "models/hoop_detector_yolov8m.pt"  # Update this path
    
    if not os.path.exists(model_path):
        print(f"Model file not found: {model_path}")
        print("Using detector without YOLO model...")
        model_path = "nonexistent_model.pt"  # This will cause the model to be None
    
    detector = HoopDetector(model_path)
    
    # Test with a sample video or create a test frame
    print("Testing hoop detection methods...")
    
    # Create a test frame with a simple circle (simulating a hoop)
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw a circle in the upper part of the frame (like a hoop)
    cv2.circle(test_frame, (320, 120), 40, (0, 165, 255), 5)  # Orange circle
    
    # Test each detection method
    print("\n1. Testing YOLO detection...")
    yolo_result = detector._detect_hoop_by_yolo(test_frame)
    print(f"   YOLO result: {yolo_result}")
    
    print("\n2. Testing shape detection...")
    shape_result = detector._detect_hoop_by_shape(test_frame)
    print(f"   Shape result: {shape_result}")
    
    print("\n3. Testing template matching...")
    template_result = detector._detect_hoop_by_template(test_frame)
    print(f"   Template result: {template_result}")
    
    print("\n4. Testing color detection...")
    color_result = detector._detect_hoop_by_color(test_frame)
    print(f"   Color result: {color_result}")
    
    # Test with multiple frames
    print("\n5. Testing with multiple frames...")
    test_frames = [test_frame] * 5  # 5 identical frames
    results = detector.detect_frames(test_frames)
    print(f"   Results: {results}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_hoop_detector() 