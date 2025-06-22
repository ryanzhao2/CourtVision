from ultralytics import YOLO
import pickle
import os
import numpy as np
import cv2

class HoopDetector:
    """
    A robust basketball hoop detector using multiple detection strategies.
    """
    def __init__(self, model_path):
        """
        Initializes the HoopDetector with the YOLO model.
        
        Args:
            model_path (str): The path to the YOLO model weights for hoop detection.
        """
        try:
            self.model = YOLO(model_path)
            print(f"    Hoop detector initialized with model: {model_path}")
            print(f"    Model classes: {self.model.names}")
        except Exception as e:
            print(f"    Warning: Could not load YOLO model: {e}")
            self.model = None
        
        # Create a simple hoop template for template matching
        self.hoop_template = self._create_hoop_template()

    def _create_hoop_template(self):
        """Create a simple circular template for hoop detection."""
        template_size = 60
        template = np.zeros((template_size, template_size), dtype=np.uint8)
        center = template_size // 2
        radius = template_size // 3
        
        # Draw a circle (hoop)
        cv2.circle(template, (center, center), radius, (255,), 3)
        return template

    def _detect_hoop_by_shape(self, frame):
        """
        Detect hoops by looking for circular shapes.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Detect circles using Hough Circle Transform
        circles = cv2.HoughCircles(
            blurred, 
            cv2.HOUGH_GRADIENT, 
            dp=1, 
            minDist=50,
            param1=50, 
            param2=30, 
            minRadius=20, 
            maxRadius=100
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            
            # Find the circle closest to the top of the frame (likely the hoop)
            best_circle = None
            min_y = float('inf')
            
            for (x, y, r) in circles:
                # Prefer circles in the upper half of the frame
                if y < frame.shape[0] // 2 and r > 15:
                    if y < min_y:
                        min_y = y
                        best_circle = (x, y, r)
            
            if best_circle:
                x, y, r = best_circle
                return [x - r, y - r, x + r, y + r]
        
        return None

    def _detect_hoop_by_template(self, frame):
        """
        Detect hoops using template matching.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Template matching
        result = cv2.matchTemplate(gray, self.hoop_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val > 0.3:  # Threshold for template matching
            x, y = max_loc
            h, w = self.hoop_template.shape
            return [x, y, x + w, y + h]
        
        return None

    def _detect_hoop_by_color(self, frame):
        """
        Enhanced color-based hoop detection.
        """
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define multiple color ranges for basketball hoops
        color_ranges = [
            # Orange/red (typical hoop colors)
            (np.array([5, 50, 50]), np.array([15, 255, 255])),
            (np.array([0, 50, 50]), np.array([10, 255, 255])),
            (np.array([170, 50, 50]), np.array([180, 255, 255])),
            # White (some hoops are white)
            (np.array([0, 0, 200]), np.array([180, 30, 255])),
            # Gray/black (metal hoops)
            (np.array([0, 0, 50]), np.array([180, 255, 150]))
        ]
        
        combined_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        
        for lower, upper in color_ranges:
            mask = cv2.inRange(hsv, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        # Apply morphological operations to clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Find contours that could be hoops (circular, reasonable size)
            potential_hoops = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 20000:  # Reasonable size for a hoop
                    # Check if contour is roughly circular
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                        if circularity > 0.3:  # Roughly circular
                            potential_hoops.append(contour)
            
            if potential_hoops:
                # Choose the contour closest to the top of the frame
                best_contour = min(potential_hoops, key=lambda c: cv2.boundingRect(c)[1])
                x, y, w, h = cv2.boundingRect(best_contour)
                return [x, y, x + w, y + h]
        
        return None

    def _detect_hoop_by_yolo(self, frame):
        """
        Detect hoops using YOLO model.
        """
        if self.model is None:
            return None
            
        try:
            results = self.model.predict(frame, conf=0.2, verbose=False)  # Very low confidence threshold
            
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None and len(result.boxes) > 0:
                    # Find the detection with highest confidence
                    best_detection = None
                    max_confidence = 0
                    
                    for box in result.boxes:
                        class_id = int(box.cls)
                        class_name = self.model.names[class_id]
                        confidence = float(box.conf)
                        
                        # Accept any class that might be a hoop
                        if class_name in ['hoop', 'basket', 'rim', 'net'] and confidence > max_confidence:
                            max_confidence = confidence
                            best_detection = box.xyxy[0].tolist()
                    
                    return best_detection
        except Exception as e:
            print(f"    YOLO detection error: {e}")
        
        return None

    def detect_frames(self, frames):
        """
        Detects the hoop in a sequence of frames using multiple strategies.
        """
        print(f"    Processing {len(frames)} frames with multiple detection strategies")
        
        hoop_positions = []
        detection_stats = {
            'yolo': 0,
            'shape': 0,
            'template': 0,
            'color': 0,
            'none': 0
        }
        
        for i, frame in enumerate(frames):
            if i % 10 == 0:  # Progress update every 10 frames
                print(f"    Processing frame {i}/{len(frames)}")
            
            # Try different detection methods in order of preference
            hoop_detection = None
            
            # 1. Try YOLO first
            if self.model:
                hoop_detection = self._detect_hoop_by_yolo(frame)
                if hoop_detection:
                    detection_stats['yolo'] += 1
                    continue
            
            # 2. Try shape detection
            hoop_detection = self._detect_hoop_by_shape(frame)
            if hoop_detection:
                detection_stats['shape'] += 1
                continue
            
            # 3. Try template matching
            hoop_detection = self._detect_hoop_by_template(frame)
            if hoop_detection:
                detection_stats['template'] += 1
                continue
            
            # 4. Try color detection
            hoop_detection = self._detect_hoop_by_color(frame)
            if hoop_detection:
                detection_stats['color'] += 1
                continue
            
            # 5. No detection found
            detection_stats['none'] += 1
            
            hoop_positions.append(hoop_detection)
        
        print(f"    Detection statistics:")
        print(f"      YOLO: {detection_stats['yolo']}")
        print(f"      Shape: {detection_stats['shape']}")
        print(f"      Template: {detection_stats['template']}")
        print(f"      Color: {detection_stats['color']}")
        print(f"      None: {detection_stats['none']}")
        print(f"      Total frames with hoops: {sum(detection_stats.values()) - detection_stats['none']}/{len(frames)}")
        
        return hoop_positions

    def get_hoop_positions(self, frames, read_from_stub=False, stub_path=None):
        """
        Gets the position of the hoop for each frame, with optional caching.
        """
        if read_from_stub and stub_path and os.path.exists(stub_path):
            try:
                with open(stub_path, 'rb') as f:
                    cached_positions = pickle.load(f)
                    print(f"    Loaded {len(cached_positions)} cached hoop positions")
                    return cached_positions
            except Exception as e:
                print(f"    Failed to load cached positions: {e}")

        print("    Running hoop detection with multiple strategies...")
        hoop_positions = self.detect_frames(frames)

        if stub_path:
            try:
                with open(stub_path, 'wb') as f:
                    pickle.dump(hoop_positions, f)
                print(f"    Saved hoop positions to {stub_path}")
            except Exception as e:
                print(f"    Failed to save positions: {e}")
            
        return hoop_positions 