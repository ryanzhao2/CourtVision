import cv2
import numpy as np
import base64
import json
import asyncio
import websockets
import time
import logging
import sys
import os
from pathlib import Path

# Add the opencv-test directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'opencv-test'))

# Import the existing person_ball_detection functions
from person_ball_detection import (
    is_person_holding_ball_with_hands,
    get_person_center_from_pose,
    detect_steps,
    detect_traveling
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasketballAnalysisServer:
    def __init__(self):
        """Initialize the basketball analysis server with YOLO models."""
        try:
            from ultralytics import YOLO
            
            # Load YOLO models from the opencv-test directory
            opencv_test_dir = os.path.join(os.path.dirname(__file__), 'opencv-test')
            self.basketball_model = YOLO(os.path.join(opencv_test_dir, 'basketballmodel.pt'))
            self.pose_model = YOLO(os.path.join(opencv_test_dir, 'yolov8s-pose.pt'))
            
            logger.info("YOLO models loaded successfully")
            
            # Initialize tracking variables (same as in person_ball_detection.py)
            self.ball_positions = []
            self.knee_positions = []
            self.hip_positions = []
            self.was_holding = False
            self.current_holder = None
            self.holding_frames = 0
            self.traveling_detected = False
            self.last_announcement_time = 0
            
        except Exception as e:
            logger.error(f"Error initializing BasketballAnalysisServer: {e}")
            raise

    def analyze_frame(self, frame):
        """Analyze a single frame using the existing person_ball_detection logic."""
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
                        
                        if is_person_holding_ball_with_hands(ball_boxes[0], person_pose_keypoints):
                            current_holding = True
                            current_holder_id = i
                            current_holder_pose = person_pose_keypoints
                            
                            # Get person center from pose keypoints
                            current_person_center = get_person_center_from_pose(person_pose_keypoints)
                            
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
                    if detect_traveling(self.ball_positions, self.knee_positions, self.holding_frames):
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
                "pose_results": len(pose_results),
                "visual_data": {
                    "ball_boxes": ball_boxes,
                    "pose_keypoints": [],
                    "current_holder_pose": None,
                    "current_knee_pos": current_knee_pos,
                    "current_hip_pos": current_hip_pos,
                    "current_person_center": current_person_center
                }
            }
            
            # Add pose keypoints for all detected people
            if pose_results:
                for pose_result in pose_results:
                    if pose_result.keypoints is not None and len(pose_result.keypoints.data) > 0:
                        # Convert keypoints to list format for JSON serialization
                        keypoints = pose_result.keypoints.data[0].cpu().numpy().tolist()
                        analysis_result["visual_data"]["pose_keypoints"].append(keypoints)
                
                # Add current holder's pose if available
                if current_holder_pose is not None:
                    analysis_result["visual_data"]["current_holder_pose"] = current_holder_pose.cpu().numpy().tolist()
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing frame: {e}")
            return {
                "events": [],
                "error": str(e)
            }

# Global server instance
analysis_server = None

async def websocket_handler(websocket, path):
    """Handle WebSocket connections for real-time video analysis."""
    global analysis_server
    
    try:
        # Initialize server if not already done
        if analysis_server is None:
            analysis_server = BasketballAnalysisServer()
            logger.info("Basketball analysis server initialized")
        
        logger.info(f"New WebSocket connection established")
        
        # Send initial connection confirmation
        await websocket.send(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "Basketball analysis server ready"
        }))
        
        # Keep connection alive and process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data.get("type") == "frame":
                    # Decode base64 frame
                    frame_data = base64.b64decode(data["frame"].split(",")[1])
                    nparr = np.frombuffer(frame_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # Analyze the frame using the existing person_ball_detection logic
                        analysis_result = analysis_server.analyze_frame(frame)
                        
                        # Send analysis results back
                        await websocket.send(json.dumps({
                            "type": "analysis",
                            "data": analysis_result
                        }))
                    else:
                        logger.warning("Failed to decode frame")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Failed to decode frame"
                        }))
                        
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Invalid JSON: {str(e)}"
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Processing error: {str(e)}"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")

async def start_websocket_server(host="localhost", port=8765):
    """Start the WebSocket server."""
    logger.info(f"Starting Basketball Analysis WebSocket Server on {host}:{port}")
    logger.info("This server integrates with person_ball_detection.py for real-time analysis")
    async with websockets.serve(websocket_handler, host, port):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(start_websocket_server()) 