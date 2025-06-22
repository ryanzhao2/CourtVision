import cv2
import numpy as np
import base64
import json
import asyncio
import websockets
from ultralytics import YOLO
import time
from typing import Dict, List, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasketballAnalyzer:
    def __init__(self):
        """Initialize the basketball analyzer with YOLO models."""
        try:
            # Load YOLO models
            self.basketball_model = YOLO('opencv-test/basketballmodel.pt')
            self.pose_model = YOLO('opencv-test/yolov8s-pose.pt')
            logger.info("YOLO models loaded successfully")
            
            # Initialize tracking variables
            self.ball_positions: List[Optional[Tuple[float, float]]] = []
            self.knee_positions: List[Optional[Tuple[float, float]]] = []
            self.hip_positions: List[Optional[Tuple[float, float]]] = []
            self.was_holding = False
            self.current_holder: Optional[int] = None
            self.holding_frames = 0
            self.traveling_detected = False
            self.last_announcement_time = 0
            
        except Exception as e:
            logger.error(f"Error initializing BasketballAnalyzer: {e}")
            raise

    def is_person_holding_ball_with_hands(self, ball_box: Tuple[float, float, float, float], 
                                        pose_keypoints: np.ndarray, threshold: float = 8) -> bool:
        """Check if a person is holding the basketball based on ball being close to keypoints."""
        if not ball_box or pose_keypoints is None:
            return False
        
        bx1, by1, bx2, by2 = ball_box[:4]
        ball_center_x = (bx1 + bx2) / 2
        ball_center_y = (by1 + by2) / 2
        
        # Check if ANY keypoint is inside or extremely close to the ball's bounding box
        for keypoint in pose_keypoints:
            if keypoint[2] > 0.2:  # Very low confidence threshold
                keypoint_x, keypoint_y = keypoint[0], keypoint[1]
                
                # Check if keypoint is inside the ball's bounding box
                if bx1 <= keypoint_x <= bx2 and by1 <= keypoint_y <= by2:
                    return True
                
                # Check if keypoint is extremely close to the ball's bounding box edges
                nearest_x = max(bx1, min(keypoint_x, bx2))
                nearest_y = max(by1, min(keypoint_y, by2))
                
                distance = np.sqrt((keypoint_x - nearest_x)**2 + (keypoint_y - nearest_y)**2)
                
                if distance < threshold:
                    return True
                
                # Additional check: distance from keypoint to ball center
                center_distance = np.sqrt((keypoint_x - ball_center_x)**2 + (keypoint_y - ball_center_y)**2)
                if center_distance < threshold * 2:
                    return True
        
        return False

    def get_person_center_from_pose(self, pose_keypoints: np.ndarray) -> Optional[Tuple[float, float]]:
        """Calculate the center position of a person based on pose keypoints."""
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

    def detect_traveling(self, ball_positions: List[Optional[Tuple[float, float]]], 
                        knee_positions: List[Optional[Tuple[float, float]]], 
                        holding_frames: int, travel_threshold: float = 600) -> bool:
        """Detect traveling based on ball movement and position relative to knees."""
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
            
            # Ball is above knees if ball Y is smaller than knee Y
            ball_above_knees = current_ball_y < current_knee_y
            
            # Traveling detected if ball is above knees and moving horizontally more than threshold
            if ball_above_knees and horizontal_movement > travel_threshold:
                return True
        
        return False

    def analyze_frame(self, frame: np.ndarray) -> Dict:
        """Analyze a single frame and return detection results."""
        try:
            # Detect basketballs using basketball model
            basketball_results = self.basketball_model(frame)
            
            # Get basketball detections
            ball_boxes = []
            for r in basketball_results:
                for box in r.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.basketball_model.names[class_id]
                    
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    confidence = float(box.conf[0])
                    
                    # Only include high-confidence detections
                    if confidence > 0.5:
                        ball_boxes.append((x1, y1, x2, y2, confidence))
            
            # Detect pose using pose model
            pose_results = self.pose_model(frame)
            
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
                self.ball_positions.append((ball_center_x, ball_center_y))
                
                # Keep only recent ball history (last 30 frames)
                if len(self.ball_positions) > 30:
                    self.ball_positions.pop(0)
                
                # Check which person is holding the ball using hand positions
                for i, pose_result in enumerate(pose_results):
                    if pose_result.keypoints is not None and len(pose_result.keypoints.data) > 0:
                        person_pose_keypoints = pose_result.keypoints.data[0]
                        
                        if self.is_person_holding_ball_with_hands(ball_boxes[0], person_pose_keypoints):
                            current_holding = True
                            current_holder_id = i
                            current_holder_pose = person_pose_keypoints
                            
                            # Get person center from pose keypoints
                            current_person_center = self.get_person_center_from_pose(person_pose_keypoints)
                            
                            # Get knee and hip positions for step counting
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
                self.knee_positions.append(current_knee_pos)
                self.hip_positions.append(current_hip_pos)
            else:
                self.knee_positions.append(None)
                self.hip_positions.append(None)
            
            # Keep only recent knee and hip history (last 30 frames)
            if len(self.knee_positions) > 30:
                self.knee_positions.pop(0)
                self.hip_positions.pop(0)
            
            # Update holding state and detect traveling
            events = []
            
            if current_holding and self.was_holding and current_holder_id == self.current_holder:
                # Same person has continuous possession
                self.holding_frames += 1
                
                # Check for traveling after some frames of holding
                if self.holding_frames > 5 and not self.traveling_detected:
                    if self.detect_traveling(self.ball_positions, self.knee_positions, self.holding_frames):
                        self.traveling_detected = True
                        events.append({
                            "type": "Violation",
                            "description": f"Traveling detected! Player {current_holder_id} moving with ball above knees",
                            "severity": "error",
                            "timestamp": time.time()
                        })
            else:
                # Possession changed or lost
                if current_holding and not self.was_holding:
                    # New possession
                    self.current_holder = current_holder_id
                    self.holding_frames = 1
                    self.traveling_detected = False
                    
                    events.append({
                        "type": "Info",
                        "description": f"Player {current_holder_id} gained possession",
                        "severity": "info",
                        "timestamp": time.time()
                    })
                    
                elif not current_holding and self.was_holding:
                    # Lost possession
                    events.append({
                        "type": "Info",
                        "description": f"Player {self.current_holder} lost possession",
                        "severity": "info",
                        "timestamp": time.time()
                    })
                    self.traveling_detected = False
            
            # Update previous state
            self.was_holding = current_holding
            
            # Prepare analysis results
            analysis_result = {
                "events": events,
                "current_holder": current_holder_id,
                "holding_frames": self.holding_frames,
                "traveling_detected": self.traveling_detected,
                "ball_detected": len(ball_boxes) > 0,
                "people_detected": len(pose_results),
                "ball_boxes": ball_boxes,
                "pose_results": len(pose_results)
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing frame: {e}")
            return {
                "events": [],
                "error": str(e)
            }

# Global analyzer instance
analyzer = None

async def websocket_handler(websocket, path):
    """Handle WebSocket connections for real-time video analysis."""
    global analyzer
    
    try:
        # Initialize analyzer if not already done
        if analyzer is None:
            analyzer = BasketballAnalyzer()
            logger.info("Basketball analyzer initialized")
        
        logger.info(f"New WebSocket connection established")
        
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data.get("type") == "frame":
                    # Decode base64 frame
                    frame_data = base64.b64decode(data["frame"].split(",")[1])
                    nparr = np.frombuffer(frame_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # Analyze the frame
                        analysis_result = analyzer.analyze_frame(frame)
                        
                        # Send analysis results back
                        await websocket.send(json.dumps({
                            "type": "analysis",
                            "data": analysis_result
                        }))
                    else:
                        logger.warning("Failed to decode frame")
                        
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")

async def start_websocket_server(host="localhost", port=8765):
    """Start the WebSocket server."""
    logger.info(f"Starting WebSocket server on {host}:{port}")
    async with websockets.serve(websocket_handler, host, port):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(start_websocket_server()) 