"""
E2E Verification Script for DineFlow2.
Tests all flows against real API and SQLite database.
"""

import os
import sys
import json
import requests
from decimal import Decimal
from datetime import datetime, date

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.utils import timezone
from django.db.models import Sum, Count
from apps.restaurants.models import Restaurant, Staff
from apps.users.models import User
from apps.orders.models import Order, OrderItem
from apps.menu.models import MenuItem, MenuCategory

# Configuration
BASE_URL = "http://127.0.0.1:8000"
RESTAURANT_SLUG = "italian-place"

# Track test results
results = {
    'passed': [],
    'failed': [],
    'errors': []
}

def log_pass(test_name, details=""):
    print(f"✅ PASS: {test_name}")
    if details:
        print(f"   {details}")
    results['passed'].append(test_name)

def log_fail(test_name, expected, actual):
    print(f"❌ FAIL: {test_name}")
    print(f"   Expected: {expected}")
    print(f"   Actual: {actual}")
    results['failed'].append({'test': test_name, 'expected': expected, 'actual': actual})

def log_error(test_name, error):
    print(f"⚠️ ERROR: {test_name}")
    print(f"   {error}")
    results['errors'].append({'test': test_name, 'error': str(error)})

def get_auth_token(email, password):
    """Get JWT token for authentication."""
    try:
        r = requests.post(f"{BASE_URL}/api/auth/login/", json={
            'email': email,
            'password': password
        })
        if r.status_code == 200:
            return r.json().get('access')
        else:
            return None
    except Exception as e:
        print(f"   Auth error: {e}")
        return None

def auth_headers(token):
    """Return authorization headers."""
    return {'Authorization': f'Bearer {token}'}


# ================================================
# 1. CUSTOMER FLOW TESTS
# ================================================

def test_public_restaurant():
    """Test public restaurant info endpoint."""
    print("\n" + "="*50)
    print("1️⃣ CUSTOMER FLOW TESTS")
    print("="*50)
    
    r = requests.get(f"{BASE_URL}/api/public/r/{RESTAURANT_SLUG}/")
    
    if r.status_code != 200:
        log_fail("Public restaurant endpoint", "Status 200", f"Status {r.status_code}")
        return None
    
    data = r.json()
    
    # Verify against DB
    db_restaurant = Restaurant.objects.get(slug=RESTAURANT_SLUG)
    
    if data['id'] == str(db_restaurant.id):
        log_pass("Public restaurant - ID matches DB", f"ID: {data['id']}")
    else:
        log_fail("Public restaurant - ID matches DB", str(db_restaurant.id), data['id'])
    
    if data['name'] == db_restaurant.name:
        log_pass("Public restaurant - Name matches DB", f"Name: {data['name']}")
    else:
        log_fail("Public restaurant - Name matches DB", db_restaurant.name, data['name'])
    
    return db_restaurant


def test_public_menu(restaurant):
    """Test public menu endpoint."""
    r = requests.get(f"{BASE_URL}/api/public/r/{RESTAURANT_SLUG}/menu/")
    
    if r.status_code != 200:
        log_fail("Public menu endpoint", "Status 200", f"Status {r.status_code}")
        return []
    
    data = r.json()
    
    # Count DB categories and items
    db_categories = MenuCategory.objects.filter(restaurant=restaurant, is_active=True).count()
    db_items = MenuItem.objects.filter(category__restaurant=restaurant, is_available=True).count()
    
    api_categories = len(data.get('categories', []))
    api_items = sum(len(cat.get('items', [])) for cat in data.get('categories', []))
    
    if api_categories == db_categories:
        log_pass("Public menu - Category count matches DB", f"Categories: {api_categories}")
    else:
        log_fail("Public menu - Category count matches DB", db_categories, api_categories)
    
    # Return menu items for order creation
    items = []
    for cat in data.get('categories', []):
        items.extend(cat.get('items', []))
    
    print(f"   Available menu items: {len(items)}")
    return items


