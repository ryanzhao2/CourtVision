from collections import defaultdict
from typing import Dict, Any, List, Optional
import numpy as np

# Define a type hint for the player state for clarity and type safety
PlayerState = Dict[str, Any]

class ViolationDetector:
    """
    Detects travel and double-dribble violations using more precise, state-based logic.
    - Holding: The ball is stationary near a player for a set duration.
    - Dribble Start: The player pushes the ball downwards from a held position.
    - Travel: The player moves while in a confirmed 'holding' state.
    - Double Dribble: The player starts a new dribble after having stopped a previous one.
    """
    def __init__(self, fps: float, travel_threshold: int = 30, hold_duration_seconds: float = 0.35, hold_stationary_threshold: float = 8.0, dribble_start_stability_threshold: float = 5.0):
        """
        Initializes the violation detector with configurable, time-based thresholds.
        
        Args:
            fps (float): The frames per second of the input video.
            hold_duration_seconds (float): The time in seconds the ball must be stationary to be considered 'held'.
        """
        self.player_states: Dict[int, PlayerState] = defaultdict(lambda: {
            'action': 'no_ball', 'dribble_stopped': False, 'last_pos': None, 'violation_committed': False
        })
        self.fps = fps
        self.travel_threshold = travel_threshold
        # Calculate the number of frames required to confirm a hold, based on time
        self.hold_history_len = int(hold_duration_seconds * self.fps)
        self.hold_stationary_threshold = hold_stationary_threshold
        self.dribble_start_stability_threshold = dribble_start_stability_threshold

    def _get_ball_center(self, ball_bbox: List[float]) -> Optional[np.ndarray]:
        return np.array([(ball_bbox[0] + ball_bbox[2]) / 2, (ball_bbox[1] + ball_bbox[3]) / 2]) if ball_bbox else None

    def _get_player_center(self, player_bbox: List[float]) -> Optional[np.ndarray]:
        return np.array([(player_bbox[0] + player_bbox[2]) / 2, (player_bbox[1] + player_bbox[3]) / 2]) if player_bbox else None

    def _is_holding(self, ball_pos_history: List[Optional[np.ndarray]]) -> bool:
        if len(ball_pos_history) < self.hold_history_len: return False
        recent_pos = [p for p in ball_pos_history[-self.hold_history_len:] if p is not None]
        if len(recent_pos) < self.hold_history_len: return False
        max_dist = np.max([np.linalg.norm(p - recent_pos[0]) for p in recent_pos])
        return bool(max_dist < self.hold_stationary_threshold)

    def _is_starting_dribble(self, ball_pos_history: List[Optional[np.ndarray]]) -> bool:
        if len(ball_pos_history) < 4: return False
        p1, p2, p3, p4 = ball_pos_history[-4:]
        if any(p is None for p in [p1, p2, p3, p4]): return False

        # Add asserts to help the type checker understand the types are not None
        assert p1 is not None and p2 is not None and p3 is not None and p4 is not None
        
        is_stable_before = abs(p2[1] - p1[1]) < self.dribble_start_stability_threshold
        is_moving_down = p4[1] > p3[1] + 1 and p3[1] > p2[1] + 1
        
        return is_stable_before and is_moving_down

    def detect_violations(self, player_tracks: List[Dict[int, Any]], ball_tracks: List[Dict[int, Any]], ball_aquisition: List[int]) -> tuple[List[int], List[int]]:
        num_frames = len(player_tracks)
        travels, double_dribbles = [0] * num_frames, [0] * num_frames
        total_travels, total_double_dribbles = 0, 0
        ball_pos_history: List[Optional[np.ndarray]] = []

        for frame_num in range(num_frames):
            ball_bbox = ball_tracks[frame_num].get(1, {}).get('bbox', [])
            ball_pos_history.append(self._get_ball_center(ball_bbox))
            
            player_with_ball = ball_aquisition[frame_num]
            
            for player_id in list(self.player_states.keys()):
                if player_id != player_with_ball:
                    if self.player_states[player_id]['action'] != 'no_ball':
                        self.player_states[player_id]['dribble_stopped'] = True
                    self.player_states[player_id]['action'] = 'no_ball'
                    self.player_states[player_id]['violation_committed'] = False
                    self.player_states[player_id]['last_pos'] = None

            if player_with_ball != -1:
                state = self.player_states[player_with_ball]
                player_pos = self._get_player_center(player_tracks[frame_num].get(player_with_ball, {}).get('bbox'))
                if player_pos is None: continue

                is_holding = self._is_holding(ball_pos_history)
                is_starting_dribble = self._is_starting_dribble(ball_pos_history)

                if is_starting_dribble and state['dribble_stopped'] and not state['violation_committed']:
                    total_double_dribbles += 1
                    state['violation_committed'] = True
                    state['dribble_stopped'] = False
                
                if is_holding:
                    if state['action'] != 'holding': # Just entered holding state
                        state['dribble_stopped'] = True
                        state['last_pos'] = player_pos
                    state['action'] = 'holding'
                else:
                    state['action'] = 'transient'
                    state['last_pos'] = None

                # Travel check is now only when holding
                if state['action'] == 'holding' and state['last_pos'] is not None and not state['violation_committed']:
                    distance = np.linalg.norm(player_pos - state['last_pos'])
                    if distance > self.travel_threshold:
                        total_travels += 1
                        state['violation_committed'] = True
                        state['last_pos'] = player_pos
            
            travels[frame_num] = total_travels
            double_dribbles[frame_num] = total_double_dribbles
        
        print("    ✅ Finalized violation detection complete.")
        return travels, double_dribbles 