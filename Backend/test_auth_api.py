import requests
import json

base_url = "http://localhost:8000/api"

# Test 1: Login with owner credentials
print("=" * 50)
print("TEST 1: Owner Login")
print("=" * 50)

try:
    response = requests.post(
        f"{base_url}/auth/login/",
        json={"email": "owner@restaurant.com", "password": "owner123"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access")
        print(f"\n✅ Login successful! Token: {token[:50]}...")
        
        # Test 2: Get current user with token
        print("\n" + "=" * 50)
        print("TEST 2: Get Current User (/auth/me/)")
        print("=" * 50)
        
        me_response = requests.get(
            f"{base_url}/auth/me/",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Status Code: {me_response.status_code}")
        print(f"Response: {json.dumps(me_response.json(), indent=2)}")
    else:
        print(f"\n❌ Login failed!")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Staff Login
print("\n" + "=" * 50)
print("TEST 3: Staff Login")
print("=" * 50)

try:
    response = requests.post(
        f"{base_url}/auth/login/",
        json={"email": "staff@restaurant.com", "password": "staff123"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Admin Login
print("\n" + "=" * 50)
print("TEST 4: Admin Login")
print("=" * 50)

try:
    response = requests.post(
        f"{base_url}/auth/login/",
        json={"email": "admin@dineflow.com", "password": "admin123"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")
