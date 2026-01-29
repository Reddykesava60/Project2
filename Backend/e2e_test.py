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

DB_PATH = 'db.sqlite3'

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
# PHASE 2: CUSTOMER FLOW TESTS
# ============================================
def test_customer_menu():
    """Test customer QR scan → menu load"""
    print_section("TEST: Customer Menu Endpoint (QR Scan)")
    try:
        r = requests.get(f'{BASE}/api/public/r/italian-place/menu/', timeout=5)
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            print(f"Restaurant: {data.get('restaurant', {}).get('name')}")
            print(f"Categories: {len(data.get('categories', []))}")
            for cat in data.get('categories', []):
                print(f"  - {cat['name']}: {len(cat.get('items', []))} items")
            return data
        else:
            print(f"Error: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_create_cash_order(menu_data):
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
    
    try:
        r = requests.post(
            f'{BASE}/api/public/r/italian-place/order/',
            json=order_data,
            timeout=5
        )
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            order = data.get('order', data)
            print(f"Order Number: {order.get('order_number')}")
            print(f"Status: {order.get('status')}")
            print(f"Payment Status: {order.get('payment_status')}")
            print(f"Payment Method: {order.get('payment_method')}")
            return order
        else:
            print(f"Error: {r.text[:500]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_create_upi_order(menu_data):
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
    
    try:
        r = requests.post(
            f'{BASE}/api/public/r/italian-place/order/',
            json=order_data,
            timeout=5
        )
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            order = data.get('order', data)
            print(f"Order Number: {order.get('order_number')}")
            print(f"Status: {order.get('status')}")
            print(f"Payment Status: {order.get('payment_status')}")
            print(f"Payment Method: {order.get('payment_method')}")
            return order
        else:
            print(f"Error: {r.text[:500]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# ============================================
# PHASE 3: STAFF VIEW TESTS
# ============================================
def test_staff_login():
    """Login as staff user"""
    print_section("TEST: Staff Login")
    try:
        r = requests.post(
            f'{BASE}/api/auth/login/',
            json={"email": "staff@restaurant.com", "password": "password123"},
            timeout=5
        )
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            token = data.get('access')
            user = data.get('user', {})
            print(f"User: {user.get('email')}")
            print(f"Role: {user.get('role')}")
            print(f"Can Collect Cash: {user.get('can_collect_cash')}")
            print(f"Token: {token[:20]}..." if token else "No token")
            return token
        else:
            print(f"Error: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_staff_orders(token):
    """Get orders visible to staff"""
    print_section("TEST: Staff Orders View")
    if not token:
        print("SKIP: No token")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(
            f'{BASE}/api/orders/',
            headers=headers,
            timeout=5
        )
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            orders = data if isinstance(data, list) else data.get('results', [])
            print(f"Total Orders Visible: {len(orders)}")
            for o in orders:
                print(f"  - {o.get('order_number')}: status={o.get('status')}, payment={o.get('payment_status')}, method={o.get('payment_method')}")
            return orders
        else:
            print(f"Error: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# ============================================
# PHASE 4: OWNER VIEW TESTS
# ============================================
def test_owner_login():
    """Login as owner user"""
    print_section("TEST: Owner Login")
    try:
        r = requests.post(
            f'{BASE}/api/auth/login/',
            json={"email": "owner@restaurant.com", "password": "password123"},
            timeout=5
        )
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            token = data.get('access')
            user = data.get('user', {})
            print(f"User: {user.get('email')}")
            print(f"Role: {user.get('role')}")
            print(f"Restaurant ID: {user.get('restaurant_id')}")
            print(f"Token: {token[:20]}..." if token else "No token")
            return token, user.get('restaurant_id')
        else:
            print(f"Error: {r.text[:200]}")
            return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def test_owner_orders(token, restaurant_id):
    """Get all orders visible to owner"""
    print_section("TEST: Owner Orders View")
    if not token:
        print("SKIP: No token")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"restaurant": restaurant_id} if restaurant_id else {}
        r = requests.get(
            f'{BASE}/api/orders/',
            headers=headers,
            params=params,
            timeout=5
        )
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            orders = data if isinstance(data, list) else data.get('results', [])
            print(f"Total Orders Visible: {len(orders)}")
            
            # Count by status
            status_counts = {}
            for o in orders:
                s = o.get('status')
                status_counts[s] = status_counts.get(s, 0) + 1
            print(f"Status Breakdown: {status_counts}")
            return orders
        else:
            print(f"Error: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_owner_analytics(token, restaurant_id):
    """Get owner analytics"""
    print_section("TEST: Owner Analytics")
    if not token:
        print("SKIP: No token")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"restaurant": restaurant_id} if restaurant_id else {}
        r = requests.get(
            f'{BASE}/api/analytics/dashboard/',
            headers=headers,
            params=params,
            timeout=5
        )
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            print(f"Analytics: {json.dumps(data, indent=2)[:500]}")
            return data
        else:
            print(f"Error: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# ============================================
# PHASE 5: ADMIN VIEW TESTS
# ============================================
def test_admin_login():
    """Login as admin user"""
    print_section("TEST: Admin Login")
    try:
        r = requests.post(
            f'{BASE}/api/auth/login/',
            json={"email": "admin@dineflow.com", "password": "admin123"},
            timeout=5
        )
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            token = data.get('access')
            user = data.get('user', {})
            print(f"User: {user.get('email')}")
            print(f"Role: {user.get('role')}")
            print(f"Token: {token[:20]}..." if token else "No token")
            return token
        else:
            print(f"Error: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_admin_restaurants(token):
    """Get all restaurants as admin"""
    print_section("TEST: Admin Restaurants View")
    if not token:
        print("SKIP: No token")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(
            f'{BASE}/api/restaurants/',
            headers=headers,
            timeout=5
        )
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            restaurants = data if isinstance(data, list) else data.get('results', [])
            print(f"Total Restaurants: {len(restaurants)}")
            for rest in restaurants:
                print(f"  - {rest.get('name')} (slug: {rest.get('slug')}, status: {rest.get('status')})")
            return restaurants
        else:
            print(f"Error: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# ============================================
# PHASE 6: DATABASE VERIFICATION
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
    print("\nRevenue by Payment Method:")
    for row in conn.execute('''
        SELECT payment_method, SUM(total_amount) as revenue, COUNT(*) as orders
        FROM orders_order 
        WHERE status = 'completed'
        GROUP BY payment_method
    ''').fetchall():
        print(f"  {dict(row)}")
    
    conn.close()

# ============================================
# MAIN
# ============================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("  ORDERFLOW E2E VALIDATION")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    # Phase 1: Database Truth
    verify_db_truth()
    
    # Phase 2: Customer Flow
    menu = test_customer_menu()
    cash_order = test_create_cash_order(menu)
    upi_order = test_create_upi_order(menu)
    
    # Phase 3: Staff View
    staff_token = test_staff_login()
    staff_orders = test_staff_orders(staff_token)
    
    # Phase 4: Owner View
    owner_token, restaurant_id = test_owner_login()
    owner_orders = test_owner_orders(owner_token, restaurant_id)
    owner_analytics = test_owner_analytics(owner_token, restaurant_id)
    
    # Phase 5: Admin View
    admin_token = test_admin_login()
    admin_restaurants = test_admin_restaurants(admin_token)
    
    # Final DB Truth
    verify_db_truth()
    
    print("\n" + "="*60)
    print("  E2E VALIDATION COMPLETE")
    print("="*60)
