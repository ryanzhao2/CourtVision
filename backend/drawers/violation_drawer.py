import cv2
import numpy as np

class ViolationDrawer:
    """
    Draws a dedicated panel on video frames to display violation statistics
    (travels and double dribbles).
    """
    def __init__(self):
        pass

    def draw(self, video_frames, travels, double_dribbles):
        """
        Draws the violation counts on each frame in a separate panel.

        Args:
            video_frames (list): The frames of the video.
            travels (list): A list with the cumulative travel count for each frame.
            double_dribbles (list): A list with the cumulative double dribble count for each frame.

        Returns:
            list: The video frames with the violation panel drawn on them.
        """
        output_video_frames = []
        for frame_num, frame in enumerate(video_frames):
            frame = frame.copy()
            
            travel_count = travels[frame_num]
            double_dribble_count = double_dribbles[frame_num]

            # Draw a semi-transparent rectangle for the violation panel
            overlay = frame.copy()
            font_scale = 0.8
            font_thickness = 2
            
            frame_height, frame_width, _ = frame.shape
            
            # Position the panel above the main summary panel
            rect_x1 = int(frame_width * 0.05)
            rect_y1 = int(frame_height * 0.70)
            rect_x2 = int(frame_width * 0.50)
            rect_y2 = int(frame_height * 0.77)
            
            cv2.rectangle(overlay, (rect_x1, rect_y1), (rect_x2, rect_y2), (255, 255, 255), -1)
            alpha = 0.6
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            
            # Text for the panel
            text_y = int(frame_height * 0.75)
            text_x = int(frame_width * 0.08)
            
            violation_text = f"Travels: {travel_count}    Double Dribbles: {double_dribble_count}"
            cv2.putText(frame, violation_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), font_thickness)

            output_video_frames.append(frame)

        return output_video_frames 