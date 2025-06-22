import os
import argparse
from utils import read_video, save_video
from trackers import PlayerTracker, BallTracker
from team_assigner import TeamAssigner
from ball_aquisition import BallAquisitionDetector
from pass_and_interception_detector import PassAndInterceptionDetector
from violation_detector import ViolationDetector
from shot_detector import ShotDetector
from hoop_detector import HoopDetector
from event_collector import EventCollector
from drawers import (
    PlayerTracksDrawer, 
    BallTracksDrawer,
    CourtKeypointDrawer,
    FrameNumberDrawer,
    PassInterceptionDrawer,
    ViolationDrawer,
    HoopDrawer
)
from configs import(
    STUBS_DEFAULT_PATH,
    PLAYER_DETECTOR_PATH,
    BALL_DETECTOR_PATH,
    HOOP_DETECTOR_PATH,
    OUTPUT_VIDEO_PATH
)

def parse_args():
    parser = argparse.ArgumentParser(description='Basketball Video Analysis')
    parser.add_argument('input_video', type=str, help='Path to input video file')
    parser.add_argument('--output_video', type=str, default=OUTPUT_VIDEO_PATH, 
                        help='Path to output video file')
    parser.add_argument('--stub_path', type=str, default=STUBS_DEFAULT_PATH,
                        help='Path to stub directory')
    parser.add_argument('--max_frames', type=int, default=None,
                        help='Maximum number of frames to process (for faster testing)')
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("🚀 Starting Basketball Video Analysis...")
    print(f"📹 Input video: {args.input_video}")
    print(f"💾 Output video: {args.output_video}")
    print(f"📁 Stub path: {args.stub_path}")
    print()
    
    # Read Video
    print("📖 Reading video file...")
    video_frames, fps = read_video(args.input_video)
    print(f"✅ Video loaded: {len(video_frames)} frames at {fps:.2f} FPS")
    
    # Calculate video duration
    video_duration = len(video_frames) / fps if fps > 0 else 0
    print(f"⏱️ Video duration: {video_duration:.2f} seconds")
    
    # Limit frames for faster testing
    if args.max_frames and args.max_frames < len(video_frames):
        video_frames = video_frames[:args.max_frames]
        print(f"🔄 Limited to {len(video_frames)} frames for faster testing")
    
    print()
    
    ## Initialize Tracker
    print("🔧 Initializing trackers...")
    player_tracker = PlayerTracker(PLAYER_DETECTOR_PATH)
    ball_tracker = BallTracker(BALL_DETECTOR_PATH)
    print("✅ Trackers initialized")
    print()


    # Run Detectors
    print("🎯 Running player detection and tracking...")
    player_tracks = player_tracker.get_object_tracks(video_frames,
                                       read_from_stub=True,
                                       stub_path=os.path.join(args.stub_path, 'player_track_stubs.pkl')
                                      )
    print("✅ Player tracking completed")
    
    print("🏀 Running ball detection and tracking...")
    ball_tracks = ball_tracker.get_object_tracks(video_frames,
                                                 read_from_stub=True,
                                                 stub_path=os.path.join(args.stub_path, 'ball_track_stubs.pkl')
                                                )
    print("✅ Ball tracking completed")
    
    # Detect Hoop
    print("🏀 Detecting hoop...")
    hoop_detector = HoopDetector(HOOP_DETECTOR_PATH)
    hoop_positions = hoop_detector.get_hoop_positions(video_frames,
                                                     read_from_stub=True,
                                                     stub_path=os.path.join(args.stub_path, 'hoop_positions_stub.pkl')
                                                     )
    print("✅ Hoop detection complete")
    print()

    # Remove Wrong Ball Detections
    print("🧹 Cleaning ball detections...")
    ball_tracks = ball_tracker.remove_wrong_detections(ball_tracks)
    print("✅ Wrong ball detections removed")
    
    # Interpolate Ball Tracks
    print("📈 Interpolating ball positions...")
    ball_tracks = ball_tracker.interpolate_ball_positions(ball_tracks)
    print("✅ Ball positions interpolated")
    print()
   

    # Assign Player Teams
    print("👥 Assigning player teams...")
    team_assigner = TeamAssigner()
    player_assignment = team_assigner.get_player_teams_across_frames(video_frames,
                                                                    player_tracks,
                                                                    read_from_stub=True,
                                                                    stub_path=os.path.join(args.stub_path, 'player_assignment_stub.pkl')
                                                                    )
    print("✅ Player teams assigned")
    print()

    # Ball Acquisition
    print("🤲 Detecting ball possession...")
    ball_aquisition_detector = BallAquisitionDetector()
    ball_aquisition = ball_aquisition_detector.detect_ball_possession(player_tracks,ball_tracks)
    print("✅ Ball possession detected")
    print()

    # Detect Shots
    print("🏀 Detecting shots...")
    shot_detector = ShotDetector()
    shot_player_ids = shot_detector.detect_shots(ball_tracks, ball_aquisition, hoop_positions)
    print("✅ Shot detection complete")
    print()

    # Detect Passes
    print("🏀 Detecting passes and interceptions...")
    pass_and_interception_detector = PassAndInterceptionDetector()
    passes = pass_and_interception_detector.detect_passes(ball_aquisition,player_assignment)
    shot_attempts_bool = [x != -1 for x in shot_player_ids]
    interceptions = pass_and_interception_detector.detect_interceptions(ball_aquisition,player_assignment, shot_attempts_bool)
    print("✅ Passes and interceptions detected")
    print()

    # Detect Violations
    print("🕵️ Detecting violations (travels, double dribbles)...")
    violation_detector = ViolationDetector(fps=fps)
    travels, double_dribbles = violation_detector.detect_violations(player_tracks, ball_tracks, ball_aquisition)
    print("✅ Violation detection complete.")
    print()

    # Collect Events for Frontend
    print("📊 Collecting events for frontend...")
    event_collector = EventCollector(fps)
    event_collector.set_video_duration(video_duration)
    event_collector.collect_violations(travels, double_dribbles)
    event_collector.collect_passes(passes)
    event_collector.collect_interceptions(interceptions)
    event_collector.collect_shots(shot_player_ids)
    
    # Export events data
    events_data = event_collector.export_for_frontend()
    events_output_path = os.path.join(os.path.dirname(args.output_video), 'events_data.json')
    event_collector.export_to_json(events_output_path)
    
    print(f"✅ Events collected: {len(events_data['events'])} total events")
    print(f"📄 Events data saved to: {events_output_path}")
    print()

    print("🎨 Initializing video renderers...")
    # Draw output   
    # Initialize Drawers
    player_tracks_drawer = PlayerTracksDrawer()
    ball_tracks_drawer = BallTracksDrawer()
    frame_number_drawer = FrameNumberDrawer()
    pass_and_interceptions_drawer = PassInterceptionDrawer()
    violation_drawer = ViolationDrawer()
    hoop_drawer = HoopDrawer()
    print("✅ Renderers initialized")
    print()

    print("🎬 Rendering video output...")
    ## Draw object Tracks
    print("  📍 Drawing player tracks...")
    output_video_frames = player_tracks_drawer.draw(video_frames, 
                                                    player_tracks,
                                                    player_assignment,
                                                    ball_aquisition)
    print("  ✅ Player tracks drawn")
    
    print("  🏀 Drawing ball tracks...")
    output_video_frames = ball_tracks_drawer.draw(output_video_frames, ball_tracks)
    print("  ✅ Ball tracks drawn")

    # ## Draw KeyPoints
    # print("  🎯 Drawing court keypoints...")
    # output_video_frames = court_keypoint_drawer.draw(output_video_frames, court_keypoints_per_frame)
    # print("  ✅ Court keypoints drawn")

    # ## Draw Frame Number
    # print("  🔢 Drawing frame numbers...")
    # output_video_frames = frame_number_drawer.draw(output_video_frames)
    # print("  ✅ Frame numbers drawn")

    # Draw Passes, Interceptions and Ball Control
    print("  📊 Drawing summary stats...")
    output_video_frames = pass_and_interceptions_drawer.draw(output_video_frames,
                                                             passes,
                                                             interceptions,
                                                             player_assignment,
                                                             ball_aquisition,
                                                             shot_player_ids)
    print("  ✅ Summary stats drawn")
    
    # Draw Violations
    print("  ⚠️ Drawing violations...")
    output_video_frames = violation_drawer.draw(output_video_frames, travels, double_dribbles)
    print("  ✅ Violations drawn")
    
    # Draw Hoops
    print("  🏀 Drawing hoops...")
    output_video_frames = hoop_drawer.draw(output_video_frames, hoop_positions)
    print("  ✅ Hoops drawn")

    # Save video
    print("💾 Saving output video...")
    save_video(output_video_frames, args.output_video)
    print(f"✅ Video saved successfully to: {args.output_video}")
    print()
    print("🎉 Analysis complete!")

if __name__ == '__main__':
    main()