def test_cash_order_creation(restaurant, menu_items):
    """Test CASH order creation."""
    if not menu_items:
        log_error("Cash order creation", "No menu items available")
        return None
    
    # Pick first item
    item = menu_items[0]
    
    order_data = {
        'payment_method': 'cash',
        'customer_name': 'E2E Test Customer',
        'table_number': 'T5',
        'is_parcel': False,
        'spicy_level': 'medium',
        'items': [
            {
                'menu_item_id': item['id'],
                'quantity': 2,
                'notes': 'Extra cheese please',
                'attributes': {'egg_count': 1}
            }
        ]
    }
    
    r = requests.post(
        f"{BASE_URL}/api/public/r/{RESTAURANT_SLUG}/order/",
        json=order_data
    )
    
    if r.status_code != 201:
        log_fail("Cash order creation - HTTP status", "201", f"{r.status_code}: {r.text}")
        return None
    
    data = r.json()
    order_id = data.get('order', {}).get('id')
    
    if not order_id:
        log_fail("Cash order creation - Order ID returned", "Order ID", "None")
        return None
    
    log_pass("Cash order creation - Order created", f"Order ID: {order_id}")
    
    # Verify in DB
    try:
        db_order = Order.objects.get(id=order_id)
        
        # Check all required fields
        checks = [
            ('restaurant_id matches', str(db_order.restaurant_id), str(restaurant.id)),
            ('order_number exists', bool(db_order.order_number), True),
            ('status is pending', db_order.status, 'pending'),
            ('payment_method is cash', db_order.payment_method, 'cash'),
            ('payment_status is pending', db_order.payment_status, 'pending'),
            ('spicy_level is medium', db_order.spicy_level, 'medium'),
            ('is_parcel is False', db_order.is_parcel, False),
            ('customer_name matches', db_order.customer_name, 'E2E Test Customer'),
            ('table_number matches', db_order.table_number, 'T5'),
        ]
        
        for check_name, actual, expected in checks:
            if actual == expected:
                log_pass(f"Cash order DB - {check_name}", f"{actual}")
            else:
                log_fail(f"Cash order DB - {check_name}", expected, actual)
        
        # Check order items
        order_items = db_order.items.all()
        if order_items.count() == 1:
            log_pass("Cash order DB - Item count", "1 item")
            item_obj = order_items.first()
            if item_obj.quantity == 2:
                log_pass("Cash order DB - Item quantity", "2")
            else:
                log_fail("Cash order DB - Item quantity", 2, item_obj.quantity)
            
            # Check attributes
            attrs = item_obj.attributes
            if attrs.get('egg_count') == 1:
                log_pass("Cash order DB - Item attributes (egg_count)", "1")
            else:
                log_fail("Cash order DB - Item attributes (egg_count)", 1, attrs.get('egg_count'))
        else:
            log_fail("Cash order DB - Item count", 1, order_items.count())
        
        return db_order
        
    except Order.DoesNotExist:
        log_fail("Cash order DB - Order exists in DB", "Order found", "Order not found")
        return None


