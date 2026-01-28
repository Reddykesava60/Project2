"""Live API test for staff orders."""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

# Login as staff
print("="*60)
print("LOGIN AS STAFF")
print("="*60)
login_resp = requests.post(f'{BASE_URL}/api/auth/login/', json={
    'email': 'staff@restaurant.com',
    'password': 'Test123!'
})
print(f'Login Status: {login_resp.status_code}')

if login_resp.status_code == 200:
    tokens = login_resp.json()
    access_token = tokens.get('access')
    headers = {'Authorization': f'Bearer {access_token}'}
    
    print("\n" + "="*60)
    print("GET /api/orders/active/ AS STAFF")
    print("="*60)
    
    orders_resp = requests.get(f'{BASE_URL}/api/orders/active/', headers=headers)
    print(f'Status: {orders_resp.status_code}')
    
    if orders_resp.status_code == 200:
        orders = orders_resp.json()
        print(f'Order Count: {len(orders)}')
        for order in orders:
            print(f'  Status: {order.get("status")}, Customer: {order.get("customer_name")}')
        
        # Check for completed
        completed = [o for o in orders if o.get('status') in ['completed', 'COMPLETED']]
        cancelled = [o for o in orders if o.get('status') in ['cancelled', 'CANCELLED']]
        
        print(f'\nCompleted in response: {len(completed)}')
        print(f'Cancelled in response: {len(cancelled)}')
        
        if completed or cancelled:
            print("\n🚨 BUG: Staff sees completed/cancelled orders!")
        else:
            print("\n✅ SUCCESS: Staff only sees active orders")
    else:
        print(f'Error: {orders_resp.text[:500]}')
else:
    print(f'Login failed: {login_resp.text[:500]}')
