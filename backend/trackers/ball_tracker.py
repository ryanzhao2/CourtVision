from ultralytics import YOLO
import supervision as sv
import numpy as np
import pandas as pd
import sys 
sys.path.append('../')
from utils import read_stub, save_stub


class BallTracker:
    """
    A class that handles basketball detection and tracking using YOLO.

    This class provides methods to detect the ball in video frames, process detections
    in batches, and refine tracking results through filtering and interpolation.
    """
    def __init__(self, model_path):
        self.model = YOLO(model_path) 

    def detect_frames(self, frames):
        """
        Detect the ball in a sequence of frames using optimized batch processing.

        Args:
            frames (list): List of video frames to process.

        Returns:
            list: YOLO detection results for each frame.
        """
        batch_size = 1  # Process one frame at a time for maximum speed
        detections = [] 
        
        # Only process every 3rd frame for speed, then interpolate
        frame_skip = 3
        frames_to_process = frames[::frame_skip]
        total_frames = len(frames_to_process)
        
        print(f"    Processing {len(frames)} frames (sampling every {frame_skip}rd frame = {total_frames} frames)...")
        
        for i in range(0, len(frames_to_process), batch_size):
            frame_num = i // batch_size
            if frame_num % 20 == 0 or frame_num == total_frames - 1:
                print(f"    Frame {frame_num}/{total_frames} ({frame_num/total_frames*100:.1f}%)")
                
            detections_batch = self.model.predict(frames_to_process[i:i+batch_size], conf=0.5, verbose=False)
            detections += detections_batch
            
        # Interpolate detections for skipped frames
        print("    Interpolating detections for skipped frames...")
        all_detections = []
        for i in range(len(frames)):
            if i % frame_skip == 0:
                all_detections.append(detections[i // frame_skip])
            else:
                # Use the previous detection for skipped frames
                all_detections.append(detections[i // frame_skip])
        
        print("    ✅ Ball detection completed")
        return all_detections

    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None):
        """
        Get ball tracking results for a sequence of frames with optional caching.

        Args:
            frames (list): List of video frames to process.
            read_from_stub (bool): Whether to attempt reading cached results.
            stub_path (str): Path to the cache file.

        Returns:
            list: List of dictionaries containing ball tracking information for each frame.
        """
        tracks = read_stub(read_from_stub,stub_path)
        if tracks is not None:
            if len(tracks) == len(frames):
                return tracks

        detections = self.detect_frames(frames)

        tracks=[]

        for frame_num, detection in enumerate(detections):
            cls_names = detection.names
            cls_names_inv = {v:k for k,v in cls_names.items()}

            # Covert to supervision Detection format
            detection_supervision = sv.Detections.from_ultralytics(detection)

            tracks.append({})
            chosen_bbox =None
            max_confidence = 0
            
            # Debug: Print detected classes for first few frames
            if frame_num < 3:
                detected_classes = [cls_names.get(cls_id, f"unknown_{cls_id}") for cls_id in detection_supervision.class_id]
                if detected_classes:
                    print(f"    Frame {frame_num} detected classes: {detected_classes}")
            
            for frame_detection in detection_supervision:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]
                confidence = frame_detection[2]
                
                # Use 'sports ball' class or any small object that could be a ball
                # yolov8n.pt has classes like 'sports ball', 'baseball', etc.
                ball_classes = ['sports ball', 'baseball', 'tennis ball', 'basketball']
                class_name = cls_names.get(cls_id, f"unknown_{cls_id}")
                
                # Check if it's a known ball class
                if any(cls_name in cls_names_inv and cls_id == cls_names_inv[cls_name] for cls_name in ball_classes):
                    if max_confidence < confidence:
                        chosen_bbox = bbox
                        max_confidence = confidence
                
                # Also check for any small, high-confidence objects that could be a ball
                # (small bounding box area, high confidence)
                bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                if (confidence > 0.7 and  # High confidence
                    bbox_area < 5000 and   # Small object (less than 5000 pixels)
                    bbox_area > 100):      # But not too small (more than 100 pixels)
                    if max_confidence < confidence:
                        chosen_bbox = bbox
                        max_confidence = confidence
                        print(f"    Frame {frame_num} detected potential ball: {class_name} (confidence: {confidence:.2f}, area: {bbox_area:.0f})")

            if chosen_bbox is not None:
                tracks[frame_num][1] = {"bbox":chosen_bbox}

        save_stub(stub_path,tracks)
        
        return tracks

    def remove_wrong_detections(self,ball_positions):
        """
        Filter out incorrect ball detections based on maximum allowed movement distance.

        Args:
            ball_positions (list): List of detected ball positions across frames.

        Returns:
            list: Filtered ball positions with incorrect detections removed.
        """
        
        maximum_allowed_distance = 25
        last_good_frame_index = -1

        for i in range(len(ball_positions)):
            current_box = ball_positions[i].get(1, {}).get('bbox', [])

            if len(current_box) == 0:
                continue

            if last_good_frame_index == -1:
                # First valid detection
                last_good_frame_index = i
                continue

            last_good_box = ball_positions[last_good_frame_index].get(1, {}).get('bbox', [])
            frame_gap = i - last_good_frame_index
            adjusted_max_distance = maximum_allowed_distance * frame_gap

            if np.linalg.norm(np.array(last_good_box[:2]) - np.array(current_box[:2])) > adjusted_max_distance:
                ball_positions[i] = {}
            else:
                last_good_frame_index = i

        return ball_positions

    def interpolate_ball_positions(self,ball_positions):
        """
        Interpolate missing ball positions to create smooth tracking results.

        Args:
            ball_positions (list): List of ball positions with potential gaps.

        Returns:
            list: List of ball positions with interpolated values filling the gaps.
        """
        ball_positions = [x.get(1,{}).get('bbox',[]) for x in ball_positions]
        
        # Check if we have any valid ball detections
        valid_detections = [pos for pos in ball_positions if len(pos) == 4]
        
        if not valid_detections:
            print("    Warning: No ball detections found. Creating empty ball tracks.")
            # Return empty ball positions for all frames
            return [{1: {"bbox": []}} for _ in range(len(ball_positions))]
        
        # Fill empty detections with None for interpolation
        ball_positions_filled = []
        for pos in ball_positions:
            if len(pos) == 4:
                ball_positions_filled.append(pos)
            else:
                ball_positions_filled.append([None, None, None, None])
        
        df_ball_positions = pd.DataFrame(ball_positions_filled, columns=['x1','y1','x2','y2'])

        # Interpolate missing values
        df_ball_positions = df_ball_positions.interpolate()
        df_ball_positions = df_ball_positions.bfill()
        df_ball_positions = df_ball_positions.ffill()  # Forward fill any remaining NaNs

        ball_positions = [{1: {"bbox": x if not any(pd.isna(val) for val in x) else []}} for x in df_ball_positions.to_numpy().tolist()]
        return ball_positions