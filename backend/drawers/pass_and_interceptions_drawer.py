import cv2
import numpy as np

class PassInterceptionDrawer:
    """
    A class responsible for calculating and drawing pass, interception, and ball control statistics
    on a sequence of video frames.
    """
    def __init__(self):
        self.team_ball_control = []

    def get_team_ball_control(self,player_assignment,ball_aquisition):
        """
        Calculate which team has ball control for each frame.
        """
        team_ball_control_frame = -1
        if ball_aquisition != -1 and ball_aquisition in player_assignment:
            if player_assignment[ball_aquisition] == 1:
                team_ball_control_frame = 1
            else:
                team_ball_control_frame = 2
        
        self.team_ball_control.append(team_ball_control_frame)


    def get_stats(self, passes, interceptions):
        """
        Calculate the number of passes and interceptions for Team 1 and Team 2.
        """
        team1_passes = (passes == 1).sum()
        team2_passes = (passes == 2).sum()
        team1_interceptions = (interceptions == 1).sum()
        team2_interceptions = (interceptions == 2).sum()
                
        return team1_passes, team2_passes, team1_interceptions, team2_interceptions

    def draw(self, video_frames, passes, interceptions, player_assignment, ball_aquisition, shot_player_ids):
        """
        Draw pass, interception, and shot statistics on a list of video frames.
        """
        output_video_frames = []
        passes = np.array(passes)
        interceptions = np.array(interceptions)
        
        for frame_num, frame in enumerate(video_frames):
            if frame_num == 0:
                output_video_frames.append(frame)
                continue

            self.get_team_ball_control(player_assignment[frame_num], ball_aquisition[frame_num])
            
            frame_drawn = self.draw_frame(frame, frame_num, passes, interceptions, shot_player_ids, player_assignment)
            output_video_frames.append(frame_drawn)

        return output_video_frames
    
    def draw_frame(self, frame, frame_num, passes, interceptions, shot_player_ids, player_assignment):
        """
        Draw a semi-transparent overlay of all statistics on a single frame.
        """
        overlay = frame.copy()
        font_scale = 0.8
        font_thickness = 2
        frame_height, frame_width = overlay.shape[:2]
        rect_x1 = int(frame_width * 0.05) 
        rect_y1 = int(frame_height * 0.82)
        rect_x2 = int(frame_width * 0.95)  
        rect_y2 = int(frame_height * 0.95)

        cv2.rectangle(overlay, (rect_x1, rect_y1), (rect_x2, rect_y2), (255,255,255), -1)
        alpha = 0.6
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Calculate cumulative stats
        team1_passes, team2_passes, team1_interceptions, team2_interceptions = self.get_stats(passes[:frame_num+1], interceptions[:frame_num+1])
        
        # Calculate shot stats
        team1_shots, team2_shots = 0, 0
        for i in range(frame_num + 1):
            player_id = shot_player_ids[i]
            if player_id != -1:
                team = player_assignment[i].get(player_id)
                if team == 1:
                    team1_shots += 1
                elif team == 2:
                    team2_shots += 1

        # Text positions
        text_y1 = int(frame_height * 0.87)  
        text_y2 = int(frame_height * 0.93)
        
        text_x_team = int(frame_width * 0.08)
        text_x_passes = int(frame_width * 0.22)
        text_x_interceptions = int(frame_width * 0.45)
        text_x_shots = int(frame_width * 0.75)

        # Team 1 Stats
        cv2.putText(frame, f"Team 1:", (text_x_team, text_y1), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), font_thickness)
        cv2.putText(frame, f"Passes: {team1_passes}", (text_x_passes, text_y1), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), font_thickness)
        cv2.putText(frame, f"Interceptions: {team1_interceptions}", (text_x_interceptions, text_y1), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), font_thickness)
        cv2.putText(frame, f"Shots: {team1_shots}", (text_x_shots, text_y1), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), font_thickness)
        
        # Team 2 Stats
        cv2.putText(frame, f"Team 2:", (text_x_team, text_y2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), font_thickness)
        cv2.putText(frame, f"Passes: {team2_passes}", (text_x_passes, text_y2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), font_thickness)
        cv2.putText(frame, f"Interceptions: {team2_interceptions}", (text_x_interceptions, text_y2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), font_thickness)
        cv2.putText(frame, f"Shots: {team2_shots}", (text_x_shots, text_y2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), font_thickness)

        return frame