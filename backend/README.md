# Backend Setup

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the backend directory with your MongoDB password:
```
MONGO_PASSWORD=your_actual_mongodb_password
```

3. Run the Flask server:
```bash
python user.py
```

The server will start on `http://127.0.0.1:5000`

## Endpoints

- `POST /signup` - Create a new user account
- `POST /login` - Authenticate user login

## Dependencies

- Flask - Web framework
- pymongo - MongoDB driver
- python-dotenv - Environment variable management
- flask-cors - Cross-origin resource sharing
- Werkzeug - Password hashing utilities 