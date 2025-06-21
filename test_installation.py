#!/usr/bin/env python3
"""
Test script to verify installation and model loading
"""

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing imports...")
    
    try:
        import cv2
        print(f"✓ OpenCV version: {cv2.__version__}")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✓ NumPy version: {np.__version__}")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
    except ImportError as e:
        print(f"✗ PyTorch import failed: {e}")
        return False
    
    try:
        from ultralytics import YOLO
        print("✓ Ultralytics YOLO import successful")
    except ImportError as e:
        print(f"✗ Ultralytics import failed: {e}")
        return False
    
    return True

def test_camera():
    """Test if camera can be accessed"""
    print("\nTesting camera access...")
    
    import cv2
    cap = cv2.VideoCapture(0)
    
    if cap.isOpened():
        print("✓ Camera access successful")
        ret, frame = cap.read()
        if ret:
            print(f"✓ Frame captured successfully (shape: {frame.shape})")
        else:
            print("✗ Could not capture frame")
            cap.release()
            return False
        cap.release()
        return True
    else:
        print("✗ Could not access camera")
        return False

def test_yolo_model():
    """Test if YOLO model can be loaded"""
    print("\nTesting YOLO model loading...")
    
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n-pose.pt')
        print("✓ YOLO model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ YOLO model loading failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running installation tests...\n")
    
    tests = [
        ("Package Imports", test_imports),
        ("Camera Access", test_camera),
        ("YOLO Model Loading", test_yolo_model)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("TEST RESULTS:")
    print("="*50)
    
    all_passed = True
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("="*50)
    
    if all_passed:
        print("🎉 All tests passed! You're ready to run the person detection program.")
        print("\nTo start the program, run:")
        print("python person_detector.py")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("\nCommon solutions:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Check camera permissions")
        print("3. Ensure internet connection for model download")

if __name__ == "__main__":
    main() 