"""
Test login API with correct credentials
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login(email, password):
    print(f"\n{'='*60}")
    print(f"Testing login: {email}")
    print('='*60)
    
    url = f"{BASE_URL}/api/auth/login/"
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('user', {})
            print(f"✓ Login successful!")
            print(f"  User ID: {user.get('id')}")
            print(f"  Name: {user.get('first_name')} {user.get('last_name')}")
            print(f"  Email: {user.get('email')}")
            print(f"  Role: {user.get('role')}")
            print(f"  Restaurant ID: {user.get('restaurant_id')}")
            print(f"  Restaurant Name: {user.get('restaurant_name')}")
            return True
        else:
            print(f"✗ Login failed!")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    print("Testing Login API with Fixed Roles")
    print("=" * 60)
    
    # Test different user roles
    test_cases = [
        ("admin@dineflow.com", "admin123", "platform_admin"),
        ("owner@restaurant.com", "owner123", "restaurant_owner"),
        ("staff@restaurant.com", "staff123", "staff"),
    ]
    
    results = []
    for email, password, expected_role in test_cases:
        success = test_login(email, password)
        results.append((email, expected_role, success))
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    for email, expected_role, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status} - {email} ({expected_role})")
