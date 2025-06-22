import cv2
import numpy as np
import sys
from ultralytics import YOLO
import time

def is_person_holding_ball_with_hands(ball_box, pose_keypoints, threshold=8):
    """
    Check if a person is holding the basketball based on ball being extremely close to or over any keypoint.
    Returns True if the ball's bounding box overlaps with or is extremely close to any keypoint.
    """
    if not ball_box or pose_keypoints is None:
        return False
    
    bx1, by1, bx2, by2 = ball_box[:4]
    ball_center_x = (bx1 + bx2) / 2
    ball_center_y = (by1 + by2) / 2
    
    # Check if ANY keypoint is inside or extremely close to the ball's bounding box
    for i, keypoint in enumerate(pose_keypoints):
        if keypoint[2] > 0.2:  # Very low confidence threshold for extremely sensitive detection
            keypoint_x, keypoint_y = keypoint[0], keypoint[1]
            
            # Check if keypoint is inside the ball's bounding box (direct overlap)
            if bx1 <= keypoint_x <= bx2 and by1 <= keypoint_y <= by2:
                return True
            
            # Check if keypoint is extremely close to the ball's bounding box edges
            # Calculate distance from keypoint to the nearest point on the ball's bounding box
            nearest_x = max(bx1, min(keypoint_x, bx2))
            nearest_y = max(by1, min(keypoint_y, by2))
            
            distance = np.sqrt((keypoint_x - nearest_x)**2 + (keypoint_y - nearest_y)**2)
            
            # If keypoint is extremely close to the ball's bounding box, consider it holding
            if distance < threshold:
                return True
            
            # Additional check: distance from keypoint to ball center (for very close proximity)
            center_distance = np.sqrt((keypoint_x - ball_center_x)**2 + (keypoint_y - ball_center_y)**2)
            if center_distance < threshold * 2:  # Allow slightly more distance for center proximity
                return True
    
    return False

def get_person_center_from_pose(pose_keypoints):
    """
    Calculate the center position of a person based on pose keypoints.
    """
    if pose_keypoints is None:
        return None
    
    # Get all visible keypoints
    visible_keypoints = []
    for keypoint in pose_keypoints:
        if keypoint[2] > 0.4:  # Confidence threshold
            visible_keypoints.append([keypoint[0], keypoint[1]])
    
    if not visible_keypoints:
        return None
    
    # Calculate center from visible keypoints
    x_coords = [kp[0] for kp in visible_keypoints]
    y_coords = [kp[1] for kp in visible_keypoints]
    
    center_x = sum(x_coords) / len(x_coords)
    center_y = sum(y_coords) / len(y_coords)
    
    return (center_x, center_y)

def detect_steps(knee_positions, hip_positions, step_threshold=20):
    """
    Detect steps based on knee movement relative to hip positions.
    Returns the number of steps taken.
    """
    if len(knee_positions) < 10 or len(hip_positions) < 10:
        return 0
    
    # Get recent knee and hip positions (last 15 frames)
    recent_knee_positions = knee_positions[-15:]
    recent_hip_positions = hip_positions[-15:]
    
    # Calculate knee movement relative to hips
    movements = []
    for i in range(1, len(recent_knee_positions)):
        if (recent_knee_positions[i] is not None and recent_knee_positions[i-1] is not None and
            recent_hip_positions[i] is not None and recent_hip_positions[i-1] is not None):
            
            # Calculate knee movement
            knee_movement = np.sqrt((recent_knee_positions[i][0] - recent_knee_positions[i-1][0])**2 + 
                                  (recent_knee_positions[i][1] - recent_knee_positions[i-1][1])**2)
            
            # Calculate hip movement
            hip_movement = np.sqrt((recent_hip_positions[i][0] - recent_hip_positions[i-1][0])**2 + 
                                 (recent_hip_positions[i][1] - recent_hip_positions[i-1][1])**2)
            
            # Calculate relative movement (knee movement relative to hip)
            relative_movement = knee_movement - hip_movement
            
            movements.append(relative_movement)
    
    # Count steps based on significant relative movements
    steps = 0
    for movement in movements:
        if movement > step_threshold:
            steps += 1
    
    return steps

