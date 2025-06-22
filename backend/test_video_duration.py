#!/usr/bin/env python3
"""
Test script to verify video duration calculation and event timestamp generation.
"""

import cv2
import os
import sys

def test_video_duration():
    """Test video duration calculation from a video file."""
    print("Testing video duration calculation...")
    
    # Test with a sample video if available
    test_video = "videos/test.mp4"
    if os.path.exists(test_video):
        print(f"Testing with {test_video}")
        try:
            cap = cv2.VideoCapture(test_video)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                cap.release()
                
                print(f"  FPS: {fps}")
                print(f"  Frame count: {frame_count}")
                print(f"  Duration: {duration:.2f} seconds")
                print(f"  Duration (MM:SS): {int(duration//60)}:{int(duration%60):02d}")
                return True
            else:
                print("  ❌ Could not open video file")
                return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    else:
        print(f"  ⚠️ Test video {test_video} not found")
        return False

def test_event_collector():
    """Test event collector timestamp generation."""
    print("\nTesting event collector...")
    
    try:
        from event_collector import EventCollector
        
        # Create a test event collector
        fps = 30.0
        collector = EventCollector(fps)
        collector.set_video_duration(60.0)  # 1 minute video
        
        # Test frame to timestamp conversion
        test_frames = [0, 30, 60, 90, 1500]  # 0s, 1s, 2s, 3s, 50s
        for frame in test_frames:
            timestamp = collector._frame_to_timestamp(frame)
            print(f"  Frame {frame} -> {timestamp:.2f}s")
        
        # Test event collection
        collector.collect_passes([1, -1, 2, -1, -1])  # 5 frames with 2 passes
        collector.collect_shots([-1, 5, -1, -1, -1])  # 5 frames with 1 shot
        
        events = collector.get_events()
        print(f"  Generated {len(events)} events:")
        for event in events:
            print(f"    {event['type']} at {event['timestamp']:.2f}s - {event['description']}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("Video Duration and Timestamp Test")
    print("=" * 40)
    
    success1 = test_video_duration()
    success2 = test_event_collector()
    
    print("\n" + "=" * 40)
    if success1 and success2:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return 0 if (success1 and success2) else 1

if __name__ == "__main__":
    sys.exit(main()) 