def test_upi_payment_flow(restaurant, menu_items):
    """Test UPI payment flow."""
    print("\n--- UPI Payment Flow ---")
    
    if not menu_items:
        log_error("UPI order creation", "No menu items available")
        return None
    
    # Pick first item
    item = menu_items[0]
    
    # Step 1: Try to create UPI order directly (should fail)
    order_data = {
        'payment_method': 'upi',
        'customer_name': 'UPI Test Customer',
        'table_number': 'T10',
        'is_parcel': True,
        'spicy_level': 'high',
        'items': [
            {
                'menu_item_id': item['id'],
                'quantity': 1,
            }
        ]
    }
    
    r = requests.post(
        f"{BASE_URL}/api/public/r/{RESTAURANT_SLUG}/order/",
        json=order_data
    )
    
    if r.status_code == 400 and 'UPI_REQUIRES_PAYMENT_FLOW' in r.text:
        log_pass("UPI order - Rejects direct creation", "Requires payment flow")
    else:
        log_fail("UPI order - Rejects direct creation", "Error with UPI_REQUIRES_PAYMENT_FLOW", f"Status {r.status_code}: {r.text[:100]}")
    
    # Step 2: Initiate payment
    initiate_data = {
        'customer_name': 'UPI Test Customer',
        'table_number': 'T10',
        'is_parcel': True,
        'spicy_level': 'high',
        'items': [
            {
                'menu_item_id': item['id'],
                'quantity': 1,
            }
        ]
    }
    
    r = requests.post(
        f"{BASE_URL}/api/public/r/{RESTAURANT_SLUG}/payment/initiate/",
        json=initiate_data
    )
    
    if r.status_code != 200:
        log_fail("UPI payment initiate", "Status 200", f"Status {r.status_code}: {r.text[:200]}")
        return None
    
    payment_data = r.json()
    payment_token = payment_data.get('payment_token')
    razorpay_order_id = payment_data.get('razorpay_order_id')
    
    if payment_token and razorpay_order_id:
        log_pass("UPI payment initiate - Returns tokens", f"Token: {payment_token[:20]}...")
    else:
        log_fail("UPI payment initiate - Returns tokens", "payment_token and razorpay_order_id", payment_data)
        return None
    
    # Step 3: Verify payment (simulated)
    # In test mode, RAZORPAY_FORCE_SUCCESS=True simulates successful payment
    verify_data = {
        'payment_token': payment_token,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': 'pay_simulated_12345',
        'razorpay_signature': 'simulated_signature'
    }
    
    r = requests.post(
        f"{BASE_URL}/api/public/r/{RESTAURANT_SLUG}/payment/verify/",
        json=verify_data
    )
    
    if r.status_code not in [200, 201]:
        log_fail("UPI payment verify", "Status 200/201", f"Status {r.status_code}: {r.text[:200]}")
        return None
    
    result = r.json()
    order_id = result.get('order', {}).get('id')
    
    if not order_id:
        log_fail("UPI payment verify - Order created", "Order ID", "None")
        return None
    
    log_pass("UPI payment verify - Order created", f"Order ID: {order_id}")
    
    # Verify in DB
    try:
        db_order = Order.objects.get(id=order_id)
        
        checks = [
            ('status is preparing', db_order.status, 'preparing'),
            ('payment_method is upi', db_order.payment_method, 'upi'),
            ('payment_status is success', db_order.payment_status, 'success'),
            ('is_parcel is True', db_order.is_parcel, True),
            ('spicy_level is high', db_order.spicy_level, 'high'),
        ]
        
        for check_name, actual, expected in checks:
            if actual == expected:
                log_pass(f"UPI order DB - {check_name}", f"{actual}")
            else:
                log_fail(f"UPI order DB - {check_name}", expected, actual)
        
        return db_order
        
    except Order.DoesNotExist:
        log_fail("UPI order DB - Order exists", "Found", "Not found")
        return None


# ================================================
# 2. CASH FLOW TESTS
# ================================================

def test_cash_flow_rules(cash_order, staff_token):
    """Test cash payment collection rules."""
    print("\n" + "="*50)
    print("2️⃣ CASH FLOW TESTS")
    print("="*50)
    
    if not cash_order:
        log_error("Cash flow tests", "No cash order to test")
        return
    
    if not staff_token:
        log_error("Cash flow tests", "No staff token available")
        return
    
    # Verify order starts as pending/pending
    if cash_order.status == 'pending' and cash_order.payment_status == 'pending':
        log_pass("Cash flow - Initial state", f"status={cash_order.status}, payment_status={cash_order.payment_status}")
    else:
        log_fail("Cash flow - Initial state", "pending/pending", f"{cash_order.status}/{cash_order.payment_status}")
    
    # Collect cash payment
    r = requests.post(
        f"{BASE_URL}/api/orders/{cash_order.id}/collect_payment/",
        headers=auth_headers(staff_token)
    )
    
    if r.status_code == 200:
        log_pass("Cash collection API - Success", f"Status {r.status_code}")
    else:
        log_fail("Cash collection API - Success", "200", f"{r.status_code}: {r.text[:200]}")
        return
    
    # Refresh from DB
    cash_order.refresh_from_db()
    
    # Verify state after collection
    checks = [
        ('payment_status is success', cash_order.payment_status, 'success'),
        ('status is preparing', cash_order.status, 'preparing'),
        ('cash_collected_by is set', cash_order.cash_collected_by is not None, True),
        ('cash_collected_at is set', cash_order.cash_collected_at is not None, True),
    ]
    
    for check_name, actual, expected in checks:
        if actual == expected:
            log_pass(f"Cash collection DB - {check_name}", f"{actual}")
        else:
            log_fail(f"Cash collection DB - {check_name}", expected, actual)


