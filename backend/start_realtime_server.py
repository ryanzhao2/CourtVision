#!/usr/bin/env python3
"""
Startup script for the real-time basketball analysis WebSocket server.
This script initializes the WebSocket server that handles live video analysis.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from realtime_analysis import start_websocket_server

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('realtime_server.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to start the WebSocket server."""
    try:
        logger.info("Starting Basketball Analysis WebSocket Server...")
        logger.info("Server will be available at ws://localhost:8765")
        logger.info("Press Ctrl+C to stop the server")
        
        # Start the WebSocket server
        await start_websocket_server(host="localhost", port=8765)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 