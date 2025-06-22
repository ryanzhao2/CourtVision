import numpy as np
from typing import List, Optional, Dict, Any

class ShotDetector:
    """
    Detects shot attempts by analyzing if the ball's trajectory is directed towards the hoop.
    A shot is identified by upward movement and a projected path that intersects with the hoop.
    """
    def __init__(self, trajectory_frames: int = 5, min_trajectory_points: int = 3):
        """
        Initializes the shot detector.

        Args:
            trajectory_frames (int): The number of recent frames to use for trajectory calculation.
            min_trajectory_points (int): The minimum number of ball positions required to form a valid trajectory.
        """
        self.trajectory_frames = trajectory_frames
        self.min_trajectory_points = min_trajectory_points

    def _get_ball_center(self, ball_bbox: List[float]) -> Optional[np.ndarray]:
        return np.array([(ball_bbox[0] + ball_bbox[2]) / 2, (ball_bbox[1] + ball_bbox[3]) / 2]) if ball_bbox else None
    
    def _get_hoop_center(self, hoop_bbox: List[float]) -> Optional[np.ndarray]:
        return np.array([(hoop_bbox[0] + hoop_bbox[2]) / 2, (hoop_bbox[1] + hoop_bbox[3]) / 2]) if hoop_bbox else None

    def _line_intersects_box(self, p1: np.ndarray, p2: np.ndarray, box: List[float]) -> bool:
        """
        Checks if the line segment defined by p1-p2 intersects with a bounding box.
        This is a simplified check and can be improved with more robust geometry libraries if needed.
        """
        box_min = np.array([box[0], box[1]])
        box_max = np.array([box[2], box[3]])
        
        # Simple check: if either point is inside the box, we count it.
        if (box_min[0] < p1[0] < box_max[0] and box_min[1] < p1[1] < box_max[1]) or \
           (box_min[0] < p2[0] < box_max[0] and box_min[1] < p2[1] < box_max[1]):
            return True
        return False # A full line-segment intersection algorithm would be more robust.

    def detect_shots(self, ball_tracks: List[Dict[int, Any]], ball_aquisition: List[int], hoop_positions: List[Optional[List[float]]]) -> List[int]:
        """
        Processes ball and hoop data to detect shot attempts based on trajectory.
        """
        shots = [-1] * len(ball_tracks)
        ball_pos_history: List[Optional[np.ndarray]] = []

        for frame_num in range(len(ball_tracks)):
            ball_bbox = ball_tracks[frame_num].get(1, {}).get('bbox', [])
            ball_pos = self._get_ball_center(ball_bbox)
            ball_pos_history.append(ball_pos)
            
            if frame_num >= len(hoop_positions):
                continue
            hoop_bbox = hoop_positions[frame_num]

            if ball_pos is None or hoop_bbox is None or frame_num < self.trajectory_frames:
                continue

            # Check for a valid recent trajectory
            recent_ball_positions = [p for p in ball_pos_history[-self.trajectory_frames:] if p is not None]
            if len(recent_ball_positions) < self.min_trajectory_points:
                continue

            # The trajectory is defined by the first and last points in the window
            p_start = recent_ball_positions[0]
            p_end = recent_ball_positions[-1]

            # Condition 1: Is the ball moving upwards?
            is_moving_up = p_end[1] < p_start[1]
            
            # Condition 2: Is the trajectory aimed at the hoop?
            # Project the trajectory forward
            direction_vector = p_end - p_start
            # Don't project if the ball is barely moving
            if np.linalg.norm(direction_vector) < 2: continue 

            # Project a point far along the trajectory line
            p_projected = p_end + direction_vector * 5 

            is_aimed_at_hoop = self._line_intersects_box(p_end, p_projected, hoop_bbox)
            
            if is_moving_up and is_aimed_at_hoop:
                player_who_shot = ball_aquisition[frame_num - 1]
                if player_who_shot != -1:
                    shots[frame_num] = player_who_shot

        print("    ✅ Trajectory-based shot detection complete.")
        return shots 