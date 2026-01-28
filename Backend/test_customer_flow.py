"""
End-to-End Customer Order Flow Test
Tests the complete customer journey from menu view to order placement
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
RESTAURANT_SLUG = "italian-place"

print("=" * 80)
print("CUSTOMER ORDER FLOW TEST")
print("=" * 80)
print(f"Testing restaurant: {RESTAURANT_SLUG}")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Step 1: Get Restaurant by Slug (Public API)
print("\n[Step 1] Getting restaurant by slug...")
try:
    restaurant_response = requests.get(f"{BASE_URL}/restaurants/slug/{RESTAURANT_SLUG}/")
    print(f"Status: {restaurant_response.status_code}")
    
    if restaurant_response.status_code == 200:
        restaurant = restaurant_response.json()
        restaurant_id = restaurant.get("id")
        print(f"✅ Restaurant found: {restaurant.get('name')}")
        print(f"Restaurant ID: {restaurant_id}")
    else:
        print(f"❌ Failed to get restaurant: {restaurant_response.text[:200]}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Step 2: Get Menu (Public API)
print(f"\n[Step 2] Getting menu for restaurant ID: {restaurant_id}...")
try:
    menu_response = requests.get(f"{BASE_URL}/restaurants/{restaurant_id}/menu/")
    print(f"Status: {menu_response.status_code}")
    
    if menu_response.status_code == 200:
        menu_categories = menu_response.json()
        print(f"✅ Menu loaded: {len(menu_categories)} categories")
        
        # Display menu
        for category in menu_categories:
            print(f"\n  Category: {category.get('name')}")
            items = category.get('items', [])
            for item in items:
                print(f"    - {item.get('name')} - ₹{item.get('price')}")
        
        # Select first available item for order
        if menu_categories and menu_categories[0].get('items'):
            test_item = menu_categories[0]['items'][0]
            print(f"\n  Selected item for test order: {test_item.get('name')} (₹{test_item.get('price')})")
        else:
            print("❌ No menu items available!")
            exit(1)
    else:
        print(f"❌ Failed to get menu: {menu_response.text[:200]}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Step 3: Create Order (Cash Payment)
print(f"\n[Step 3] Creating order (Cash Payment)...")
order_data = {
    "restaurant": restaurant_id,
    "customer_name": "Test Customer",
    "items": [
        {
            "menu_item": test_item.get('id'),
            "quantity": 2,
            "price": test_item.get('price')
        }
    ],
    "payment_method": "cash",
    "total_amount": test_item.get('price') * 2
}

try:
    order_response = requests.post(
        f"{BASE_URL}/orders/",
        json=order_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {order_response.status_code}")
    
    if order_response.status_code in [200, 201]:
        order = order_response.json()
        order_id = order.get('id')
        order_number = order.get('order_number')
        print(f"✅ Order created successfully!")
        print(f"Order ID: {order_id}")
        print(f"Order Number: {order_number}")
        print(f"Status: {order.get('status')}")
        print(f"Total: ₹{order.get('total_amount')}")
    else:
        print(f"❌ Order creation failed: {order_response.text[:500]}")
        print(f"\nRequest data: {json.dumps(order_data, indent=2)}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Step 4: Verify Order in Database
print(f"\n[Step 4] Verifying order in database...")
import sqlite3

try:
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, order_number, status, customer_name, total_amount, payment_method
        FROM orders_order 
        WHERE order_number = ?
    """, (order_number,))
    
    db_order = cursor.fetchone()
    
    if db_order:
        print(f"✅ Order found in database!")
        print(f"DB Order Number: {db_order[1]}")
        print(f"DB Status: {db_order[2]}")
        print(f"DB Customer: {db_order[3]}")
        print(f"DB Total: ₹{db_order[4]}")
        print(f"DB Payment Method: {db_order[5]}")
    else:
        print(f"❌ Order not found in database!")
    
    conn.close()
except Exception as e:
    print(f"❌ Database error: {e}")

# Step 5: Test Order Retrieval (Staff Flow)
print(f"\n[Step 5] Testing order retrieval...")
print("Logging in as staff...")

try:
    # Staff login
    login_response = requests.post(
        f"{BASE_URL}/auth/login/",
        json={"email": "staff@restaurant.com", "password": "staff123"}
    )
    
    if login_response.status_code == 200:
        staff_token = login_response.json().get("access")
        print(f"✅ Staff logged in")
        
        # Get active orders
        active_orders_response = requests.get(
            f"{BASE_URL}/orders/active/",
            params={"restaurant": restaurant_id},
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        
        print(f"Active orders status: {active_orders_response.status_code}")
        
        if active_orders_response.status_code == 200:
            active_orders = active_orders_response.json()
            print(f"✅ Active orders retrieved: {len(active_orders)} orders")
            
            # Check if our order is in the list
            order_found = any(o.get('order_number') == order_number for o in active_orders)
            if order_found:
                print(f"✅ Test order found in active orders!")
            else:
                print(f"⚠️  Test order not in active orders (may be filtered)")
        else:
            print(f"❌ Failed to get active orders: {active_orders_response.text[:200]}")
    else:
        print(f"❌ Staff login failed")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
