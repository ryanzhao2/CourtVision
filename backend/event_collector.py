from typing import List, Dict, Any, Optional
import json

class EventCollector:
    """
    Collects and formats basketball events with timestamps for frontend consumption.
    """
    
    def __init__(self, fps: float):
        """
        Initialize the event collector.
        
        Args:
            fps (float): Frames per second of the video
        """
        self.fps = fps
        self.events = []
        self.video_duration = 0  # Will be set later
    
    def _frame_to_timestamp(self, frame_num: int) -> float:
        """Convert frame number to timestamp in seconds."""
        return frame_num / self.fps
    
    def collect_violations(self, travels: List[int], double_dribbles: List[int]) -> None:
        """
        Collect travel and double dribble violations.
        
        Args:
            travels: List where each element is the cumulative count of travels up to that frame
            double_dribbles: List where each element is the cumulative count of double dribbles up to that frame
        """
        prev_travels = 0
        prev_double_dribbles = 0
        
        for frame_num, (travel_count, double_dribble_count) in enumerate(zip(travels, double_dribbles)):
            # Check for new travels
            if travel_count > prev_travels:
                self.events.append({
                    'type': 'travel',
                    'timestamp': self._frame_to_timestamp(frame_num),
                    'frame': frame_num,
                    'description': 'Travel violation'
                })
                prev_travels = travel_count
            
            # Check for new double dribbles
            if double_dribble_count > prev_double_dribbles:
                self.events.append({
                    'type': 'double_dribble',
                    'timestamp': self._frame_to_timestamp(frame_num),
                    'frame': frame_num,
                    'description': 'Double dribble violation'
                })
                prev_double_dribbles = double_dribble_count
    
    def collect_passes(self, passes: List[int]) -> None:
        """
        Collect pass events.
        
        Args:
            passes: List where each element indicates if a pass occurred (-1: no pass, 1: Team 1 pass, 2: Team 2 pass)
        """
        for frame_num, pass_team in enumerate(passes):
            if pass_team != -1:
                self.events.append({
                    'type': 'pass',
                    'timestamp': self._frame_to_timestamp(frame_num),
                    'frame': frame_num,
                    'team': pass_team,
                    'description': f'Team {pass_team} pass'
                })
    
    def collect_interceptions(self, interceptions: List[int]) -> None:
        """
        Collect interception events.
        
        Args:
            interceptions: List where each element indicates if an interception occurred (-1: no interception, 1: Team 1 interception, 2: Team 2 interception)
        """
        for frame_num, interception_team in enumerate(interceptions):
            if interception_team != -1:
                self.events.append({
                    'type': 'interception',
                    'timestamp': self._frame_to_timestamp(frame_num),
                    'frame': frame_num,
                    'team': interception_team,
                    'description': f'Team {interception_team} interception'
                })
    
    def collect_shots(self, shot_player_ids: List[int]) -> None:
        """
        Collect shot events.
        
        Args:
            shot_player_ids: List where each element is the player ID who shot (-1: no shot)
        """
        for frame_num, player_id in enumerate(shot_player_ids):
            if player_id != -1:
                self.events.append({
                    'type': 'shot',
                    'timestamp': self._frame_to_timestamp(frame_num),
                    'frame': frame_num,
                    'player_id': player_id,
                    'description': f'Shot by player {player_id}'
                })
    
    def get_events(self) -> List[Dict[str, Any]]:
        """
        Get all collected events sorted by timestamp.
        
        Returns:
            List of event dictionaries sorted by timestamp
        """
        return sorted(self.events, key=lambda x: x['timestamp'])
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """
        Get events filtered by type.
        
        Args:
            event_type: Type of events to return ('travel', 'double_dribble', 'pass', 'interception', 'shot')
            
        Returns:
            List of events of the specified type
        """
        return [event for event in self.events if event['type'] == event_type]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics of all events.
        
        Returns:
            Dictionary with event counts and other statistics
        """
        event_counts = {}
        for event in self.events:
            event_type = event['type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Add team-specific stats
        team_stats = {'team_1': {}, 'team_2': {}}
        for event in self.events:
            if 'team' in event:
                team_key = f'team_{event["team"]}'
                event_type = event['type']
                if event_type not in team_stats[team_key]:
                    team_stats[team_key][event_type] = 0
                team_stats[team_key][event_type] += 1
        
        return {
            'total_events': len(self.events),
            'event_counts': event_counts,
            'team_stats': team_stats
        }
    
    def export_to_json(self, filepath: str) -> None:
        """
        Export all events to a JSON file.
        
        Args:
            filepath: Path to save the JSON file
        """
        data = {
            'events': self.get_events(),
            'summary': self.get_summary_stats(),
            'metadata': {
                'fps': self.fps,
                'total_events': len(self.events),
                'video_duration': self.video_duration
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_for_frontend(self) -> Dict[str, Any]:
        """
        Export events in a format optimized for frontend consumption.
        
        Returns:
            Dictionary with events and metadata for frontend
        """
        return {
            'events': self.get_events(),
            'summary': self.get_summary_stats(),
            'eventsByType': {
                'travels': self.get_events_by_type('travel'),
                'double_dribbles': self.get_events_by_type('double_dribble'),
                'passes': self.get_events_by_type('pass'),
                'interceptions': self.get_events_by_type('interception'),
                'shots': self.get_events_by_type('shot')
            },
            'metadata': {
                'fps': self.fps,
                'total_events': len(self.events),
                'video_duration': self.video_duration
            }
        }
    
    def set_video_duration(self, duration: float) -> None:
        """Set the video duration in seconds."""
        self.video_duration = duration 