from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import subprocess
import tempfile
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output_videos'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Basketball Analysis API is running'})

@app.route('/analyze', methods=['POST'])
def analyze_video():
    """
    Analyze a basketball video and return results.
    
    Expected form data:
    - video: Video file
    - max_frames: (optional) Maximum frames to process for faster testing
    """
    try:
        # Check if video file is present
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
        
        if not allowed_file(video_file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv'}), 400
        
        # Get optional parameters
        max_frames = request.form.get('max_frames', None)
        if max_frames:
            try:
                max_frames = int(max_frames)
            except ValueError:
                return jsonify({'error': 'max_frames must be an integer'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session_folder = os.path.join(OUTPUT_FOLDER, session_id)
        os.makedirs(session_folder, exist_ok=True)
        
        # Save uploaded video
        filename = video_file.filename
        if filename is None:
            return jsonify({'error': 'Invalid filename'}), 400
        
        filename = secure_filename(filename)
        input_path = os.path.join(session_folder, filename)
        video_file.save(input_path)
        
        # Generate output paths
        output_video_path = os.path.join(session_folder, 'analyzed_video.mp4')
        events_data_path = os.path.join(session_folder, 'events_data.json')
        
        # Run analysis
        cmd = ['python', 'main.py', input_path, '--output_video', output_video_path]
        if max_frames:
            cmd.extend(['--max_frames', str(max_frames)])
        
        print(f"Running analysis command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode != 0:
            return jsonify({
                'error': 'Analysis failed',
                'stderr': result.stderr,
                'stdout': result.stdout
            }), 500
        
        # Check if events data was generated
        if not os.path.exists(events_data_path):
            return jsonify({
                'error': 'Analysis completed but events data not found',
                'stdout': result.stdout
            }), 500
        
        # Load events data
        with open(events_data_path, 'r') as f:
            events_data = json.load(f)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'events': events_data,
            'output_video_url': f'/video/{session_id}',
            'message': 'Analysis completed successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/video/<session_id>', methods=['GET'])
def get_video(session_id):
    """Serve the analyzed video file."""
    try:
        video_path = os.path.join(OUTPUT_FOLDER, session_id, 'analyzed_video.mp4')
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video not found'}), 404
        
        return send_file(video_path, mimetype='video/mp4')
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/events/<session_id>', methods=['GET'])
def get_events(session_id):
    """Get events data for a specific session."""
    try:
        events_path = os.path.join(OUTPUT_FOLDER, session_id, 'events_data.json')
        if not os.path.exists(events_path):
            return jsonify({'error': 'Events data not found'}), 404
        
        with open(events_path, 'r') as f:
            events_data = json.load(f)
        
        return jsonify(events_data)
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/sessions', methods=['GET'])
def list_sessions():
    """List all available analysis sessions."""
    try:
        sessions = []
        if os.path.exists(OUTPUT_FOLDER):
            for session_id in os.listdir(OUTPUT_FOLDER):
                session_path = os.path.join(OUTPUT_FOLDER, session_id)
                if os.path.isdir(session_path):
                    # Check if session has required files
                    video_exists = os.path.exists(os.path.join(session_path, 'analyzed_video.mp4'))
                    events_exists = os.path.exists(os.path.join(session_path, 'events_data.json'))
                    
                    if video_exists and events_exists:
                        sessions.append({
                            'session_id': session_id,
                            'video_url': f'/video/{session_id}',
                            'events_url': f'/events/{session_id}'
                        })
        
        return jsonify({'sessions': sessions})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id):
    """Delete a specific analysis session."""
    try:
        session_path = os.path.join(OUTPUT_FOLDER, session_id)
        if not os.path.exists(session_path):
            return jsonify({'error': 'Session not found'}), 404
        
        # Remove session directory and all contents
        import shutil
        shutil.rmtree(session_path)
        
        return jsonify({'message': f'Session {session_id} deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 