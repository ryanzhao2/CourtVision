#!/usr/bin/env python3
"""
Test script to check if the backend can start without errors
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        import flask
        import pymongo
        import jwt
        import werkzeug
        import flask_cors
        print("✓ Basic imports successful")
        
        # Test our modules
        from mongodb import create_user, get_user
        print("✓ MongoDB module imported")
        
        from user import app
        print("✓ User module imported")
        
        # Test main.py imports
        from utils import read_video, save_video
        print("✓ Utils module imported")
        
        from trackers import PlayerTracker, BallTracker
        print("✓ Trackers module imported")
        
        from team_assigner import TeamAssigner
        print("✓ Team assigner module imported")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_flask_app():
    """Test if Flask app can be created"""
    try:
        print("\nTesting Flask app creation...")
        from user import app
        
        # Test if app has required routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        required_routes = ['/api/analyze', '/api/analysis-status', '/login', '/signup']
        
        for route in required_routes:
            if route in routes:
                print(f"✓ Route {route} found")
            else:
                print(f"✗ Route {route} missing")
                return False
        
        print("✓ Flask app creation successful")
        return True
        
    except Exception as e:
        print(f"✗ Flask app error: {e}")
        return False

def main():
    """Main test function"""
    print("Backend Test Script")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        sys.exit(1)
    
    # Test Flask app
    if not test_flask_app():
        print("\n❌ Flask app tests failed")
        sys.exit(1)
    
    print("\n✅ All tests passed! Backend should start successfully.")
    print("\nTo start the backend, run:")
    print("python3 start_backend.py")

if __name__ == "__main__":
    main() 