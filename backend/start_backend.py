#!/usr/bin/env python3
"""
Startup script for the Flask backend server
"""

import os
import sys
from user import app

if __name__ == "__main__":
    print("Starting Flask Backend Server...")
    print("Server will be available at http://localhost:5002")
    print("This server can launch the basketball analysis desktop app")
    print("Press Ctrl+C to stop the server")
    
    try:
        app.run(host='0.0.0.0', port=5002, debug=True)
    except KeyboardInterrupt:
        print("\nServer shutdown complete")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1) 