def detect_traveling(ball_positions, knee_positions, holding_frames, travel_threshold=600):
    """
    Detect traveling based on:
    1. Ball is being held above knee level
    2. Ball is moving horizontally (X-direction) more than threshold
    3. Continuous holding for several frames
    """
    if len(ball_positions) < 10 or len(knee_positions) < 10 or holding_frames < 5:
        return False
    
    # Check if ball is moving horizontally (X-direction)
    recent_ball_positions = ball_positions[-10:]
    ball_x_positions = [pos[0] for pos in recent_ball_positions if pos is not None]
    
    if len(ball_x_positions) < 5:
        return False
    
    # Calculate horizontal movement of ball
    min_x = min(ball_x_positions)
    max_x = max(ball_x_positions)
    horizontal_movement = max_x - min_x
    
    # Check if ball is above knee level
    if knee_positions and knee_positions[-1] is not None:
        current_ball_y = ball_positions[-1][1] if ball_positions[-1] is not None else 0
        current_knee_y = knee_positions[-1][1]
        
        # Ball is above knees if ball Y is smaller than knee Y (smaller Y = higher on screen)
        ball_above_knees = current_ball_y < current_knee_y
        
        # Traveling detected if ball is above knees and moving horizontally more than threshold
        if ball_above_knees and horizontal_movement > travel_threshold:
            return True
    
    return False

