#!/usr/bin/env python
"""E2E Validation Script for OrderFlow - Using Django Test Client"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
import json
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')

User = get_user_model()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ============================================
# PHASE 1: DATABASE TRUTH
# ============================================
def verify_db_truth():
    """Get current database state"""
    print_section("DATABASE TRUTH VERIFICATION")
    conn = get_db_connection()
    
    # Order counts
    print("\nOrder Counts by Status:")
    for row in conn.execute('''
        SELECT status, payment_status, payment_method, COUNT(*) as count 
        FROM orders_order 
        GROUP BY status, payment_status, payment_method
    ''').fetchall():
        print(f"  {dict(row)}")
    
    # Total revenue
    print("\nRevenue by Payment Method (completed orders):")
    for row in conn.execute('''
        SELECT payment_method, SUM(total_amount) as revenue, COUNT(*) as orders
        FROM orders_order 
        WHERE status = 'completed'
        GROUP BY payment_method
    ''').fetchall():
        print(f"  {dict(row)}")
    
    # All orders
    print("\nAll Orders:")
    for row in conn.execute('''
        SELECT order_number, status, payment_status, payment_method, total_amount, customer_name
        FROM orders_order 
        ORDER BY created_at DESC
    ''').fetchall():
        print(f"  {dict(row)}")
    
    conn.close()

# ============================================
# PHASE 2: CUSTOMER FLOW TESTS
# ============================================
def test_customer_menu(client):
    """Test customer QR scan → menu load"""
    print_section("TEST: Customer Menu Endpoint (QR Scan)")
    
    response = client.get('/api/public/r/italian-place/menu/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Restaurant: {data.get('restaurant', {}).get('name')}")
        print(f"Categories: {len(data.get('categories', []))}")
        for cat in data.get('categories', []):
            print(f"  - {cat['name']}: {len(cat.get('items', []))} items")
        return data
    else:
        print(f"Error: {response.content[:500]}")
        return None

def test_create_cash_order(client, menu_data):
    """Create a cash order as customer"""
    print_section("TEST: Create Cash Order")
    if not menu_data:
        print("SKIP: No menu data")
        return None
    
    # Get first menu item
    items = []
    for cat in menu_data.get('categories', []):
        for item in cat.get('items', []):
            items.append(item)
            break
        if items:
            break
    
    if not items:
        print("SKIP: No menu items found")
        return None
    
    order_data = {
        "items": [{"menu_item_id": items[0]['id'], "quantity": 1}],
        "customer_name": "E2E Cash Test",
        "payment_method": "cash",
        "privacy_accepted": True
    }
    
    response = client.post(
        '/api/public/r/italian-place/order/',
        data=json.dumps(order_data),
        content_type='application/json'
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        data = response.json()
        order = data.get('order', data)
        print(f"Order Number: {order.get('order_number')}")
        print(f"Status: {order.get('status')}")
        print(f"Payment Status: {order.get('payment_status')}")
        print(f"Payment Method: {order.get('payment_method')}")
        
        # VALIDATION: Cash order should be pending/pending
        expected_status = 'pending'
        expected_payment = 'pending'
        actual_status = order.get('status')
        actual_payment = order.get('payment_status')
        
        if actual_status == expected_status and actual_payment == expected_payment:
            print(f"✅ PASS: Cash order status is correct")
        else:
            print(f"❌ FAIL: Expected {expected_status}/{expected_payment}, got {actual_status}/{actual_payment}")
        
        return order
    else:
        print(f"Error: {response.content[:500]}")
        return None

def test_create_upi_order(client, menu_data):
    """Create a UPI order as customer"""
    print_section("TEST: Create UPI Order")
    if not menu_data:
        print("SKIP: No menu data")
        return None
    
    # Get first menu item
    items = []
    for cat in menu_data.get('categories', []):
        for item in cat.get('items', []):
            items.append(item)
            break
        if items:
            break
    
    if not items:
        print("SKIP: No menu items found")
        return None
    
    order_data = {
        "items": [{"menu_item_id": items[0]['id'], "quantity": 1}],
        "customer_name": "E2E UPI Test",
        "payment_method": "upi",
        "privacy_accepted": True
    }
    
    response = client.post(
        '/api/public/r/italian-place/order/',
        data=json.dumps(order_data),
        content_type='application/json'
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        data = response.json()
        order = data.get('order', data)
        print(f"Order Number: {order.get('order_number')}")
        print(f"Status: {order.get('status')}")
        print(f"Payment Status: {order.get('payment_status')}")
        print(f"Payment Method: {order.get('payment_method')}")
        
        # VALIDATION: UPI order should be pending/pending until payment verified
        # (In real flow, after Razorpay callback it would be preparing/success)
        actual_status = order.get('status')
        actual_payment = order.get('payment_status')
        print(f"INFO: UPI order created with {actual_status}/{actual_payment}")
        print(f"INFO: Payment verification would move to preparing/success")
        
        return order
    else:
        print(f"Error: {response.content[:500]}")
        return None

# ============================================
# PHASE 3: STAFF VIEW TESTS
# ============================================
def test_staff_login(client):
    """Login as staff user"""
    print_section("TEST: Staff Login")
    
    response = client.post(
        '/api/auth/login/',
        data=json.dumps({"email": "staff@restaurant.com", "password": "staff123"}),
        content_type='application/json'
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access')
        user = data.get('user', {})
        print(f"User: {user.get('email')}")
        print(f"Role: {user.get('role')}")
        print(f"Can Collect Cash: {user.get('can_collect_cash')}")
        return token, user.get('can_collect_cash', False)
    else:
        print(f"Error: {response.content[:500]}")
        return None, False

def test_staff_orders(client, token):
    """Get orders visible to staff"""
    print_section("TEST: Staff Orders View")
    if not token:
        print("SKIP: No token")
        return None
    
    response = client.get(
        '/api/orders/',
        HTTP_AUTHORIZATION=f'Bearer {token}'
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        orders = data if isinstance(data, list) else data.get('results', [])
        print(f"Total Orders Visible: {len(orders)}")
        
        # Count by status
        status_counts = {}
        for o in orders:
            s = o.get('status')
            status_counts[s] = status_counts.get(s, 0) + 1
            print(f"  - {o.get('order_number')}: status={o.get('status')}, payment={o.get('payment_status')}, method={o.get('payment_method')}")
        
        print(f"Status Breakdown: {status_counts}")
        
        # VALIDATION: Staff should NOT see completed orders
        if 'completed' in status_counts:
            print(f"❌ FAIL: Staff can see {status_counts['completed']} completed orders (should be 0)")
        else:
            print(f"✅ PASS: Staff cannot see completed orders")
        
        return orders
    else:
        print(f"Error: {response.content[:500]}")
        return None

# ============================================
# PHASE 4: OWNER VIEW TESTS
# ============================================
def test_owner_login(client):
    """Login as owner user"""
    print_section("TEST: Owner Login")
    
    response = client.post(
        '/api/auth/login/',
        data=json.dumps({"email": "owner@restaurant.com", "password": "owner123"}),
        content_type='application/json'
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access')
        user = data.get('user', {})
        print(f"User: {user.get('email')}")
        print(f"Role: {user.get('role')}")
        print(f"Restaurant ID: {user.get('restaurant_id')}")
        return token, user.get('restaurant_id')
    else:
        print(f"Error: {response.content[:500]}")
        return None, None

def test_owner_orders(client, token, restaurant_id):
    """Get all orders visible to owner"""
    print_section("TEST: Owner Orders View")
    if not token:
        print("SKIP: No token")
        return None
    
    url = f'/api/orders/?restaurant={restaurant_id}' if restaurant_id else '/api/orders/'
    response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        orders = data if isinstance(data, list) else data.get('results', [])
        print(f"Total Orders Visible: {len(orders)}")
        
        # Count by status
        status_counts = {}
        for o in orders:
            s = o.get('status')
            status_counts[s] = status_counts.get(s, 0) + 1
        print(f"Status Breakdown: {status_counts}")
        
        # Compare with DB
        conn = get_db_connection()
        db_count = conn.execute('SELECT COUNT(*) FROM orders_order WHERE restaurant_id = ?', 
                                (restaurant_id.replace('-', ''),)).fetchone()[0]
        conn.close()
        
        if len(orders) == db_count:
            print(f"✅ PASS: Owner sees all {db_count} orders")
        else:
            print(f"❌ FAIL: Owner sees {len(orders)} orders but DB has {db_count}")
        
        return orders
    else:
        print(f"Error: {response.content[:500]}")
        return None

def test_owner_analytics(client, token, restaurant_id):
    """Get owner analytics"""
    print_section("TEST: Owner Analytics")
    if not token:
        print("SKIP: No token")
        return None
    
    url = f'/api/analytics/dashboard/?restaurant={restaurant_id}' if restaurant_id else '/api/analytics/dashboard/'
    response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Analytics Response: {json.dumps(data, indent=2)[:1000]}")
        return data
    else:
        print(f"Error: {response.content[:500]}")
        return None

# ============================================
# PHASE 5: ADMIN VIEW TESTS
# ============================================
def test_admin_login(client):
    """Login as admin user"""
    print_section("TEST: Admin Login")
    
    response = client.post(
        '/api/auth/login/',
        data=json.dumps({"email": "admin@dineflow.com", "password": "admin123"}),
        content_type='application/json'
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access')
        user = data.get('user', {})
        print(f"User: {user.get('email')}")
        print(f"Role: {user.get('role')}")
        return token
    else:
        print(f"Error: {response.content[:500]}")
        return None

def test_admin_restaurants(client, token):
    """Get all restaurants as admin"""
    print_section("TEST: Admin Restaurants View")
    if not token:
        print("SKIP: No token")
        return None
    
    response = client.get('/api/restaurants/', HTTP_AUTHORIZATION=f'Bearer {token}')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        restaurants = data if isinstance(data, list) else data.get('results', [])
        print(f"Total Restaurants: {len(restaurants)}")
        for rest in restaurants:
            print(f"  - {rest.get('name')} (slug: {rest.get('slug')}, status: {rest.get('status')})")
        
        # Compare with DB
        conn = get_db_connection()
        db_count = conn.execute('SELECT COUNT(*) FROM restaurants_restaurant').fetchone()[0]
        conn.close()
        
        if len(restaurants) == db_count:
            print(f"✅ PASS: Admin sees all {db_count} restaurants")
        else:
            print(f"❌ FAIL: Admin sees {len(restaurants)} restaurants but DB has {db_count}")
        
        return restaurants
    else:
        print(f"Error: {response.content[:500]}")
        return None

# ============================================
# MAIN
# ============================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("  ORDERFLOW E2E VALIDATION")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    # Create Django test client
    client = Client()
    
    # Phase 1: Database Truth
    verify_db_truth()
    
    # Phase 2: Customer Flow
    menu = test_customer_menu(client)
    cash_order = test_create_cash_order(client, menu)
    upi_order = test_create_upi_order(client, menu)
    
    # Phase 3: Staff View
    staff_token, can_collect_cash = test_staff_login(client)
    staff_orders = test_staff_orders(client, staff_token)
    
    # Phase 4: Owner View
    owner_token, restaurant_id = test_owner_login(client)
    owner_orders = test_owner_orders(client, owner_token, restaurant_id)
    owner_analytics = test_owner_analytics(client, owner_token, restaurant_id)
    
    # Phase 5: Admin View
    admin_token = test_admin_login(client)
    admin_restaurants = test_admin_restaurants(client, admin_token)
    
    # Final DB Truth
    verify_db_truth()
    
    print("\n" + "="*60)
    print("  E2E VALIDATION COMPLETE")
    print("="*60)