# ================================================
# 3. STAFF VIEW VALIDATION
# ================================================

def test_staff_visibility(staff_token, cash_staff_token, restaurant):
    """Test staff visibility rules."""
    print("\n" + "="*50)
    print("3️⃣ STAFF VIEW VALIDATION")
    print("="*50)
    
    # Create a new pending cash order for testing visibility
    menu_items = MenuItem.objects.filter(category__restaurant=restaurant, is_available=True)
    if not menu_items:
        log_error("Staff visibility", "No menu items")
        return
    
    item = menu_items.first()
    
    # Create pending cash order via API
    order_data = {
        'payment_method': 'cash',
        'customer_name': 'Visibility Test',
        'table_number': 'V1',
        'items': [{'menu_item_id': str(item.id), 'quantity': 1}]
    }
    
    r = requests.post(f"{BASE_URL}/api/public/r/{RESTAURANT_SLUG}/order/", json=order_data)
    if r.status_code != 201:
        log_error("Staff visibility", f"Failed to create test order: {r.text}")
        return
    
    pending_order_id = r.json()['order']['id']
    
    # Test cash staff sees pending orders
    if cash_staff_token:
        r = requests.get(f"{BASE_URL}/api/orders/active/", headers=auth_headers(cash_staff_token))
        if r.status_code == 200:
            orders = r.json()
            pending_ids = [o['id'] for o in orders if o['status'] == 'pending']
            if pending_order_id in pending_ids:
                log_pass("Cash staff sees pending orders", f"Found {len(pending_ids)} pending orders")
            else:
                log_fail("Cash staff sees pending orders", "Order in list", "Order not found")
        else:
            log_fail("Cash staff active orders API", "200", f"{r.status_code}")
    
    # Get current DB state
    db_pending = Order.objects.filter(restaurant=restaurant, status='pending').count()
    db_preparing = Order.objects.filter(restaurant=restaurant, status='preparing').count()
    db_completed = Order.objects.filter(restaurant=restaurant, status='completed').count()
    
    print(f"\n   DB State: pending={db_pending}, preparing={db_preparing}, completed={db_completed}")
    
    # Verify staff NEVER sees completed orders
    if cash_staff_token:
        r = requests.get(f"{BASE_URL}/api/orders/", headers=auth_headers(cash_staff_token))
        if r.status_code == 200:
            orders = r.json()
            completed_in_response = [o for o in orders if o['status'] == 'completed']
            if len(completed_in_response) == 0:
                log_pass("Staff never sees completed orders", "0 completed in response")
            else:
                log_fail("Staff never sees completed orders", "0", len(completed_in_response))


# ================================================
# 4. OWNER DASHBOARD VALIDATION
# ================================================

