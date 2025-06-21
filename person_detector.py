import cv2
import numpy as np
from ultralytics import YOLO
import time
from collections import defaultdict

class PersonDetector:
    def __init__(self, model_path=None):
        """
        Initialize the person detector with YOLO model
        Args:
            model_path: Path to custom YOLO model (optional, will use YOLOv8n-pose if None)
        """
        if model_path:
            self.model = YOLO(model_path)
        else:
            # Use YOLOv8 pose estimation model
            self.model = YOLO('yolov8n-pose.pt')
        
        # Load object detection model for water bottle detection
        self.object_model = YOLO('yolov8n.pt')  # General object detection
        
        # Define body part indices for YOLO pose model
        self.body_parts = {
            'nose': 0,
            'left_eye': 1,
            'right_eye': 2,
            'left_ear': 3,
            'right_ear': 4,
            'left_shoulder': 5,
            'right_shoulder': 6,
            'left_elbow': 7,
            'right_elbow': 8,
            'left_wrist': 9,
            'right_wrist': 10,
            'left_hip': 11,
            'right_hip': 12,
            'left_knee': 13,
            'right_knee': 14,
            'left_ankle': 15,
            'right_ankle': 16
        }
        
        # Define regions of interest for torso, hands, and feet
        self.torso_points = ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']
        
        # Colors for different body parts
        self.colors = {
            'body': (0, 255, 0),      # Green
            'left_hand': (255, 0, 0),  # Blue
            'right_hand': (0, 255, 255), # Yellow
            'left_foot': (255, 0, 255),  # Magenta
            'right_foot': (0, 0, 255),   # Red
            'travel_violation': (0, 0, 0),  # Black for travel violations
            'water_bottle': (255, 165, 0)  # Orange for water bottles
        }
        
        # Player tracking data
        self.player_data = defaultdict(lambda: {
            'left_foot_pos': None,
            'right_foot_pos': None,
            'step_count': 0,
            'last_step_time': 0,
            'step_threshold': 50,  # Minimum distance for a step
            'step_cooldown': 0.5,  # Minimum time between steps (seconds)
            'left_hand_has_item': False,
            'right_hand_has_item': False,
            'water_bottle_detected': False,
            'travel_violations': 0,
            'last_travel_reset': 0
        })
        
        self.frame_count = 0
    
    def get_bounding_box(self, points, padding=20):
        """
        Calculate bounding box from a list of points with optional padding
        Args:
            points: List of (x, y) coordinates
            padding: Padding to add around the bounding box (default: 20 pixels)
        Returns:
            tuple: (x_min, y_min, x_max, y_max)
        """
        if not points:
            return None
        
        x_coords = [p[0] for p in points if p is not None]
        y_coords = [p[1] for p in points if p is not None]
        
        if not x_coords or not y_coords:
            return None
        
        x_min, y_min, x_max, y_max = min(x_coords), min(y_coords), max(x_coords), max(y_coords)
        
        # Add padding to create a small bounding box
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = x_max + padding
        y_max = y_max + padding
        
        return (x_min, y_min, x_max, y_max)
    
    def detect_body_parts(self, frame):
        """
        Detect body parts and track travel violations
        Args:
            frame: Input image frame
        Returns:
            dict: Dictionary containing detected body parts with bounding boxes and travel data
        """
        results = self.model(frame, verbose=False)
        
        detections = {
            'body': [],
            'left_hand': [],
            'right_hand': [],
            'left_foot': [],
            'right_foot': [],
            'step_counts': {},
            'travel_violations': {},
            'hand_items': {}
        }
        
        for result in results:
            if result.keypoints is not None and len(result.keypoints.data) > 0:
                # Process each person detected
                for person_idx in range(len(result.keypoints.data)):
                    keypoints = result.keypoints.data[person_idx]
                    
                    # Check if keypoints array has enough elements
                    if len(keypoints) < 17:
                        continue
                    
                    # Create unique player ID
                    player_id = f"player_{person_idx}"
                    
                    # Extract body (torso) points
                    body_points = []
                    for point_name in self.torso_points:
                        idx = self.body_parts[point_name]
                        if idx < len(keypoints) and keypoints[idx][2] > 0.5:
                            body_points.append((int(keypoints[idx][0]), int(keypoints[idx][1])))
                    
                    # Extract hand points
                    left_hand_points = []
                    right_hand_points = []
                    left_hand_pos = None
                    right_hand_pos = None
                    
                    # Left wrist
                    left_wrist_idx = self.body_parts['left_wrist']
                    if left_wrist_idx < len(keypoints) and keypoints[left_wrist_idx][2] > 0.5:
                        left_hand_pos = (int(keypoints[left_wrist_idx][0]), int(keypoints[left_wrist_idx][1]))
                        left_hand_points.append(left_hand_pos)
                    
                    # Right wrist
                    right_wrist_idx = self.body_parts['right_wrist']
                    if right_wrist_idx < len(keypoints) and keypoints[right_wrist_idx][2] > 0.5:
                        right_hand_pos = (int(keypoints[right_wrist_idx][0]), int(keypoints[right_wrist_idx][1]))
                        right_hand_points.append(right_hand_pos)
                    
                    # Extract foot points
                    left_foot_points = []
                    right_foot_points = []
                    left_foot_pos = None
                    right_foot_pos = None
                    
                    # Left ankle
                    left_ankle_idx = self.body_parts['left_ankle']
                    if left_ankle_idx < len(keypoints) and keypoints[left_ankle_idx][2] > 0.5:
                        left_foot_pos = (int(keypoints[left_ankle_idx][0]), int(keypoints[left_ankle_idx][1]))
                        left_foot_points.append(left_foot_pos)
                    
                    # Right ankle
                    right_ankle_idx = self.body_parts['right_ankle']
                    if right_ankle_idx < len(keypoints) and keypoints[right_ankle_idx][2] > 0.5:
                        right_foot_pos = (int(keypoints[right_ankle_idx][0]), int(keypoints[right_ankle_idx][1]))
                        right_foot_points.append(right_foot_pos)
                    
                    # Detect steps
                    self.detect_step(player_id, left_foot_pos, right_foot_pos)
                    
                    # Simple item detection: assume hands have items if they're in certain positions
                    # This is a simplified version - you can enhance this with actual object detection
                    left_hand_has_item = left_hand_pos is not None and left_hand_pos[1] < 400  # Above certain Y position
                    right_hand_has_item = right_hand_pos is not None and right_hand_pos[1] < 400
                    
                    # Detect travel violations
                    travel_violation = self.detect_travel_violation(player_id, left_hand_has_item, right_hand_has_item)
                    
                    # Calculate bounding boxes
                    if body_points:
                        body_bbox = self.get_bounding_box(body_points)
                        if body_bbox:
                            detections['body'].append((body_bbox, player_id))
                    
                    if left_hand_points:
                        left_hand_bbox = self.get_bounding_box(left_hand_points)
                        if left_hand_bbox:
                            detections['left_hand'].append(left_hand_bbox)
                    
                    if right_hand_points:
                        right_hand_bbox = self.get_bounding_box(right_hand_points)
                        if right_hand_bbox:
                            detections['right_hand'].append(right_hand_bbox)
                    
                    if left_foot_points:
                        left_foot_bbox = self.get_bounding_box(left_foot_points)
                        if left_foot_bbox:
                            detections['left_foot'].append(left_foot_bbox)
                    
                    if right_foot_points:
                        right_foot_bbox = self.get_bounding_box(right_foot_points)
                        if right_foot_bbox:
                            detections['right_foot'].append(right_foot_bbox)
                    
                    # Store data for this player
                    detections['step_counts'][player_id] = self.player_data[player_id]['step_count']
                    detections['travel_violations'][player_id] = self.player_data[player_id]['travel_violations']
                    detections['hand_items'][player_id] = {
                        'left_hand': left_hand_has_item,
                        'right_hand': right_hand_has_item
                    }
        
        return detections
    
    def draw_bounding_boxes(self, frame, detections):
        """
        Draw bounding boxes on the frame with step counters and travel violations
        Args:
            frame: Input image frame
            detections: Dictionary containing detected body parts
        Returns:
            numpy.ndarray: Frame with bounding boxes drawn
        """
        frame_with_boxes = frame.copy()
        
        # Draw body bounding boxes with step counters and travel violations
        for body_data in detections['body']:
            if isinstance(body_data, tuple):
                bbox, player_id = body_data
            else:
                bbox = body_data
                player_id = "unknown"
            
            x_min, y_min, x_max, y_max = bbox
            color = self.colors['body']
            
            # Draw rectangle
            cv2.rectangle(frame_with_boxes, (x_min, y_min), (x_max, y_max), color, 2)
            
            # Get player data
            step_count = detections['step_counts'].get(player_id, 0)
            travel_violations = detections['travel_violations'].get(player_id, 0)
            hand_items = detections['hand_items'].get(player_id, {'left_hand': False, 'right_hand': False})
            
            # Create display text
            step_text = f"Steps: {step_count}/3"
            travel_text = f"Travel: {travel_violations}"
            item_text = "Holding Item" if (hand_items['left_hand'] or hand_items['right_hand']) else "No Item"
            
            # Calculate text sizes
            step_size = cv2.getTextSize(step_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            travel_size = cv2.getTextSize(travel_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            item_size = cv2.getTextSize(item_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            
            # Calculate total height needed
            total_height = step_size[1] + travel_size[1] + item_size[1] + 30
            
            # Draw background for all text
            cv2.rectangle(frame_with_boxes, 
                         (x_min, y_min - total_height), 
                         (x_min + max(step_size[0], travel_size[0], item_size[0]) + 10, y_min), 
                         color, -1)
            
            # Draw step counter
            cv2.putText(frame_with_boxes, step_text, 
                       (x_min + 5, y_min - total_height + step_size[1] + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Draw travel violations
            travel_color = (0, 0, 255) if travel_violations > 0 else (255, 255, 255)  # Red if violations
            cv2.putText(frame_with_boxes, travel_text, 
                       (x_min + 5, y_min - total_height + step_size[1] + travel_size[1] + 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, travel_color, 2)
            
            # Draw item status
            item_color = (0, 255, 255) if (hand_items['left_hand'] or hand_items['right_hand']) else (255, 255, 255)
            cv2.putText(frame_with_boxes, item_text, 
                       (x_min + 5, y_min - total_height + step_size[1] + travel_size[1] + item_size[1] + 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, item_color, 2)
            
            # Add body label
            label = "Body"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame_with_boxes, (x_min, y_min - total_height - label_size[1] - 10), 
                         (x_min + label_size[0], y_min - total_height), color, -1)
            cv2.putText(frame_with_boxes, label, (x_min, y_min - total_height - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw other body parts
        for body_part in ['left_hand', 'right_hand', 'left_foot', 'right_foot']:
            color = self.colors[body_part]
            for bbox in detections[body_part]:
                x_min, y_min, x_max, y_max = bbox
                
                # Draw rectangle
                cv2.rectangle(frame_with_boxes, (x_min, y_min), (x_max, y_max), color, 2)
                
                # Add label
                label = body_part.replace('_', ' ').title()
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(frame_with_boxes, (x_min, y_min - label_size[1] - 10), 
                             (x_min + label_size[0], y_min), color, -1)
                cv2.putText(frame_with_boxes, label, (x_min, y_min - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame_with_boxes
    
    def run_detection(self, camera_index=0):
        """
        Run real-time detection using webcam
        Args:
            camera_index: Index of the camera to use (default: 0)
        """
        # Try different camera indices
        camera_indices = [0, 1, 2]
        cap = None
        
        for idx in camera_indices:
            print(f"Trying camera index {idx}...")
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                print(f"Successfully opened camera at index {idx}")
                break
            else:
                cap.release()
        
        if cap is None or not cap.isOpened():
            print("Error: Could not open any camera")
            print("Possible solutions:")
            print("1. Check if your webcam is connected")
            print("2. Grant camera permissions to your terminal/IDE")
            print("3. Make sure no other application is using the camera")
            print("4. On macOS, go to System Preferences > Security & Privacy > Camera")
            return
        
        print("Starting person detection...")
        print("Press 'q' to quit")
        
        consecutive_failures = 0
        max_failures = 5
        
        while True:
            ret, frame = cap.read()
            if not ret:
                consecutive_failures += 1
                print(f"Warning: Could not read frame (attempt {consecutive_failures}/{max_failures})")
                
                if consecutive_failures >= max_failures:
                    print("Error: Too many consecutive frame reading failures. Exiting...")
                    break
                
                # Wait a bit before trying again
                time.sleep(0.1)
                continue
            
            # Reset failure counter on successful frame read
            consecutive_failures = 0
            
            try:
                # Detect body parts
                detections = self.detect_body_parts(frame)
                
                # Draw bounding boxes
                frame_with_boxes = self.draw_bounding_boxes(frame, detections)
                
                # Add status text
                cv2.putText(frame_with_boxes, f"Press 'q' to quit", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Display the frame
                cv2.imshow('Person Detection - Body, Hands, Feet & Step Counter', frame_with_boxes)
                
            except Exception as e:
                print(f"Error processing frame: {e}")
                # Continue with next frame instead of crashing
                continue
            
            # Break loop on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("Detection stopped.")

    def detect_step(self, player_id, left_foot_pos, right_foot_pos):
        """
        Detect if a player has taken a step based on foot movement
        Counts up to 3 steps then resets
        Args:
            player_id: Unique identifier for the player
            left_foot_pos: Current left foot position (x, y) or None
            right_foot_pos: Current right foot position (x, y) or None
        Returns:
            bool: True if a step was detected
        """
        current_time = time.time()
        player_data = self.player_data[player_id]
        
        # Initialize positions if first detection
        if player_data['left_foot_pos'] is None:
            player_data['left_foot_pos'] = left_foot_pos
            player_data['right_foot_pos'] = right_foot_pos
            return False
        
        # Calculate distances moved by each foot
        left_distance = 0
        if left_foot_pos is not None and player_data['left_foot_pos'] is not None:
            left_distance = np.sqrt(
                (left_foot_pos[0] - player_data['left_foot_pos'][0])**2 + 
                (left_foot_pos[1] - player_data['left_foot_pos'][1])**2
            )
            
        right_distance = 0
        if right_foot_pos is not None and player_data['right_foot_pos'] is not None:
            right_distance = np.sqrt(
                (right_foot_pos[0] - player_data['right_foot_pos'][0])**2 + 
                (right_foot_pos[1] - player_data['right_foot_pos'][1])**2
            )
        
        # Check if enough time has passed since last step
        time_since_last_step = current_time - player_data['last_step_time']
        
        # Detect step if either foot moved significantly and cooldown has passed
        if (left_distance > player_data['step_threshold'] or right_distance > player_data['step_threshold']) and \
           time_since_last_step > player_data['step_cooldown']:
            
            player_data['step_count'] += 1
            
            # Reset counter after 3 steps
            if player_data['step_count'] > 3:
                player_data['step_count'] = 1
                print(f"Player {player_id} completed 3 steps, resetting to 1")
            else:
                print(f"Player {player_id} took step #{player_data['step_count']}")
            
            player_data['last_step_time'] = current_time
            return True
        
        # Update positions
        if left_foot_pos is not None:
            player_data['left_foot_pos'] = left_foot_pos
        if right_foot_pos is not None:
            player_data['right_foot_pos'] = right_foot_pos
            
        return False

    def detect_travel_violation(self, player_id, left_hand_has_item, right_hand_has_item):
        """
        Detect travel violation when player takes 3 steps while holding an item
        Args:
            player_id: Unique identifier for the player
            left_hand_has_item: Boolean indicating if left hand has an item
            right_hand_has_item: Boolean indicating if right hand has an item
        """
        player_data = self.player_data[player_id]
        current_time = time.time()
        
        # Update hand item status
        player_data['left_hand_has_item'] = left_hand_has_item
        player_data['right_hand_has_item'] = right_hand_has_item
        
        # Check if player has item in either hand
        has_item = left_hand_has_item or right_hand_has_item
        
        # If player has 3 steps and is holding an item, it's a travel violation
        if player_data['step_count'] >= 3 and has_item:
            # Only count violation once per 3-step cycle
            if current_time - player_data['last_travel_reset'] > 2.0:  # 2 second cooldown
                player_data['travel_violations'] += 1
                player_data['last_travel_reset'] = current_time
                print(f"TRAVEL VIOLATION! Player {player_id} took 3 steps while holding an item!")
                return True
        
        return False

    def detect_water_bottle(self, frame, left_hand_pos, right_hand_pos):
        """
        Detect water bottles in the frame and check if they're being held
        Args:
            frame: Input image frame
            left_hand_pos: Left hand position (x, y) or None
            right_hand_pos: Right hand position (x, y) or None
        Returns:
            tuple: (left_hand_has_bottle, right_hand_has_bottle, bottle_bboxes)
        """
        # Run object detection
        results = self.object_model(frame, verbose=False)
        
        bottle_bboxes = []
        left_hand_has_bottle = False
        right_hand_has_bottle = False
        
        for result in results:
            if result.boxes is not None:
                boxes = result.boxes.data
                for box in boxes:
                    x1, y1, x2, y2, conf, cls = box
                    
                    # Check if it's a bottle-like object (class 39 is bottle in COCO dataset)
                    # Also check for other container-like objects
                    if conf > 0.5 and cls in [39, 44, 67]:  # bottle, cup, cell phone
                        bottle_bbox = (int(x1), int(y1), int(x2), int(y2))
                        bottle_bboxes.append(bottle_bbox)
                        
                        # Calculate bottle center
                        bottle_center_x = (x1 + x2) / 2
                        bottle_center_y = (y1 + y2) / 2
                        
                        # Check if bottle is near left hand
                        if left_hand_pos is not None:
                            distance_to_left = np.sqrt(
                                (bottle_center_x - left_hand_pos[0])**2 + 
                                (bottle_center_y - left_hand_pos[1])**2
                            )
                            if distance_to_left < 100:  # Within 100 pixels
                                left_hand_has_bottle = True
                        
                        # Check if bottle is near right hand
                        if right_hand_pos is not None:
                            distance_to_right = np.sqrt(
                                (bottle_center_x - right_hand_pos[0])**2 + 
                                (bottle_center_y - right_hand_pos[1])**2
                            )
                            if distance_to_right < 100:  # Within 100 pixels
                                right_hand_has_bottle = True
        
        return left_hand_has_bottle, right_hand_has_bottle, bottle_bboxes

def main():
    """
    Main function to run the person detection program
    """
    print("Initializing Person Detector...")
    print("This program will detect torso, hands, and feet using YOLO pose estimation")
    
    # Initialize detector
    detector = PersonDetector()
    
    # Run detection
    detector.run_detection()

if __name__ == "__main__":
    main() 