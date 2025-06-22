#!/usr/bin/env python3
"""
Test script to run analysis and check event generation.
"""

import os
import sys
import json
import subprocess

def test_analysis_events():
    """Test analysis event generation with a small video."""
    print("Testing analysis event generation...")
    
    # Test with a sample video
    test_video = "videos/test.mp4"
    if not os.path.exists(test_video):
        print(f"❌ Test video {test_video} not found")
        return False
    
    # Create output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Run analysis with limited frames for faster testing
    cmd = [
        "python3", "main.py", 
        test_video,
        "--output_video", f"{output_dir}/test_output.mp4",
        "--max_frames", "300"  # Only process first 300 frames (~10 seconds)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Analysis completed successfully")
            print("STDOUT:")
            print(result.stdout)
            
            # Check if events file was created
            events_file = f"{output_dir}/events_data.json"
            if os.path.exists(events_file):
                print(f"\n📄 Events file found: {events_file}")
                with open(events_file, 'r') as f:
                    events_data = json.load(f)
                
                print(f"Total events: {len(events_data.get('events', []))}")
                print(f"Events summary: {events_data.get('summary', {})}")
                
                if events_data.get('events'):
                    print("\nSample events:")
                    for i, event in enumerate(events_data['events'][:10]):  # Show first 10 events
                        print(f"  {i+1}. {event.get('type', 'unknown')} at {event.get('timestamp', 0):.2f}s - {event.get('description', 'No description')}")
                else:
                    print("❌ No events generated!")
                
                return True
            else:
                print(f"❌ Events file not found: {events_file}")
                return False
        else:
            print("❌ Analysis failed")
            print("STDERR:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Analysis timed out")
        return False
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        return False

def main():
    print("Analysis Events Test")
    print("=" * 40)
    
    success = test_analysis_events()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Test completed!")
    else:
        print("❌ Test failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 