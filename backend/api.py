from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import json
import subprocess
import tempfile
from werkzeug.utils import secure_filename
import uuid
import sys
import psutil
import atexit
import requests
from functools import wraps

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output_videos'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
USER_SERVICE_URL = "http://localhost:5002"

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global variables for real-time analysis
opencv_process = None

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def token_required(f):
    """
    Decorator to require a valid JWT token.
    This decorator now communicates with the user service to validate the token.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            token = request.args.get('token')

        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Verify token with the user service
            response = requests.post(f"{USER_SERVICE_URL}/verify-token", json={"token": token})
            if response.status_code != 200 or not response.json().get('valid'):
                return jsonify({'error': 'Token is invalid or expired'}), 401
            # Pass user data to the decorated function
            current_user = response.json().get('user')
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to user service: {e}")
            return jsonify({'error': 'Could not verify authentication credentials'}), 503
        
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Basketball Analysis API is running'})

@app.route('/analyze', methods=['POST'])
@token_required
def analyze_video(current_user):
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
        cmd = [sys.executable, 'main.py', input_path, '--output_video', output_video_path]
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
            'output_video_url': f'/processed_video/{session_id}/analyzed_video.mp4',
            'message': 'Analysis completed successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/processed_video/<session_id>/<filename>', methods=['GET'])
@token_required
def serve_processed_video(current_user, session_id, filename):
    video_directory = os.path.join(OUTPUT_FOLDER, session_id)
    return send_from_directory(video_directory, filename)

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

@app.route('/api/launch-desktop-app', methods=['POST'])
@token_required
def launch_desktop_app(current_user):
    global opencv_process
    script_path = os.path.join(os.path.dirname(__file__), 'opencv-test', 'person_ball_detection.py')
    if not os.path.exists(script_path):
        return jsonify({'error': 'person_ball_detection.py not found'}), 404
    if opencv_process is not None and opencv_process.poll() is None:
        return jsonify({'error': 'Analysis is already running'}), 400
    opencv_process = subprocess.Popen([sys.executable, script_path], cwd=os.path.dirname(script_path))
    return jsonify({'success': True, 'message': 'Real-time analysis launched.', 'pid': opencv_process.pid})

@app.route('/api/kill-desktop-app', methods=['POST'])
@token_required
def kill_desktop_app(current_user):
    global opencv_process
    if opencv_process is None or opencv_process.poll() is not None:
        return jsonify({'error': 'No analysis process is running or it has already ended'}), 404
    try:
        parent = psutil.Process(opencv_process.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
        parent.wait(timeout=3)
    except psutil.TimeoutExpired:
        parent.kill()
    except psutil.NoSuchProcess:
        pass 
    finally:
        opencv_process = None
    return jsonify({'success': True, 'message': 'Analysis process terminated.'})

@app.route('/api/analysis-status', methods=['GET'])
@token_required
def get_analysis_status(current_user):
    global opencv_process
    if opencv_process and opencv_process.poll() is None:
        return jsonify({'running': True, 'pid': opencv_process.pid})
    return jsonify({'running': False})

def cleanup_process():
    global opencv_process
    if opencv_process and opencv_process.poll() is None:
        opencv_process.kill()
        opencv_process = None

atexit.register(cleanup_process)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 