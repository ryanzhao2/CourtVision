from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from mongodb import create_user, get_user, client
import jwt
import datetime
import os
from functools import wraps
import subprocess
import sys
import signal
import psutil
import atexit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)

# JWT token expiration time (24 hours)
JWT_EXPIRATION_HOURS = 24

# Global variable to track the OpenCV analysis process
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
    data = request.get_json()
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
        return jsonify({"message": "User created successfully", "user_id": str(user_id)}), 201
    else:
        return jsonify({"error": "Failed to create user"}), 500
    except Exception as e:
        print(f"Error creating user in database: {e}")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
    user = get_user(email)
    except Exception as e:
        print(f"Error connecting to database during login for {email}: {e}")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    try:
        if not user or not check_password_hash(user.get("password", ""), password):
            return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        print(f"Password check failed for {email}: {e}")
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token(user["_id"], user["email"])
    
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
    data = request.get_json()
    token = data.get("token")
    if not token:
        return jsonify({"error": "Token is required"}), 400
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = get_user(payload['email'])
        if not user:
            return jsonify({"error": "User not found"}), 401
        return jsonify({"valid": True, "user": {
            "id": str(user["_id"]), "email": user["email"],
            "firstName": user["first_name"], "lastName": user["last_name"]
        }}), 200
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
            'note': 'The analysis window will open on your desktop. Press q to quit.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kill-desktop-app', methods=['POST'])
def kill_desktop_app():
    """Kill the running person_ball_detection.py process"""
    global opencv_process
    
    try:
        if opencv_process is None:
            return jsonify({'error': 'No analysis process is running'}), 404
        
        # Check if process is still running
        if opencv_process.poll() is not None:
            opencv_process = None
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
            
            opencv_process = None
            
            return jsonify({
                'success': True,
                'message': 'Analysis process terminated successfully'
            })
            
        except psutil.NoSuchProcess:
            opencv_process = None
            return jsonify({
                'success': True,
                'message': 'Analysis process was already terminated'
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)
