from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from mongodb import create_user, get_user
import jwt
import datetime
import os
from functools import wraps
import subprocess
import sys
import signal
import psutil
import atexit
import time
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)

# JWT token expiration time (24 hours)
JWT_EXPIRATION_HOURS = 24

# Global variables for analysis data
opencv_process = None
analysis_sessions = {}  # Store analysis session data
current_session_id = None

def generate_token(user_id, email):
    """Generate JWT token for user"""
    payload = {
        'user_id': str(user_id),
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def token_required(f):
    """Decorator to require JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Decode token
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = get_user(payload['email'])
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"message": "Backend is running!"}), 200

@app.route("/signup", methods=["POST"])
def signup():
    print("Signup endpoint called")
    print("Request headers:", dict(request.headers))
    
    data = request.get_json()
    print("Request data:", data)

    first_name = data.get("firstName")
    last_name = data.get("lastName")
    email = data.get("email")
    password = data.get("password")

    if not all([first_name, last_name, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    if get_user(email):
        return jsonify({"error": "User already exists"}), 409

    hashed_password = generate_password_hash(password)

    user_id = create_user(first_name, last_name, email, hashed_password)
    if user_id:
        print("User created successfully:", user_id)
        return jsonify({"message": "User created successfully", "user_id": str(user_id)}), 201
    else:
        print("Failed to create user")
        return jsonify({"error": "Failed to create user"}), 500

@app.route("/login", methods=["POST"])
def login():
    print("Login endpoint called")
    
    data = request.get_json()
    print("Login data:", data)

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = get_user(email)
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Generate JWT token
    token = generate_token(user["_id"], user["email"])
    
    print("Login successful for user:", user["email"])
    
    return jsonify({
        "message": f"Welcome, {user['first_name']}!",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "firstName": user["first_name"],
            "lastName": user["last_name"]
        }
    }), 200

@app.route("/logout", methods=["POST"])
@token_required
def logout(current_user):
    """Logout endpoint - client should discard the token"""
    print("Logout endpoint called for user:", current_user["email"])
    
    # In a stateless JWT system, the client is responsible for discarding the token
    # We could implement a blacklist here if needed for additional security
    return jsonify({"message": "Logged out successfully"}), 200

@app.route("/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    """Get user profile - protected route"""
    return jsonify({
        "user": {
            "id": str(current_user["_id"]),
            "email": current_user["email"],
            "firstName": current_user["first_name"],
            "lastName": current_user["last_name"]
        }
    }), 200

@app.route("/verify-token", methods=["POST"])
def verify_token():
    """Verify if a token is valid"""
    data = request.get_json()
    token = data.get("token")
    
    if not token:
        return jsonify({"error": "Token is required"}), 400
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = get_user(payload['email'])
        
        if not user:
            return jsonify({"error": "User not found"}), 401
        
        return jsonify({
            "valid": True,
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "firstName": user["first_name"],
                "lastName": user["last_name"]
            }
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "Invalid token"}), 401

@app.route("/api/video/<filename>", methods=["GET"])
def serve_video(filename):
    """Serve video files from the backend directory"""
    try:
        # Get the directory where this script is located
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        return send_from_directory(backend_dir, filename)
    except FileNotFoundError:
        return jsonify({"error": "Video file not found"}), 404

@app.route('/api/launch-desktop-app', methods=['POST'])
def launch_desktop_app():
    """Launch the person_ball_detection.py desktop app with backend webcam"""
    global opencv_process
    
    try:
        # Path to the person_ball_detection.py script
        script_path = os.path.join(os.path.dirname(__file__), 'opencv-test', 'person_ball_detection.py')
        
        # Check if the script exists
        if not os.path.exists(script_path):
            return jsonify({'error': 'person_ball_detection.py not found'}), 404
        
        # Check if process is already running
        if opencv_process is not None and opencv_process.poll() is None:
            return jsonify({'error': 'Analysis is already running'}), 400
        
        # Create a new webcam session
        session_id = create_session('webcam')
        
        # Launch the Python script with backend webcam
        # Use subprocess.Popen to run it in the background
        opencv_process = subprocess.Popen([sys.executable, script_path], 
                                        cwd=os.path.dirname(script_path),
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        
        return jsonify({
            'success': True,
            'message': 'Basketball analysis launched successfully with backend webcam',
            'pid': opencv_process.pid,
            'session_id': session_id,
            'note': 'The analysis window will open on your desktop. Press q to quit.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kill-desktop-app', methods=['POST'])
def kill_desktop_app():
    """Kill the running person_ball_detection.py process"""
    global opencv_process, current_session_id
    
    try:
        if opencv_process is None:
            return jsonify({'error': 'No analysis process is running'}), 404
        
        # Check if process is still running
        if opencv_process.poll() is not None:
            opencv_process = None
            # Finalize the session
            if current_session_id and current_session_id in analysis_sessions:
                analysis_sessions[current_session_id]['status'] = 'completed'
                analysis_sessions[current_session_id]['duration'] = time.time() - float(current_session_id.split('_')[1])
            return jsonify({'error': 'Analysis process has already ended'}), 404
        
        # Kill the process and its children
        try:
            # Get the process and all its children
            parent = psutil.Process(opencv_process.pid)
            children = parent.children(recursive=True)
            
            # Kill children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Kill the parent process
            parent.terminate()
            
            # Wait a bit for graceful termination
            try:
                parent.wait(timeout=3)
            except psutil.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                parent.kill()
            
            # Finalize the session
            if current_session_id and current_session_id in analysis_sessions:
                analysis_sessions[current_session_id]['status'] = 'completed'
                analysis_sessions[current_session_id]['duration'] = time.time() - float(current_session_id.split('_')[1])
            
            opencv_process = None
            
            return jsonify({
                'success': True,
                'message': 'Analysis process terminated successfully',
                'session_id': current_session_id
            })
            
        except psutil.NoSuchProcess:
            opencv_process = None
            # Finalize the session
            if current_session_id and current_session_id in analysis_sessions:
                analysis_sessions[current_session_id]['status'] = 'completed'
            return jsonify({
                'success': True,
                'message': 'Analysis process was already terminated',
                'session_id': current_session_id
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis-status', methods=['GET'])
def get_analysis_status():
    """Get the current status of the analysis process"""
    global opencv_process
    
    try:
        if opencv_process is None:
            return jsonify({
                'running': False,
                'message': 'No analysis process is running'
            })
        
        # Check if process is still running
        if opencv_process.poll() is None:
            return jsonify({
                'running': True,
                'pid': opencv_process.pid,
                'message': 'Analysis is currently running'
            })
        else:
            opencv_process = None
            return jsonify({
                'running': False,
                'message': 'Analysis process has ended'
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def cleanup_process():
    """Clean up the OpenCV process if it's still running"""
    global opencv_process
    if opencv_process is not None:
        try:
            if opencv_process.poll() is None:  # Process is still running
                opencv_process.terminate()
                try:
                    opencv_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    opencv_process.kill()
        except Exception as e:
            print(f"Error cleaning up process: {e}")
        finally:
            opencv_process = None

# Register cleanup function to run on app shutdown
atexit.register(cleanup_process)

@app.route('/api/analysis-data/<session_id>', methods=['GET'])
def get_analysis_data(session_id):
    """Get analysis data for a specific session"""
    try:
        if session_id not in analysis_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_data = analysis_sessions[session_id]
        return jsonify(session_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis-completion-stats/<session_id>', methods=['GET'])
def get_completion_stats(session_id):
    """Get completion statistics for analysis session"""
    try:
        if session_id not in analysis_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_data = analysis_sessions[session_id]
        
        # Calculate stats based on session type
        if session_data.get('type') == 'webcam':
            # For webcam sessions, use real-time data
            events = session_data.get('events', [])
            duration = session_data.get('duration', 0)
            
            stats = {
                'events_found': len(events),
                'duration': format_duration(duration),
                'violations': len([e for e in events if e.get('severity') == 'error']),
                'warnings': len([e for e in events if e.get('severity') == 'warning']),
                'good_plays': len([e for e in events if e.get('severity') == 'info']),
                'session_type': 'webcam'
            }
        else:
            # For uploaded video sessions, use processed data
            events = session_data.get('events', [])
            duration = session_data.get('video_duration', 0)
            
            stats = {
                'events_found': len(events),
                'duration': format_duration(duration),
                'violations': len([e for e in events if e.get('severity') == 'error']),
                'warnings': len([e for e in events if e.get('severity') == 'warning']),
                'good_plays': len([e for e in events if e.get('severity') == 'info']),
                'session_type': 'upload'
            }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis-results/<session_id>', methods=['GET'])
def get_analysis_results(session_id):
    """Get detailed analysis results for a session"""
    try:
        if session_id not in analysis_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_data = analysis_sessions[session_id]
        
        # Format events for frontend
        events = []
        for i, event in enumerate(session_data.get('events', [])):
            events.append({
                'id': str(i + 1),
                'timestamp': event.get('timestamp', 0),
                'type': event.get('type', 'Event'),
                'title': event.get('title', event.get('description', 'Unknown Event')),
                'description': event.get('description', ''),
                'severity': event.get('severity', 'info')
            })
        
        results = {
            'events': events,
            'video_source': session_data.get('video_source', 'test.mp4'),
            'session_type': session_data.get('type', 'upload'),
            'analysis_date': session_data.get('created_at', ''),
            'total_events': len(events),
            'duration': session_data.get('video_duration', 0)
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/current-session', methods=['GET'])
def get_current_session():
    """Get the current active session ID"""
    try:
        return jsonify({
            'session_id': current_session_id,
            'has_session': current_session_id is not None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def format_duration(seconds):
    """Format duration in seconds to MM:SS format"""
    if not seconds:
        return "00:00"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def create_session(session_type, video_source=None):
    """Create a new analysis session"""
    global current_session_id
    
    session_id = f"session_{int(time.time())}"
    current_session_id = session_id
    
    analysis_sessions[session_id] = {
        'id': session_id,
        'type': session_type,
        'video_source': video_source,
        'events': [],
        'duration': 0,
        'video_duration': 0,
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'active'
    }
    
    return session_id

def update_session_data(session_id, data):
    """Update session data with new analysis results"""
    if session_id in analysis_sessions:
        analysis_sessions[session_id].update(data)

@app.route('/api/simulate-video-analysis', methods=['POST'])
def simulate_video_analysis():
    """Simulate video upload analysis with sample data"""
    try:
        data = request.get_json()
        video_filename = data.get('filename', 'test.mp4')
        
        # Create a new upload session
        session_id = create_session('upload', video_filename)
        
        # Simulate analysis delay
        time.sleep(2)
        
        # Create sample analysis events
        sample_events = [
            {
                'timestamp': 45,
                'type': 'Foul',
                'title': 'Personal Foul',
                'description': 'Pushing foul committed by Player #23',
                'severity': 'warning'
            },
            {
                'timestamp': 128,
                'type': 'Violation',
                'title': 'Double Dribble',
                'description': 'Player #15 committed a double dribble violation',
                'severity': 'error'
            },
            {
                'timestamp': 245,
                'type': 'Good Play',
                'title': 'Steal',
                'description': 'Clean steal executed by Player #8',
                'severity': 'info'
            },
            {
                'timestamp': 367,
                'type': 'Foul',
                'title': 'Traveling',
                'description': 'Traveling violation by Player #12',
                'severity': 'warning'
            },
            {
                'timestamp': 456,
                'type': 'Good Play',
                'title': 'Three-Point Shot',
                'description': 'Successful three-point shot by Player #7',
                'severity': 'info'
            },
            {
                'timestamp': 589,
                'type': 'Violation',
                'title': 'Out of Bounds',
                'description': 'Ball went out of bounds, turnover',
                'severity': 'error'
            },
            {
                'timestamp': 723,
                'type': 'Good Play',
                'title': 'Assist',
                'description': 'Great assist leading to a score',
                'severity': 'info'
            },
            {
                'timestamp': 834,
                'type': 'Foul',
                'title': 'Blocking Foul',
                'description': 'Illegal blocking foul by Player #19',
                'severity': 'warning'
            }
        ]
        
        # Update session with analysis results
        update_session_data(session_id, {
            'events': sample_events,
            'video_duration': 930,  # 15:30 in seconds
            'status': 'completed'
        })
        
        return jsonify({
            'success': True,
            'message': 'Video analysis completed successfully',
            'session_id': session_id,
            'events_found': len(sample_events),
            'duration': '15:30'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
@token_required
def analyze_video(current_user):
    """
    Analyze a basketball video and return results.
    
    Expected form data:
    - video: Video file
    - max_frames: (optional) Maximum frames to process for faster testing
    """
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
        
        if not allowed_file(video_file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv'}), 400
        
        max_frames = request.form.get('max_frames', None)
        if max_frames:
            try:
                max_frames = int(max_frames)
            except ValueError:
                return jsonify({'error': 'max_frames must be an integer'}), 400
        
        session_id = str(uuid.uuid4())
        session_folder = os.path.join('output_videos', session_id)
        os.makedirs(session_folder, exist_ok=True)
        
        filename = secure_filename(video_file.filename)
        input_path = os.path.join(session_folder, filename)
        video_file.save(input_path)
        
        output_video_path = os.path.join(session_folder, 'analyzed_video.mp4')
        events_data_path = os.path.join(session_folder, 'events_data.json')
        
        cmd = [sys.executable, 'main.py', input_path, '--output_video', output_video_path]
        if max_frames:
            cmd.extend(['--max_frames', str(max_frames)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode != 0:
            return jsonify({
                'error': 'Analysis failed',
                'stderr': result.stderr,
                'stdout': result.stdout
            }), 500
        
        if not os.path.exists(events_data_path):
            return jsonify({
                'error': 'Analysis completed but events data not found',
                'stdout': result.stdout
            }), 500
        
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
    video_directory = os.path.join('output_videos', session_id)
    return send_from_directory(video_directory, filename)

@app.route('/sessions', methods=['GET'])
@token_required
def list_sessions(current_user):
    try:
        sessions = []
        if os.path.exists('output_videos'):
            for session_id in os.listdir('output_videos'):
                session_path = os.path.join('output_videos', session_id)
                if os.path.isdir(session_path):
                    video_exists = os.path.exists(os.path.join(session_path, 'analyzed_video.mp4'))
                    events_exists = os.path.exists(os.path.join(session_path, 'events_data.json'))
                    
                    if video_exists and events_exists:
                        sessions.append({
                            'session_id': session_id,
                            'video_url': f'/processed_video/{session_id}/analyzed_video.mp4',
                            'events_url': f'/events/{session_id}'
                        })
        
        return jsonify({'sessions': sessions})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/cleanup/<session_id>', methods=['DELETE'])
@token_required
def cleanup_session(current_user, session_id):
    try:
        session_path = os.path.join('output_videos', session_id)
        if not os.path.exists(session_path):
            return jsonify({'error': 'Session not found'}), 404
        
        import shutil
        shutil.rmtree(session_path)
        
        return jsonify({'message': f'Session {session_id} deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/analysis-status', methods=['GET'])
@token_required
def get_analysis_status(current_user):
    global opencv_process
    if opencv_process and opencv_process.poll() is None:
        return jsonify({'running': True, 'pid': opencv_process.pid})
    return jsonify({'running': False})

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.run(debug=True)