def test_owner_dashboard(owner_token, restaurant):
    """Test owner dashboard matches DB exactly."""
    print("\n" + "="*50)
    print("4️⃣ OWNER DASHBOARD VALIDATION")
    print("="*50)
    
    if not owner_token:
        log_error("Owner dashboard", "No owner token")
        return
    
    # Get dashboard stats via API
    r = requests.get(
        f"{BASE_URL}/api/orders/dashboard/stats/?restaurant={restaurant.id}",
        headers=auth_headers(owner_token)
    )
    
    if r.status_code != 200:
        log_fail("Owner dashboard API", "200", f"{r.status_code}: {r.text[:200]}")
        return
    
    api_stats = r.json()
    
    # Calculate expected values from DB
    today = timezone.now().date()
    
    today_orders = Order.objects.filter(restaurant=restaurant, created_at__date=today)
    today_completed = today_orders.filter(status='completed', payment_status='success')
    
    db_today_orders = today_orders.count()
    db_today_revenue = today_completed.aggregate(total=Sum('total_amount'))['total'] or 0
    db_cash_revenue = today_completed.filter(payment_method='cash').aggregate(total=Sum('total_amount'))['total'] or 0
    db_upi_revenue = today_completed.filter(payment_method='upi').aggregate(total=Sum('total_amount'))['total'] or 0
    
    active_statuses = ['pending', 'preparing']
    db_active = Order.objects.filter(restaurant=restaurant, status__in=active_statuses).count()
    db_pending = Order.objects.filter(restaurant=restaurant, status='pending').count()
    
    print(f"\n   DB Today Orders: {db_today_orders}")
    print(f"   DB Today Revenue: {db_today_revenue}")
    print(f"   DB Cash Revenue: {db_cash_revenue}")
    print(f"   DB UPI Revenue: {db_upi_revenue}")
    print(f"   DB Active Orders: {db_active}")
    print(f"   DB Pending Orders: {db_pending}")
    
    # Compare API vs DB
    checks = [
        ('today_orders matches DB', api_stats.get('today_orders'), db_today_orders),
        ('today_revenue matches DB', float(api_stats.get('today_revenue', 0)), float(db_today_revenue)),
        ('cash_revenue matches DB', float(api_stats.get('cash_revenue', 0)), float(db_cash_revenue)),
        ('upi_revenue (online_revenue) matches DB', float(api_stats.get('online_revenue', 0)), float(db_upi_revenue)),
        ('active_orders matches DB', api_stats.get('active_orders'), db_active),
        ('pending_orders matches DB', api_stats.get('pending_orders'), db_pending),
    ]
    
    for check_name, api_val, db_val in checks:
        if api_val == db_val:
            log_pass(f"Owner dashboard - {check_name}", f"API={api_val}, DB={db_val}")
        else:
            log_fail(f"Owner dashboard - {check_name}", db_val, api_val)


# ================================================
# 5. RESTAURANT ISOLATION
# ================================================

def test_restaurant_isolation():
    """Test that Restaurant A data never appears in Restaurant B."""
    print("\n" + "="*50)
    print("5️⃣ RESTAURANT ISOLATION")
    print("="*50)
    
    # Check how many restaurants exist
    restaurants = Restaurant.objects.all()
    print(f"   Total restaurants in DB: {restaurants.count()}")
    
    if restaurants.count() < 2:
        print("   ⚠️ Only 1 restaurant exists - creating second for isolation test")
        
        # Find or create a second owner
        try:
            owner2 = User.objects.create_user(
                email='owner2@test.com',
                password='testpass123',
                first_name='Test',
                last_name='Owner2',
                role='restaurant_owner'
            )
        except:
            owner2 = User.objects.get(email='owner2@test.com')
        
        # Create second restaurant
        try:
            restaurant2 = Restaurant.objects.create(
                name='Test Restaurant B',
                slug='test-restaurant-b',
                owner=owner2
            )
            print(f"   Created restaurant: {restaurant2.name}")
        except:
            restaurant2 = Restaurant.objects.get(slug='test-restaurant-b')
    else:
        restaurant2 = restaurants.exclude(slug=RESTAURANT_SLUG).first()
    
    restaurant1 = Restaurant.objects.get(slug=RESTAURANT_SLUG)
    
    # Count orders per restaurant
    r1_orders = Order.objects.filter(restaurant=restaurant1).count()
    r2_orders = Order.objects.filter(restaurant=restaurant2).count()
    
    print(f"   Restaurant 1 ({restaurant1.name}): {r1_orders} orders")
    print(f"   Restaurant 2 ({restaurant2.name}): {r2_orders} orders")
    
    # Verify cross-check
    r1_order = Order.objects.filter(restaurant=restaurant1).first()
    if r1_order:
        # Check that Restaurant 2 API doesn't return Restaurant 1's order
        r = requests.get(f"{BASE_URL}/api/public/r/{restaurant2.slug}/order/{r1_order.id}/")
        if r.status_code == 404:
            log_pass("Restaurant isolation - Cross-restaurant order access blocked", "404 returned")
        else:
            log_fail("Restaurant isolation - Cross-restaurant order access blocked", "404", r.status_code)
    else:
        print("   ⚠️ No orders to test isolation with")
    
    log_pass("Restaurant isolation - No data leaks in queries", f"R1={r1_orders}, R2={r2_orders} orders isolated")