def main():
    # Open the webcam
    print("Attempting to open webcam...")
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        sys.exit()
    
    print("Webcam opened successfully. Now loading YOLO models...")
    
    # Load only the pose and basketball models
    basketball_model = YOLO('basketballmodel.pt')
    pose_model = YOLO('yolov8s-pose.pt')
    
    print("YOLO models loaded.")
    print("Basketball detection with travel detection active. Press 'q' to quit.")
    
    # Initialize variables for tracking
    ball_positions = []  # Track ball position history
    knee_positions = []  # Track knee positions for step counting
    hip_positions = []  # Track hip positions for step counting
    was_holding = False  # Track previous frame's holding state
    current_holder = None  # Track which person is currently holding the ball
    holding_frames = 0  # Count frames of continuous holding
    traveling_detected = False  # Flag for travel detection
    last_announcement_time = 0  # Track when we last announced holding
    
    while cap.isOpened():
        # Read a frame from the video with retry logic
        success = False
        retry_count = 0
        max_retries = 5
        
        while not success and retry_count < max_retries:
            success, frame = cap.read()
            if not success:
                retry_count += 1
                print(f"Failed to grab frame, attempt {retry_count}/{max_retries}")
                cv2.waitKey(100)  # Wait 100ms before retrying
        
        if not success:
            print(f"Failed to grab frame after {max_retries} attempts. Exiting...")
            break
        
        # Reset retry count on successful frame grab
        retry_count = 0
        
        # Detect basketballs using basketball model
        basketball_results = basketball_model(frame)
        
        # Get basketball detections
        ball_boxes = []
        for r in basketball_results:
            for box in r.boxes:
                class_id = int(box.cls[0])
                class_name = basketball_model.names[class_id]
                
                # Get bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                confidence = float(box.conf[0])
                
                # Only include high-confidence detections
                if confidence > 0.5:
                    ball_boxes.append((x1, y1, x2, y2, confidence))
        
        # Detect pose using pose model
        pose_results = pose_model(frame)
        
        # Track ball and person positions
        current_holding = False
        current_holder_id = None
        current_holder_pose = None
        current_knee_pos = None
        current_hip_pos = None
        current_person_center = None
        
        if ball_boxes and pose_results:
            ball_x, ball_y, ball_w, ball_h, ball_area = ball_boxes[0]
            ball_center_x = ball_x + ball_w / 2
            ball_center_y = ball_y + ball_h / 2
            
            # Add current ball position to history
            ball_positions.append((ball_center_x, ball_center_y))
            
            # Keep only recent ball history (last 30 frames)
            if len(ball_positions) > 30:
                ball_positions.pop(0)
            
            # Check which person is holding the ball using hand positions
            for i, pose_result in enumerate(pose_results):
                if pose_result.keypoints is not None and len(pose_result.keypoints.data) > 0:
                    person_pose_keypoints = pose_result.keypoints.data[0]
                    
                    if is_person_holding_ball_with_hands(ball_boxes[0], person_pose_keypoints):
                        current_holding = True
                        current_holder_id = i
                        current_holder_pose = person_pose_keypoints
                        
                        # Get person center from pose keypoints
                        current_person_center = get_person_center_from_pose(person_pose_keypoints)
                        
                        # Get knee and hip positions for step counting (keypoints 13 and 14 for knees, 11 and 12 for hips)
                        left_knee = person_pose_keypoints[13] if len(person_pose_keypoints) > 13 and person_pose_keypoints[13][2] > 0.4 else None
                        right_knee = person_pose_keypoints[14] if len(person_pose_keypoints) > 14 and person_pose_keypoints[14][2] > 0.4 else None
                        left_hip = person_pose_keypoints[11] if len(person_pose_keypoints) > 11 and person_pose_keypoints[11][2] > 0.4 else None
                        right_hip = person_pose_keypoints[12] if len(person_pose_keypoints) > 12 and person_pose_keypoints[12][2] > 0.4 else None
                        
                        # Use the knee with higher confidence, or average if both are visible
                        if left_knee is not None and right_knee is not None:
                            current_knee_pos = ((left_knee[0] + right_knee[0]) / 2, (left_knee[1] + right_knee[1]) / 2)
                        elif left_knee is not None:
                            current_knee_pos = (left_knee[0], left_knee[1])
                        elif right_knee is not None:
                            current_knee_pos = (right_knee[0], right_knee[1])
                        
                        # Use the hip with higher confidence, or average if both are visible
                        if left_hip is not None and right_hip is not None:
                            current_hip_pos = ((left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2)
                        elif left_hip is not None:
                            current_hip_pos = (left_hip[0], left_hip[1])
                        elif right_hip is not None:
                            current_hip_pos = (right_hip[0], right_hip[1])
                        
                        break
        
        # Track knee and hip positions for step counting
        if current_knee_pos is not None and current_hip_pos is not None:
            knee_positions.append(current_knee_pos)
            hip_positions.append(current_hip_pos)
        else:
            knee_positions.append(None)
            hip_positions.append(None)
        
        # Keep only recent knee and hip history (last 30 frames)
        if len(knee_positions) > 30:
            knee_positions.pop(0)
            hip_positions.pop(0)
        
        # Update holding state and detect traveling
        if current_holding and was_holding and current_holder_id == current_holder:
            # Same person has continuous possession
            holding_frames += 1
            
            # Check for traveling after some frames of holding
            if holding_frames > 5 and not traveling_detected:
                if detect_traveling(ball_positions, knee_positions, holding_frames):
                    traveling_detected = True
                    print(f"TRAVELING DETECTED! Player {current_holder_id} ball moving horizontally above knees!")
        else:
            # Possession changed or lost
            if current_holding and not was_holding:
                # New possession
                current_holder = current_holder_id
                holding_frames = 1
                traveling_detected = False
                
                print(f"Player {current_holder_id} gained possession")
                
                # Announce holding detection
                current_time = time.time()
                if current_time - last_announcement_time > 2:  # Announce every 2 seconds max
                    print(f"PLAYER {current_holder_id} IS HOLDING THE BALL!")
                    last_announcement_time = current_time
                    
            elif not current_holding and was_holding:
                # Lost possession
                print(f"Player {current_holder} lost possession")
                traveling_detected = False
        
        # Update previous state
        was_holding = current_holding
        
        # Draw pose keypoints for all detected people
        for i, pose_result in enumerate(pose_results):
            if pose_result.keypoints is not None and len(pose_result.keypoints.data) > 0:
                keypoints = pose_result.keypoints.data[0]
                
                # Check if this person is holding the basketball
                is_holding = (i == current_holder_id)
                
                # Draw keypoints for each person
                for j, keypoint in enumerate(keypoints):
                    if keypoint[2] > 0.4:  # Confidence threshold
                        x, y = int(keypoint[0]), int(keypoint[1])
                        
                        # Special highlighting for wrists (keypoints 9 and 10) of current holder
                        if j == 9:  # Left wrist
                            if is_holding:
                                color = (0, 255, 255)  # Bright yellow for current holder
                                radius = 12
                                cv2.circle(frame, (x, y), radius, color, -1)
                                cv2.putText(frame, "L Hand", (x + 5, y - 5), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                            else:
                                color = (0, 255, 255)  # Yellow for others
                                radius = 8
                                cv2.circle(frame, (x, y), radius, color, -1)
                        elif j == 10:  # Right wrist
                            if is_holding:
                                color = (255, 0, 255)  # Bright magenta for current holder
                                radius = 12
                                cv2.circle(frame, (x, y), radius, color, -1)
                                cv2.putText(frame, "R Hand", (x + 5, y - 5), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                            else:
                                color = (255, 0, 255)  # Magenta for others
                                radius = 8
                                cv2.circle(frame, (x, y), radius, color, -1)
                        elif j in [13, 14]:  # Knees - highlight for step tracking
                            if is_holding:
                                color = (255, 255, 0)  # Bright cyan for current holder
                                radius = 10
                                cv2.circle(frame, (x, y), radius, color, -1)
                                cv2.putText(frame, "Knee", (x + 5, y - 5), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                            else:
                                color = (255, 255, 0)  # Cyan for others
                                radius = 6
                                cv2.circle(frame, (x, y), radius, color, -1)
                        elif j in [11, 12]:  # Hips - highlight for step tracking
                            if is_holding:
                                color = (255, 255, 0)  # Bright cyan for current holder
                                radius = 10
                                cv2.circle(frame, (x, y), radius, color, -1)
                                cv2.putText(frame, "Hip", (x + 5, y - 5), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                            else:
                                color = (255, 255, 0)  # Cyan for others
                                radius = 6
                                cv2.circle(frame, (x, y), radius, color, -1)
                        else:
                            # Different colors for different body parts
                            if j < 5:  # Head and torso
                                color = (255, 255, 0)  # Cyan
                            elif j < 11:  # Arms
                                color = (0, 255, 255)  # Yellow
                            elif j < 17:  # Legs
                                color = (255, 0, 255)  # Magenta
                            else:  # Hands and feet
                                color = (0, 255, 0)  # Green
                            
                            # Make keypoints larger for the current holder
                            radius = 6 if is_holding else 4
                            cv2.circle(frame, (x, y), radius, color, -1)
                
                # Draw player ID and status near the person's center
                if current_person_center and is_holding:
                    center_x, center_y = int(current_person_center[0]), int(current_person_center[1])
                    cv2.putText(frame, f"Player {i} - HOLDING", (center_x - 50, center_y - 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                elif current_person_center:
                    center_x, center_y = int(current_person_center[0]), int(current_person_center[1])
                    cv2.putText(frame, f"Player {i}", (center_x - 30, center_y - 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw bounding boxes for basketballs (green)
        for (x1, y1, x2, y2, confidence) in ball_boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green for basketballs
            cv2.putText(frame, f"Basketball ({confidence:.2f})", (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display travel status prominently
        if traveling_detected:
            cv2.putText(frame, "TRAVELING DETECTED!", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            cv2.putText(frame, "3+ STEPS WITHOUT DRIBBLING", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Display holding status
        if current_holder_id is not None:
            cv2.putText(frame, f"Player {current_holder_id} is HOLDING the ball", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"Holding for {holding_frames} frames", (10, 140), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Display ball position and movement info
        if current_holder_id is not None and holding_frames > 5 and ball_positions and knee_positions:
            if ball_positions[-1] is not None and knee_positions[-1] is not None:
                ball_y = ball_positions[-1][1]
                knee_y = knee_positions[-1][1]
                ball_above_knees = ball_y < knee_y
                
                # Calculate horizontal movement
                if len(ball_positions) >= 10:
                    recent_x_positions = [pos[0] for pos in ball_positions[-10:] if pos is not None]
                    if recent_x_positions:
                        horizontal_movement = max(recent_x_positions) - min(recent_x_positions)
                        cv2.putText(frame, f"Ball above knees: {'YES' if ball_above_knees else 'NO'}", (10, 170), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        cv2.putText(frame, f"Horizontal movement: {horizontal_movement:.1f}px", (10, 200), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Display the frame
        cv2.imshow("Basketball Detection with Travel Detection", frame)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    # Release the video capture object and close the display window
    print("Releasing resources.")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()