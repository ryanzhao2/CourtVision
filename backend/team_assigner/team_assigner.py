from PIL import Image
import cv2
import numpy as np
import sys 
sys.path.append('../')
from utils import read_stub, save_stub

class TeamAssigner:
    """
    A class that assigns players to teams based on their jersey colors using fast color analysis.

    The class uses simple color analysis to classify players into teams based on their
    jersey colors. It maintains a consistent team assignment for each player across frames.

    Attributes:
        team_colors (dict): Dictionary storing team color information.
        player_team_dict (dict): Dictionary mapping player IDs to their team assignments.
        team_1_colors (list): List of colors associated with Team 1 (light colors).
        team_2_colors (list): List of colors associated with Team 2 (dark colors).
    """
    def __init__(self,
                 team_1_colors=None,
                 team_2_colors=None):
        """
        Initialize the TeamAssigner with specified team colors.

        Args:
            team_1_colors (list): List of HSV color ranges for Team 1 (light colors).
            team_2_colors (list): List of HSV color ranges for Team 2 (dark colors).
        """
        self.team_colors = {}
        self.player_team_dict = {}        
    
        # Default color ranges for light vs dark jerseys
        if team_1_colors is None:
            self.team_1_colors = [
                # White/light colors
                ([0, 0, 180], [180, 30, 255]),  # High value, low saturation
                ([0, 0, 200], [180, 20, 255]),  # Very light colors
            ]
        else:
            self.team_1_colors = team_1_colors
            
        if team_2_colors is None:
            self.team_2_colors = [
                # Dark colors (blue, red, green, etc.)
                ([0, 50, 0], [180, 255, 150]),   # Low value, high saturation
                ([100, 50, 0], [140, 255, 150]), # Blue range
                ([0, 50, 0], [20, 255, 150]),    # Red range
            ]
        else:
            self.team_2_colors = team_2_colors

    def get_player_color_fast(self, frame, bbox):
        """
        Fast color analysis of a player's jersey using HSV color space.

        Args:
            frame (numpy.ndarray): The video frame containing the player.
            bbox (tuple): Bounding box coordinates of the player.

        Returns:
            str: The classified jersey color ('light' or 'dark').
        """
        try:
            # Extract player region
            x1, y1, x2, y2 = map(int, bbox)
            player_region = frame[y1:y2, x1:x2]
            
            if player_region.size == 0:
                return 'light'  # Default for empty regions
            
            # Convert to HSV
            hsv = cv2.cvtColor(player_region, cv2.COLOR_BGR2HSV)
            
            # Calculate average color in the center region (avoid edges)
            height, width = hsv.shape[:2]
            center_h = height // 2
            center_w = width // 2
            center_size = min(height, width) // 3
            
            y_start = max(0, center_h - center_size)
            y_end = min(height, center_h + center_size)
            x_start = max(0, center_w - center_size)
            x_end = min(width, center_w + center_size)
            
            center_region = hsv[y_start:y_end, x_start:x_end]
            
            if center_region.size == 0:
                return 'light'
            
            # Calculate average HSV values
            avg_hsv = np.mean(center_region, axis=(0, 1))
            h, s, v = avg_hsv
            
            # Classify based on value (brightness) and saturation
            if v > 160 and s < 60:  # High value, low saturation = light
                return 'light'
            elif v < 100 and s > 60:  # Low value, high saturation = dark
                return 'dark'
            elif v > 140:  # High value regardless of saturation = light
                return 'light'
            elif v < 120:  # Low value regardless of saturation = dark
                return 'dark'
            else:
                # Use saturation as tiebreaker for medium values
                return 'light' if s < 80 else 'dark'
                
        except Exception as e:
            return 'light'  # Default for any errors

    def get_player_team(self, frame, player_bbox, player_id):
        """
        Gets the team assignment for a player, using cached results if available.

        Args:
            frame (numpy.ndarray): The video frame containing the player.
            player_bbox (tuple): Bounding box coordinates of the player.
            player_id (int): Unique identifier for the player.

        Returns:
            int: Team ID (1 or 2) assigned to the player.
        """
        # Use cached result if available
        if player_id in self.player_team_dict:
            return self.player_team_dict[player_id]

        # Only process if bbox is valid
        if len(player_bbox) != 4 or player_bbox[2] <= player_bbox[0] or player_bbox[3] <= player_bbox[1]:
            # Default to team 1 for invalid bboxes
            self.player_team_dict[player_id] = 1
            return 1

        try:
            player_color = self.get_player_color_fast(frame, player_bbox)
            team_id = 2 if player_color == 'dark' else 1
            self.player_team_dict[player_id] = team_id
            return team_id
        except Exception as e:
            # If classification fails, default to team 1
            self.player_team_dict[player_id] = 1
            return 1

    def get_player_teams_across_frames(self, video_frames, player_tracks, read_from_stub=False, stub_path=None):
        """
        Processes video frames to assign teams to players, with aggressive optimization.

        Args:
            video_frames (list): List of video frames to process.
            player_tracks (list): List of player tracking information for each frame.
            read_from_stub (bool): Whether to attempt reading cached results.
            stub_path (str): Path to the cache file.

        Returns:
            list: List of dictionaries mapping player IDs to team assignments for each frame.
        """
        
        player_assignment = read_stub(read_from_stub, stub_path)
        if player_assignment is not None:
            if len(player_assignment) == len(video_frames):
                print("    ✅ Loaded team assignments from stub")
                return player_assignment

        print("    🔄 Running ultra-fast team assignment...")
        # No model loading needed for fast color analysis

        player_assignment = []
        total_frames = len(player_tracks)
        
        print(f"    Processing {total_frames} frames (sampling every 10th frame)...")
        
        # Process every 10th frame instead of 30th for better accuracy
        sample_interval = 10
        sampled_frames = []
        sampled_assignments = []
        
        for frame_num in range(0, total_frames, sample_interval):
            if frame_num % 100 == 0:
                print(f"    Sample frame {frame_num}/{total_frames} ({frame_num/total_frames*100:.1f}%)")
            
            # Reset player team dict every 200 frames to handle new players
            if frame_num % 200 == 0:
                self.player_team_dict = {}

            frame_assignment = {}
            for player_id, track in player_tracks[frame_num].items():
                team = self.get_player_team(video_frames[frame_num],   
                                                    track['bbox'],
                                                    player_id)
                frame_assignment[player_id] = team
            
            sampled_frames.append(frame_num)
            sampled_assignments.append(frame_assignment)
        
        # Interpolate assignments for all frames
        print("    Interpolating team assignments for all frames...")
        for frame_num in range(total_frames):
            # Find the closest sampled frame
            closest_sample_idx = min(range(len(sampled_frames)), 
                                   key=lambda i: abs(sampled_frames[i] - frame_num))
            closest_frame = sampled_frames[closest_sample_idx]
            closest_assignment = sampled_assignments[closest_sample_idx]
            
            # Use the assignment from the closest sampled frame
            player_assignment.append(closest_assignment.copy())
        
        print("    ✅ Ultra-fast team assignment completed")
        save_stub(stub_path, player_assignment)

        return player_assignment