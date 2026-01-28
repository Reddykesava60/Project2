"""
Comprehensive Authentication Testing Script
Tests all user roles and auth flows
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=" * 80)
print("DINEFLOW AUTHENTICATION TESTING")
print("=" * 80)

# Test credentials
test_users = [
    {"email": "admin@dineflow.com", "password": "admin123", "role": "Platform Admin"},
    {"email": "owner@restaurant.com", "password": "owner123", "role": "Restaurant Owner"},
    {"email": "staff@restaurant.com", "password": "staff123", "role": "Staff"},
]

results = []

for user in test_users:
    print(f"\n{'=' * 80}")
    print(f"Testing: {user['role']} ({user['email']})")
    print("=" * 80)
    
    # Test Login
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login/",
            json={"email": user["email"], "password": user["password"]},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            data = login_response.json()
            access_token = data.get("access")
            user_data = data.get("user")
            
            print(f"✅ Login successful!")
            print(f"User ID: {user_data.get('id')}")
            print(f"Role: {user_data.get('role')}")
            print(f"Email: {user_data.get('email')}")
            print(f"Restaurant ID: {user_data.get('restaurant_id')}")
            
            # Test /auth/me/ endpoint
            print(f"\nTesting /auth/me/ endpoint...")
            me_response = requests.get(
                f"{BASE_URL}/auth/me/",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            print(f"/auth/me/ Status: {me_response.status_code}")
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                print(f"✅ /auth/me/ successful!")
                print(f"User: {me_data.get('email')} - {me_data.get('role')}")
            else:
                print(f"❌ /auth/me/ failed: {me_response.text[:200]}")
            
            results.append({
                "role": user["role"],
                "email": user["email"],
                "login": "SUCCESS",
                "token": access_token[:20] + "...",
                "user_id": user_data.get("id"),
                "restaurant_id": user_data.get("restaurant_id")
            })
        else:
            print(f"❌ Login failed!")
            print(f"Response: {login_response.text[:300]}")
            results.append({
                "role": user["role"],
                "email": user["email"],
                "login": "FAILED",
                "error": login_response.text[:100]
            })
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        results.append({
            "role": user["role"],
            "email": user["email"],
            "login": "ERROR",
            "error": str(e)
        })

# Summary
print(f"\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)

for result in results:
    status_icon = "✅" if result.get("login") == "SUCCESS" else "❌"
    print(f"{status_icon} {result['role']:20} - {result['email']:30} - {result['login']}")

print(f"\n{'=' * 80}")
print(f"Total Tests: {len(results)}")
print(f"Passed: {sum(1 for r in results if r.get('login') == 'SUCCESS')}")
print(f"Failed: {sum(1 for r in results if r.get('login') != 'SUCCESS')}")
print("=" * 80)
