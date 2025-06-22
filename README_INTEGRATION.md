# Frontend-Backend Integration

This document explains how to run and test the integrated basketball analysis system.

## Setup

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python api.py
```
The backend will run on `http://localhost:5000`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm start
```
The frontend will run on `http://localhost:3000`

## How It Works

### 1. Upload & Analysis Flow
1. User uploads a video on the frontend (`/upload`)
2. Frontend sends video to backend `/analyze` endpoint
3. Backend processes the video and returns:
   - `session_id` (used as analysis ID)
   - `events` data with timestamps
   - `output_video_url`
4. Frontend navigates directly to `/results/{session_id}`

### 2. Results Page Features
- **Video Player**: Displays the analyzed video from `/video/{session_id}`
- **Event Timestamps**: Shows all events (travels, double dribbles, passes, interceptions, shots)
- **Click to Seek**: Click any timestamp to jump to that moment in the video
- **Event Details**: Shows team info for passes/interceptions, player info for shots

### 3. API Endpoints Used
- `POST /analyze` - Upload and analyze video
- `GET /video/{session_id}` - Get analyzed video
- `GET /events/{session_id}` - Get event timestamps
- `GET /health` - Health check

## Testing

### 1. Test with Sample Video
1. Start both backend and frontend
2. Go to `http://localhost:3000/upload`
3. Upload a basketball video
4. Wait for analysis to complete
5. View results with video player and event timestamps

### 2. Test Event Seeking
1. In the results page, click on any event timestamp
2. Video should jump to that moment and start playing

### 3. Test API Directly
```bash
# Health check
curl http://localhost:5000/health

# List sessions
curl http://localhost:5000/sessions

# Get events for a session
curl http://localhost:5000/events/{session_id}
```

## Event Types

The system detects and displays:
- **Travel**: Player moves while holding the ball
- **Double Dribble**: Player starts a new dribble after stopping
- **Pass**: Successful pass between teammates
- **Interception**: Opposing team steals the ball
- **Shot**: Player attempts a shot at the basket

## Troubleshooting

### Frontend Can't Connect to Backend
- Ensure backend is running on port 5000
- Check that proxy is configured in `package.json`
- Verify CORS is enabled in backend

### Video Not Playing
- Check that video file exists in backend output directory
- Verify video URL is correct in browser network tab
- Ensure video format is supported (MP4, AVI, MOV, MKV)

### Events Not Loading
- Check backend logs for analysis errors
- Verify events_data.json was generated
- Check browser console for API errors

## Development Notes

- The frontend uses React with Tailwind CSS
- The backend uses Flask with CORS enabled
- Video files are stored in `backend/output_videos/{session_id}/`
- Events data is stored as JSON in the same directory
- The proxy configuration forwards all API calls to the backend 