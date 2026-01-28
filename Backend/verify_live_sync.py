import requests
import sqlite3
import time
import sys
import os

# Configuration
API_BASE = "http://localhost:8000/api"
DB_PATH = r"c:\User\Projects\Fresh\DineFlow2\Backend\db.sqlite3"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, success=True):
    color = GREEN if success else RED
    print(f"{color}{msg}{RESET}")

def check_db_order_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders_order")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def check_order_status_in_db(order_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status, payment_status FROM orders_order WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def verify_live_sync():
    print("=== STARTING LIVE SYNC VERIFICATION ===")
    
    # 1. Check Initial State
    initial_count = check_db_order_count()
    print(f"Initial DB Order Count: {initial_count}")

    # 2. Get Restaurant Slug (assuming 'dineflow-demo' or similar)
    # We will fetch public menu to get restaurant details
    try:
        # Assuming we can list or guess. Let's try to get a restaurant first.
        # Actually, let's login as admin to get a slug if needed, but public API is better.
        # We'll use the one from test setup if possible, or search.
        # Let's try common slugs or just list orders if we have a token.
        
        # We need a restaurant slug for public order.
        # Let's scan DB for a slug.
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT slug, id FROM restaurants_restaurant WHERE status='ACTIVE' LIMIT 1")
        row = cursor.fetchone()
        if not row:
            log("❌ No active restaurant found in DB", False)
            return
        slug, r_id = row
        print(f"Target Restaurant: {slug} (ID: {r_id})")
        
        # Get a menu item
        cursor.execute("SELECT id, price FROM menu_menuitem WHERE restaurant_id=? AND is_available=1 LIMIT 1", (r_id,))
        item_row = cursor.fetchone()
        if not item_row:
             log("❌ No menu items found", False)
             return
        item_id, item_price = item_row
        conn.close()
        
    except Exception as e:
        log(f"❌ DB Access Failed: {e}", False)
        return

    # 3. Create Public Order
    print("\n--- Step 1: Creating Public Order via API ---")
    payload = {
        "customer_name": "LiveSync Tester",
        "payment_method": "CASH", 
        "items": [
            {"menu_item_id": str(item_id), "quantity": 1}
        ],
        "privacy_accepted": True
    }
    
    try:
        start_time = time.time()
        res = requests.post(f"{API_BASE}/public/r/{slug}/order/", json=payload)
        end_time = time.time()
        
        if res.status_code != 201:
            log(f"❌ API Order Creation Failed: {res.status_code} {res.text}", False)
            return
            
        data = res.json()
        order_id = data['order']['id']
        order_number = data['order']['order_number']
        log(f"✅ API Created Order: {order_number} (ID: {order_id}) in {end_time - start_time:.2f}s")
        
        # Verify in DB immediately
        new_count = check_db_order_count()
        if new_count != initial_count + 1:
            log(f"❌ DB Sync Failed! Expected {initial_count + 1} orders, found {new_count}", False)
        else:
            log(f"✅ DB Persisted Order Successfully")
            
    except Exception as e:
        log(f"❌ API Request Failed: {e}", False)
        return

    # 4. Simulate Staff Fetch (Login first)
    print("\n--- Step 2: Staff Fetch Active Orders ---")
    # We need staff credentials. We can grab a staff user from DB or use admin.
    # Let's use the owner/admin for simplicity if they have access, or try to find a staff user.
    # We'll try 'staff@test.com' / 'test123' if it exists (from seed), or 'owner@restaurant.com'
    
    auth_token = None
    login_creds = [
        ('owner@restaurant.com', 'owner123'),
        ('staff@test.com', 'test123'),
        ('admin@test.com', 'test123')
    ]
    
    for email, pwd in login_creds:
        try:
            res = requests.post(f"{API_BASE}/auth/login/", json={"email": email, "password": pwd})
            if res.status_code == 200:
                auth_token = res.json().get('access') or res.json().get('token')
                print(f"Logged in as {email}")
                break
        except:
            continue
            
    if not auth_token:
        # Try to modify DB to start a known user if needed, or fail.
        # But we can check DB logic even without API login if we trust Step 1 passed.
        # But user wants "Frontend sync", so identifying if API returns it is key.
        log("⚠️ Could not login to verify Staff API fetch. Skipping API check, checking DB only.", False)
    else:
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Fetch active orders
        res = requests.get(f"{API_BASE}/orders/active/?restaurant={r_id}", headers=headers)
        if res.status_code == 200:
            active_orders = res.json()
            # Check if our order is there
            found = any(o['id'] == order_id for o in active_orders)
            if found:
                log(f"✅ Staff API lists new order {order_number}")
            else:
                log(f"❌ Staff API MISSING order {order_number}!", False)
        else:
            log(f"❌ Staff API Fetch Failed: {res.status_code}", False)

    # 5. Simulate Order Completion
    print("\n--- Step 3: Complete Order ---")
    if auth_token:
        # Mark completed
        # Note: If cash, might need payment first. 'cash' creates 'AWAITING_PAYMENT'.
        # Staff needs to collect cash.
        
        # 3a. Collect Cash
        res_pay = requests.post(f"{API_BASE}/orders/{order_id}/cash/", headers=headers)
        if res_pay.status_code == 200:
            log("✅ Payment collected via API")
        else:
            log(f"⚠️ Payment collection failed/skipped: {res_pay.status_code}")

        # 3b. Update Status -> Completed
        res_done = requests.post(f"{API_BASE}/orders/{order_id}/update_status/", json={"status": "COMPLETED"}, headers=headers)
        
        if res_done.status_code == 200:
            log("✅ API Marked Completed")
            
            # Verify DB Status
            db_status, db_pay = check_order_status_in_db(order_id)
            if db_status == 'completed': # Standardize case later
                log(f"✅ DB Status Updated to: {db_status}")
            elif db_status == 'COMPLETED':
                log(f"✅ DB Status Updated to: {db_status}")
            else:
                log(f"❌ DB Sync Failed! Status is {db_status}, expected COMPLETED", False)
        else:
            log(f"❌ API Completion Failed: {res_done.status_code} {res_done.text}", False)
            
    else:
        log("Skipping completion test due to login failure", False)

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    verify_live_sync()
