from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from mongodb import create_user, get_user

app = Flask(__name__)
CORS(app)

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

    hashed_password = generate_password_hash(password)

    user_id = create_user(first_name, last_name, email, hashed_password)
    if user_id:
        return jsonify({"message": "User created successfully", "user_id": str(user_id)}), 201
    else:
        return jsonify({"error": "Failed to create user"}), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = get_user(email)
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": f"Welcome, {user['first_name']}!"}), 200


if __name__ == "__main__":
    app.run(debug=True)
