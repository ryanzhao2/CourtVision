import cv2

class FrameNumberDrawer:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 2
        self.color = (0, 255, 0)
        self.thickness = 3

    def draw(self, video_frames):
        # The drawing logic is now disabled to hide the frame number.
        # To re-enable, uncomment the line in the loop below.
        output_video_frames = []
        for frame in video_frames:
            # cv2.putText(frame, str(frame_num), (10, 50), self.font, self.font_scale, self.color, self.thickness)
            output_video_frames.append(frame)
        return output_video_frames