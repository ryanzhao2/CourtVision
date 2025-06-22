# Basketball Analysis API

This API provides endpoints for analyzing basketball videos and extracting event timestamps for frontend consumption.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the API server:
```bash
python api.py
```

The server will run on `http://localhost:5000`

## API Endpoints

### 1. Health Check
```
GET /health
```
Returns the API status.

### 2. Analyze Video
```
POST /analyze
```
Upload and analyze a basketball video.

**Form Data:**
- `video`: Video file (mp4, avi, mov, mkv)
- `max_frames` (optional): Maximum frames to process for faster testing

**Response:**
```json
{
  "success": true,
  "session_id": "uuid-string",
  "events": {
    "events": [...],
    "summary": {...},
    "eventsByType": {...},
    "metadata": {...}
  },
  "output_video_url": "/video/uuid-string",
  "message": "Analysis completed successfully"
}
```

### 3. Get Video
```
GET /video/{session_id}
```
Download the analyzed video file.

### 4. Get Events
```
GET /events/{session_id}
```
Get events data for a specific session.

### 5. List Sessions
```
GET /sessions
```
List all available analysis sessions.

### 6. Cleanup Session
```
DELETE /cleanup/{session_id}
```
Delete a specific analysis session.

## Events Data Format

The events data contains the following structure:

### Main Events Array
Each event has this format:
```json
{
  "type": "travel|double_dribble|pass|interception|shot",
  "timestamp": 12.5,
  "frame": 300,
  "description": "Travel violation",
  "team": 1,           // Only for pass/interception events
  "player_id": 5       // Only for shot events
}
```

### Events by Type
```json
{
  "eventsByType": {
    "travels": [...],
    "double_dribbles": [...],
    "passes": [...],
    "interceptions": [...],
    "shots": [...]
  }
}
```

### Summary Statistics
```json
{
  "summary": {
    "total_events": 45,
    "event_counts": {
      "travel": 3,
      "double_dribble": 2,
      "pass": 25,
      "interception": 8,
      "shot": 7
    },
    "team_stats": {
      "team_1": {
        "pass": 12,
        "interception": 3,
        "shot": 4
      },
      "team_2": {
        "pass": 13,
        "interception": 5,
        "shot": 3
      }
    },
    "video_duration": 120.5
  }
}
```

## Frontend Integration Example

### JavaScript/React Example
```javascript
// Upload and analyze video
const formData = new FormData();
formData.append('video', videoFile);
formData.append('max_frames', '300'); // Optional: limit frames for faster testing

const response = await fetch('http://localhost:5000/analyze', {
  method: 'POST',
  body: formData
});

const result = await response.json();

if (result.success) {
  const { events, session_id, output_video_url } = result;
  
  // Access events data
  console.log('All events:', events.events);
  console.log('Travels:', events.eventsByType.travels);
  console.log('Passes:', events.eventsByType.passes);
  console.log('Summary:', events.summary);
  
  // Video URL
  const videoUrl = `http://localhost:5000${output_video_url}`;
}
```

### Python Example
```python
import requests

# Upload video
with open('basketball_video.mp4', 'rb') as f:
    files = {'video': f}
    data = {'max_frames': '300'}  # Optional
    
    response = requests.post('http://localhost:5000/analyze', 
                           files=files, data=data)
    
    result = response.json()
    
    if result['success']:
        events = result['events']
        print(f"Total events: {events['summary']['total_events']}")
        print(f"Travels: {len(events['eventsByType']['travels'])}")
        print(f"Passes: {len(events['eventsByType']['passes'])}")
```

## Event Types

1. **Travel**: Player moves while holding the ball
2. **Double Dribble**: Player starts a new dribble after stopping
3. **Pass**: Successful pass between teammates
4. **Interception**: Opposing team steals the ball
5. **Shot**: Player attempts a shot at the basket

## Timestamps

All timestamps are in seconds from the start of the video. The `frame` field provides the exact frame number for precise video seeking.

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid file, missing parameters)
- `404`: Resource not found
- `500`: Server error

Error responses include a descriptive message:
```json
{
  "error": "Description of the error"
}
``` 