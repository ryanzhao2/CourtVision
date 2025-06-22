import cv2
import numpy as np

class HoopDrawer:
    """
    A drawer class responsible for drawing detected hoops on video frames.
    """
    
    def __init__(self, color=(0, 255, 255), thickness=3, radius=8):
        """
        Initialize the HoopDrawer.
        
        Args:
            color (tuple): BGR color for the hoop (default: cyan)
            thickness (int): Line thickness for the hoop outline
            radius (int): Radius of the hoop center point
        """
        self.color = color
        self.thickness = thickness
        self.radius = radius

    def draw(self, video_frames, hoop_positions):
        """
        Draw hoops on each video frame based on detected positions.
        
        Args:
            video_frames (list): A list of video frames (as NumPy arrays)
            hoop_positions (list): A list of hoop bounding boxes for each frame
                                 Each element is either None or [x1, y1, x2, y2]
        
        Returns:
            list: A list of processed video frames with hoops drawn on them
        """
        output_video_frames = []
        
        for frame_num, frame in enumerate(video_frames):
            frame = frame.copy()
            
            # Get hoop position for this frame
            if frame_num < len(hoop_positions) and hoop_positions[frame_num] is not None:
                hoop_bbox = hoop_positions[frame_num]
                
                # Draw hoop bounding box
                x1, y1, x2, y2 = map(int, hoop_bbox)
                cv2.rectangle(frame, (x1, y1), (x2, y2), self.color, self.thickness)
                
                # Draw hoop center point
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                cv2.circle(frame, (center_x, center_y), self.radius, self.color, -1)
                
                # Add "HOOP" label
                label_x = x1
                label_y = y1 - 10 if y1 > 20 else y2 + 20
                cv2.putText(frame, "HOOP", (label_x, label_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.color, 2)
            
            output_video_frames.append(frame)
        
        return output_video_frames 