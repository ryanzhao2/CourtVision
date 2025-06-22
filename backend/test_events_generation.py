#!/usr/bin/env python3
"""
Test script to manually generate events and verify timestamp generation.
"""

import os
import sys
import json
from event_collector import EventCollector

def test_manual_events():
    """Test manual event generation with timestamps."""
    print("Testing Manual Event Generation")
    print("=" * 40)
    
    # Create a test event collector
    fps = 30.0
    video_duration = 60.0  # 1 minute video
    collector = EventCollector(fps)
    collector.set_video_duration(video_duration)
    
    # Manually add some test events
    print("Adding test events...")
    
    # Add some passes (every 5 seconds)
    for i in range(0, 60, 5):
        frame = i * fps
        collector.events.append({
            'type': 'pass',
            'timestamp': i,
            'frame': int(frame),
            'team': 1 if i % 10 == 0 else 2,
            'description': f'Team {1 if i % 10 == 0 else 2} pass at {i}s'
        })
    
    # Add some shots (every 10 seconds)
    for i in range(0, 60, 10):
        frame = i * fps
        collector.events.append({
            'type': 'shot',
            'timestamp': i,
            'frame': int(frame),
            'player_id': (i // 10) % 4 + 1,
            'description': f'Shot by player {(i // 10) % 4 + 1} at {i}s'
        })
    
    # Add some violations (every 15 seconds)
    for i in range(0, 60, 15):
        frame = i * fps
        collector.events.append({
            'type': 'travel',
            'timestamp': i,
            'frame': int(frame),
            'description': f'Travel violation at {i}s'
        })
    
    # Add some interceptions (every 20 seconds)
    for i in range(0, 60, 20):
        frame = i * fps
        collector.events.append({
            'type': 'interception',
            'timestamp': i,
            'frame': int(frame),
            'team': 1 if i % 40 == 0 else 2,
            'description': f'Team {1 if i % 40 == 0 else 2} interception at {i}s'
        })
    
    # Get and display events
    events = collector.get_events()
    print(f"\nGenerated {len(events)} events:")
    for i, event in enumerate(events):
        print(f"  {i+1}. {event['type']} at {event['timestamp']:.2f}s - {event['description']}")
    
    # Test export functions
    print(f"\nTesting export functions...")
    events_data = collector.export_for_frontend()
    
    print(f"Events data structure:")
    print(f"  - Total events: {len(events_data['events'])}")
    print(f"  - Summary: {events_data['summary']}")
    print(f"  - Metadata: {events_data['metadata']}")
    
    # Test JSON export
    test_output_path = "test_manual_events.json"
    collector.export_to_json(test_output_path)
    print(f"  - Exported to: {test_output_path}")
    
    # Verify the exported file
    with open(test_output_path, 'r') as f:
        exported_data = json.load(f)
    
    print(f"  - Exported file has {len(exported_data['events'])} events")
    print(f"  - Video duration: {exported_data['metadata']['video_duration']}s")
    
    return True

def main():
    success = test_manual_events()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Manual event generation test completed!")
    else:
        print("❌ Manual event generation test failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 