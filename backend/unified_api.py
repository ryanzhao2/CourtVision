from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from mongodb import create_user, get_user, client
import jwt
import datetime
import os
import json
import subprocess
import tempfile
import uuid
from functools import wraps
import sys
import psutil
import atexit
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)

# JWT token expiration time (24 hours)
JWT_EXPIRATION_HOURS = 24

# Configuration for video analysis
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output_videos'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global variables for real-time analysis
opencv_process = None

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
        
        # If not in header, check for token in query parameters (for video streams)
        if not token:
            token = request.args.get('token')

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

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===== HEALTH CHECK ENDPOINTS =====

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"message": "Backend is running!"}), 200

@app.route('/health', methods=['GET'])
def api_health_check():
    """Health check endpoint for basketball analysis API."""
    return jsonify({'status': 'healthy', 'message': 'Basketball Analysis API is running'})

@app.route('/status', methods=['GET'])
def status_check():
    """Provides a detailed status check of the server and its services."""
    db_status = 'disconnected'
    db_message = 'Could not connect to MongoDB.'
    try:
        # The ping command is cheap and does not require auth.
        client.admin.command('ping')
        db_status = 'connected'
        db_message = 'Successfully connected to MongoDB.'
    except Exception as e:
        db_message = f"MongoDB connection failed: {str(e)}"

    status = {
        'server_status': 'ok',
        'database': {
            'status': db_status,
            'message': db_message
        }
    }
    
    return jsonify(status), 200

# ===== USER AUTHENTICATION ENDPOINTS =====

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

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    try:
        user_id = create_user(first_name, last_name, email, hashed_password)
        if user_id:
            print("User created successfully:", user_id)
            return jsonify({"message": "User created successfully", "user_id": str(user_id)}), 201
        else:
            print("Failed to create user")
            return jsonify({"error": "Failed to create user"}), 500
    except Exception as e:
        print(f"Error creating user in database: {e}")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

@app.route("/login", methods=["POST"])
def login():
    print("Login endpoint called")
    
    data = request.get_json()
    print("Login data:", data)

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        user = get_user(email)
    except Exception as e:
        # This will catch database connection errors
        print(f"Error connecting to database during login for {email}: {e}")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    # Safely check user and password
    try:
        if not user or not check_password_hash(user.get("password", ""), password):
            return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        # This catches errors from check_password_hash if the hash is malformed
        print(f"Password check failed for {email}: {e}")
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

# ===== BASKETBALL ANALYSIS ENDPOINTS =====

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

@app.route('/sessions', methods=['GET'])
@token_required
def list_sessions(current_user):
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
                            'video_url': f'/processed_video/{session_id}/analyzed_video.mp4',
                            'events_url': f'/events/{session_id}'
                        })
        
        return jsonify({'sessions': sessions})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/cleanup/<session_id>', methods=['DELETE'])
@token_required
def cleanup_session(current_user, session_id):
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

@app.route("/api/video/<filename>", methods=["GET"])
@token_required
def serve_video(current_user, filename):
    """Serve video files from the backend directory"""
    try:
        # Get the directory where this script is located
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        return send_from_directory(backend_dir, filename)
    except FileNotFoundError:
        return jsonify({"error": "Video file not found"}), 404

@app.route('/api/launch-desktop-app', methods=['POST'])
@token_required
def launch_desktop_app(current_user):
    """Launch the person_ball_detection.py desktop app with backend webcam"""
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
        pass # Already gone
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
    print("🚀 Starting Unified Backend Server...")
    print("📡 Server will be available at http://localhost:5001")
    print("🔐 User Authentication + 🏀 Basketball Analysis API")
    print("Press Ctrl+C to stop the server")
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        print("\n✅ Server shutdown complete")
    except Exception as e:
        print(f"❌ Error starting server: {e}") 