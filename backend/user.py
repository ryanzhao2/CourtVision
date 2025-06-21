from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from mongodb import create_user, get_user
import jwt
import datetime
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)

# JWT token expiration time (24 hours)
JWT_EXPIRATION_HOURS = 24

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

if __name__ == "__main__":
    app.run(debug=True)