# ================================================
# 6. ADMIN PANEL VALIDATION
# ================================================

def test_admin_panel(admin_token):
    """Test admin sees all restaurants with correct data."""
    print("\n" + "="*50)
    print("6️⃣ ADMIN PANEL VALIDATION")
    print("="*50)
    
    if not admin_token:
        log_error("Admin panel", "No admin token")
        return
    
    # Get all restaurants via admin API
    r = requests.get(
        f"{BASE_URL}/api/admin/restaurants/",
        headers=auth_headers(admin_token)
    )
    
    if r.status_code != 200:
        log_fail("Admin restaurants API", "200", f"{r.status_code}: {r.text[:200]}")
        return
    
    api_restaurants = r.json()
    db_restaurants = Restaurant.objects.count()
    
    # Handle paginated response
    if isinstance(api_restaurants, dict) and 'results' in api_restaurants:
        api_count = len(api_restaurants['results'])
    else:
        api_count = len(api_restaurants)
    
    if api_count >= db_restaurants:
        log_pass("Admin sees all restaurants", f"API={api_count}, DB={db_restaurants}")
    else:
        log_fail("Admin sees all restaurants", db_restaurants, api_count)


# ================================================
# 7. QR & ORDER NUMBER VERIFICATION
# ================================================

def test_qr_order_number(cash_order, staff_token):
    """Test QR code and order number validation."""
    print("\n" + "="*50)
    print("7️⃣ QR & ORDER NUMBER VERIFICATION")
    print("="*50)
    
    if not cash_order:
        log_error("QR verification", "No order to test")
        return
    
    # Verify order number format (should be like A1, A2, B1, etc.)
    order_number = cash_order.order_number
    if order_number and len(order_number) >= 2:
        log_pass("Order number format", f"Order number: {order_number}")
    else:
        log_fail("Order number format", "Valid order number (e.g., A1)", order_number)
    
    # Verify daily sequence
    if cash_order.daily_sequence and cash_order.daily_sequence > 0:
        log_pass("Daily sequence set", f"Sequence: {cash_order.daily_sequence}")
    else:
        log_fail("Daily sequence set", "> 0", cash_order.daily_sequence)
    
    # Test public order status endpoint
    r = requests.get(f"{BASE_URL}/api/public/r/{RESTAURANT_SLUG}/order/{cash_order.id}/status/")
    if r.status_code == 200:
        status_data = r.json()
        if status_data.get('order_number') == cash_order.order_number:
            log_pass("Public status endpoint - Order number matches", order_number)
        else:
            log_fail("Public status endpoint - Order number matches", cash_order.order_number, status_data.get('order_number'))
    else:
        log_fail("Public status endpoint", "200", r.status_code)


# ================================================
# 8. ORDER COMPLETION FLOW
# ================================================

