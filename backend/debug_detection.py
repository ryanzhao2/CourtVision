#!/usr/bin/env python3
"""
Debug script to check ball and player detection.
"""

import os
import sys
import pickle

def debug_detection():
    """Debug ball and player detection issues."""
    print("Debugging Detection Issues")
    print("=" * 40)
    
    # Check if stub files exist
    stub_dir = "stubs"
    if not os.path.exists(stub_dir):
        print(f"❌ Stub directory {stub_dir} not found")
        return False
    
    # Check ball track stubs
    ball_stub_path = os.path.join(stub_dir, 'ball_track_stubs.pkl')
    if os.path.exists(ball_stub_path):
        print(f"📄 Ball track stub found: {ball_stub_path}")
        try:
            with open(ball_stub_path, 'rb') as f:
                ball_tracks = pickle.load(f)
            print(f"  Ball tracks length: {len(ball_tracks)}")
            
            # Check first few frames
            for i in range(min(5, len(ball_tracks))):
                frame_data = ball_tracks[i]
                print(f"  Frame {i}: {len(frame_data)} ball detections")
                if frame_data:
                    for ball_id, ball_info in frame_data.items():
                        bbox = ball_info.get('bbox', [])
                        print(f"    Ball {ball_id}: bbox={bbox}")
        except Exception as e:
            print(f"  ❌ Error loading ball tracks: {e}")
    else:
        print(f"❌ Ball track stub not found: {ball_stub_path}")
    
    # Check player track stubs
    player_stub_path = os.path.join(stub_dir, 'player_track_stubs.pkl')
    if os.path.exists(player_stub_path):
        print(f"\n📄 Player track stub found: {player_stub_path}")
        try:
            with open(player_stub_path, 'rb') as f:
                player_tracks = pickle.load(f)
            print(f"  Player tracks length: {len(player_tracks)}")
            
            # Check first few frames
            for i in range(min(5, len(player_tracks))):
                frame_data = player_tracks[i]
                print(f"  Frame {i}: {len(frame_data)} player detections")
                if frame_data:
                    for player_id, player_info in frame_data.items():
                        bbox = player_info.get('bbox', [])
                        print(f"    Player {player_id}: bbox={bbox}")
        except Exception as e:
            print(f"  ❌ Error loading player tracks: {e}")
    else:
        print(f"❌ Player track stub not found: {player_stub_path}")
    
    # Check team assignment stubs
    team_stub_path = os.path.join(stub_dir, 'player_assignment_stub.pkl')
    if os.path.exists(team_stub_path):
        print(f"\n📄 Team assignment stub found: {team_stub_path}")
        try:
            with open(team_stub_path, 'rb') as f:
                team_assignments = pickle.load(f)
            print(f"  Team assignments length: {len(team_assignments)}")
            
            # Check first few frames
            for i in range(min(5, len(team_assignments))):
                frame_data = team_assignments[i]
                print(f"  Frame {i}: {len(frame_data)} team assignments")
                if frame_data:
                    for player_id, team in frame_data.items():
                        print(f"    Player {player_id}: Team {team}")
        except Exception as e:
            print(f"  ❌ Error loading team assignments: {e}")
    else:
        print(f"❌ Team assignment stub not found: {team_stub_path}")
    
    return True

def main():
    success = debug_detection()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Debug completed!")
    else:
        print("❌ Debug failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 