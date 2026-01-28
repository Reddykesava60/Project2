"""
PHASE 3: Test Live HTTP Request
================================
This simulates exactly what the browser does.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

print("="*70)
print("PHASE 3: LIVE HTTP REQUEST TEST")
print("="*70)

# Step 1: Login as staff
print("\n1. Logging in as staff...")
login_resp = requests.post(f"{BASE_URL}/auth/login/", json={
    "email": "staff@restaurant.com",
    "password": "Test123!"
})

if login_resp.status_code != 200:
    print(f"❌ Login failed: {login_resp.status_code}")
    print(login_resp.text[:500])
    exit(1)

tokens = login_resp.json()
access_token = tokens.get('access')
print(f"✅ Login successful")

# Step 2: Get staff's restaurant ID
headers = {"Authorization": f"Bearer {access_token}"}

me_resp = requests.get(f"{BASE_URL}/me/", headers=headers)
if me_resp.status_code == 200:
    user_data = me_resp.json()
    restaurant_id = user_data.get('restaurant_id') or user_data.get('restaurant', {}).get('id')
    print(f"✅ Got user profile, restaurant_id: {restaurant_id}")
else:
    print(f"⚠️  Could not get /me endpoint: {me_resp.status_code}")
    restaurant_id = "d119ce38-78b7-4299-bf5d-40ad7321477b"  # Fallback

# Step 3: Call the EXACT endpoint frontend uses
print("\n" + "="*70)
print(f"2. Calling: GET /api/orders/active/?restaurant={restaurant_id}")
print("="*70)

orders_resp = requests.get(
    f"{BASE_URL}/orders/active/",
    params={"restaurant": restaurant_id},
    headers=headers
)

print(f"\nHTTP Status: {orders_resp.status_code}")
print(f"Response Headers:")
for key in ['content-type', 'content-length']:
    print(f"  {key}: {orders_resp.headers.get(key, 'N/A')}")

if orders_resp.status_code == 200:
    data = orders_resp.json()
    
    if isinstance(data, list):
        orders = data
    elif isinstance(data, dict) and 'results' in data:
        orders = data['results']
    else:
        orders = []
        print(f"Unexpected response format: {type(data)}")
    
    print(f"\nTotal orders returned: {len(orders)}")
    print("\nOrders:")
    for order in orders:
        oid = order.get('id', 'N/A')[:8] if order.get('id') else 'N/A'
        status = order.get('status', 'N/A')
        customer = order.get('customer_name', 'N/A')
        print(f"  ID: {oid}... | Status: {status:20} | Customer: {customer}")
    
    # Check for completed/cancelled
    completed = [o for o in orders if o.get('status') in ['completed', 'COMPLETED']]
    cancelled = [o for o in orders if o.get('status') in ['cancelled', 'CANCELLED']]
    
    print(f"\n⚠️  COMPLETED in response: {len(completed)}")
    print(f"⚠️  CANCELLED in response: {len(cancelled)}")
    
    print("\n" + "="*70)
    print("PHASE 3 VERDICT")
    print("="*70)
    if len(completed) == 0 and len(cancelled) == 0:
        print("✅ Live HTTP API returns ONLY active orders")
        print("✅ No COMPLETED or CANCELLED orders in response")
        print("\n🔍 If UI still shows completed orders, the problem is:")
        print("   - Frontend caching old data")
        print("   - Frontend calling a different endpoint")
        print("   - Frontend not refreshing after status update")
    else:
        print("❌ Live HTTP API is returning completed/cancelled orders!")
        print("   Backend filtering is broken.")
else:
    print(f"❌ Request failed: {orders_resp.status_code}")
    print(orders_resp.text[:500])
