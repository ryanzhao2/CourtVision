#!/usr/bin/env python3
"""
Startup script for the Flask server that handles authentication and API endpoints.
This server runs on port 5002 and handles user authentication, signup, login, etc.
"""

import sys
import os
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flask_server.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to start the Flask server."""
    try:
        logger.info("Starting Flask Authentication Server...")
        logger.info("Server will be available at http://localhost:5002")
        logger.info("Press Ctrl+C to stop the server")
        
        # Start the Flask server
        app.run(debug=True, host='0.0.0.0', port=5002)
        
    except KeyboardInterrupt:
        logger.info("Flask server stopped by user")
    except Exception as e:
        logger.error(f"Error starting Flask server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Flask server shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 