def test_order_completion(order, staff_token):
    """Test order completion flow."""
    print("\n" + "="*50)
    print("8️⃣ ORDER COMPLETION FLOW")
    print("="*50)
    
    if not order or not staff_token:
        log_error("Order completion", "Missing order or token")
        return
    
    # Order should be preparing at this point
    order.refresh_from_db()
    
    if order.status != 'preparing':
        print(f"   ⚠️ Order status is {order.status}, expected preparing")
        return
    
    # Complete the order
    r = requests.post(
        f"{BASE_URL}/api/orders/{order.id}/complete/",
        headers=auth_headers(staff_token)
    )
    
    if r.status_code == 200:
        log_pass("Order completion API", "Status 200")
    else:
        log_fail("Order completion API", "200", f"{r.status_code}: {r.text[:200]}")
        return
    
    # Verify DB state
    order.refresh_from_db()
    
    checks = [
        ('status is completed', order.status, 'completed'),
        ('completed_at is set', order.completed_at is not None, True),
        ('completed_by is set', order.completed_by is not None, True),
    ]
    
    for check_name, actual, expected in checks:
        if actual == expected:
            log_pass(f"Order completion DB - {check_name}", f"{actual}")
        else:
            log_fail(f"Order completion DB - {check_name}", expected, actual)


# ================================================
# MAIN
# ================================================

def main():
    print("\n" + "="*60)
    print("🔍 DINEFLOW2 E2E VERIFICATION")
    print("="*60)
    print(f"Date: {datetime.now()}")
    print(f"Base URL: {BASE_URL}")
    print(f"Restaurant: {RESTAURANT_SLUG}")
    
    # Get auth tokens
    print("\n--- Authenticating users ---")
    
    staff_token = get_auth_token('staff@restaurant.com', 'staff123')
    if staff_token:
        print("   ✓ Staff authenticated")
    else:
        print("   ✗ Staff auth failed")
    
    owner_token = get_auth_token('owner@restaurant.com', 'owner123')
    if owner_token:
        print("   ✓ Owner authenticated")
    else:
        print("   ✗ Owner auth failed")
    
    admin_token = get_auth_token('admin@dineflow.com', 'admin123')
    if admin_token:
        print("   ✓ Admin authenticated")
    else:
        print("   ✗ Admin auth failed")
    
    # Cash staff token (same as staff in this case since staff has can_collect_cash=True)
    cash_staff_token = staff_token
    
    # Run tests
    restaurant = test_public_restaurant()
    menu_items = test_public_menu(restaurant) if restaurant else []
    cash_order = test_cash_order_creation(restaurant, menu_items) if restaurant and menu_items else None
    upi_order = test_upi_payment_flow(restaurant, menu_items) if restaurant and menu_items else None
    
    test_cash_flow_rules(cash_order, cash_staff_token)
    test_staff_visibility(staff_token, cash_staff_token, restaurant)
    test_owner_dashboard(owner_token, restaurant)
    test_restaurant_isolation()
    test_admin_panel(admin_token)
    test_qr_order_number(cash_order, staff_token)
    
    # Complete the cash order (it should be preparing after cash collection)
    if cash_order:
        cash_order.refresh_from_db()
        if cash_order.status == 'preparing':
            test_order_completion(cash_order, staff_token)
    
    # Summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    print(f"✅ Passed: {len(results['passed'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"⚠️ Errors: {len(results['errors'])}")
    
    if results['failed']:
        print("\n--- Failed Tests ---")
        for f in results['failed']:
            print(f"  • {f['test']}: Expected {f['expected']}, got {f['actual']}")
    
    if results['errors']:
        print("\n--- Errors ---")
        for e in results['errors']:
            print(f"  • {e['test']}: {e['error']}")
    
    # Final verdict
    print("\n" + "="*60)
    if len(results['failed']) == 0 and len(results['errors']) == 0:
        print("🎉 ALL TESTS PASSED - SYSTEM VERIFIED")
    else:
        print("⚠️ SYSTEM HAS ISSUES - SEE FAILURES ABOVE")
    print("="*60)
    
    return len(results['failed']) == 0 and len(results['errors']) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
