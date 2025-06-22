#!/usr/bin/env python3
"""
Test script to verify backend authentication functionality
"""

import requests
import json

BASE_URL = "http://localhost:5002"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_signup():
    """Test user signup"""
    try:
        signup_data = {
            "firstName": "Test",
            "lastName": "User",
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = requests.post(
            f"{BASE_URL}/signup",
            json=signup_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Signup: {response.status_code} - {response.json()}")
        return response.status_code in [201, 409]  # 201 = created, 409 = already exists
    except Exception as e:
        print(f"Signup failed: {e}")
        return False

def test_login():
    """Test user login"""
    try:
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = requests.post(
            f"{BASE_URL}/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login: {response.status_code} - {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("token") is not None
        return False
    except Exception as e:
        print(f"Login failed: {e}")
        return False

def test_verify_token():
    """Test token verification"""
    try:
        # First login to get a token
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        login_response = requests.post(
            f"{BASE_URL}/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print("Login failed for token verification test")
            return False
            
        token = login_response.json().get("token")
        
        # Test token verification
        verify_data = {"token": token}
        response = requests.post(
            f"{BASE_URL}/verify-token",
            json=verify_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Token verification: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Token verification failed: {e}")
        return False

def test_profile():
    """Test protected profile endpoint"""
    try:
        # First login to get a token
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        login_response = requests.post(
            f"{BASE_URL}/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print("Login failed for profile test")
            return False
            
        token = login_response.json().get("token")
        
        # Test profile endpoint
        response = requests.get(
            f"{BASE_URL}/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Profile: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Profile test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Backend Authentication System")
    print("=" * 40)
    
    tests = [
        ("Health Check", test_health_check),
        ("Signup", test_signup),
        ("Login", test_login),
        ("Token Verification", test_verify_token),
        ("Profile", test_profile),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print(f"{test_name}: {'PASS' if result else 'FAIL'}")
    
    print("\n" + "=" * 40)
    print("Test Results Summary:")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

if __name__ == "__main__":
    main() 