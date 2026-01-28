"""
STAFF ORDERS VISIBILITY FIX - VALIDATION REPORT
================================================

PROBLEM:
Staff dashboard showed ALL orders including completed, cancelled, and old orders.
Staff must ONLY see: pending, preparing, ready

ROOT CAUSE:
The OrderViewSet.get_queryset() method was NOT filtering by status for staff role.
Staff saw all orders in their restaurant instead of only active ones.

FIX APPLIED:
Modified Backend/apps/orders/views.py - get_queryset() method:
- Added status filter for staff role
- Staff now only sees: PENDING, AWAITING_PAYMENT, PREPARING, READY
- COMPLETED, CANCELLED, FAILED orders are excluded

BUSINESS RULE ENFORCED:
Staff can ONLY see:
  ✓ pending
  ✓ awaiting_payment (waiting for customer payment)
  ✓ preparing
  ✓ ready

Staff can NEVER see:
  ✗ completed
  ✗ cancelled
  ✗ failed

VALIDATION:
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Add testserver to allowed hosts
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

django.setup()

from rest_framework.test import APIClient
from apps.users.models import User
from apps.orders.models import Order

def validate_staff_orders_fix():
    """Validate the staff orders visibility fix."""
    
    print("="*70)
    print("STAFF ORDERS VISIBILITY FIX - VALIDATION")
    print("="*70)
    
    # Get users
    staff = User.objects.get(email='staff@restaurant.com')
    owner = User.objects.get(email='owner@restaurant.com')
    restaurant = staff.staff_profile.restaurant
    
    # Database state
    all_orders = Order.objects.filter(restaurant=restaurant)
    active_statuses = ['PENDING', 'AWAITING_PAYMENT', 'PREPARING', 'READY']
    active_orders = all_orders.filter(status__in=active_statuses)
    completed_orders = all_orders.filter(status='COMPLETED')
    cancelled_orders = all_orders.filter(status='CANCELLED')
    
    print(f"\nDATABASE STATE:")
    print(f"  Total orders in restaurant: {all_orders.count()}")
    print(f"  Active orders: {active_orders.count()}")
    print(f"  Completed orders: {completed_orders.count()}")
    print(f"  Cancelled orders: {cancelled_orders.count()}")
    
    # Test Staff API
    print(f"\n{'='*70}")
    print("STAFF API TEST: GET /api/orders/active/")
    print("="*70)
    
    staff_client = APIClient()
    staff_client.force_authenticate(user=staff)
    
    staff_response = staff_client.get('/api/orders/active/')
    staff_orders = staff_response.data if isinstance(staff_response.data, list) else []
    
    print(f"  Status Code: {staff_response.status_code}")
    print(f"  Orders returned: {len(staff_orders)}")
    
    staff_completed = [o for o in staff_orders if o.get('status') in ['completed', 'COMPLETED']]
    staff_cancelled = [o for o in staff_orders if o.get('status') in ['cancelled', 'CANCELLED']]
    
    print(f"\n  Orders by status:")
    status_counts = {}
    for order in staff_orders:
        s = order.get('status', 'unknown')
        status_counts[s] = status_counts.get(s, 0) + 1
    for s, c in status_counts.items():
        print(f"    {s}: {c}")
    
    # Test Owner API
    print(f"\n{'='*70}")
    print("OWNER API TEST: GET /api/orders/")
    print("="*70)
    
    owner_client = APIClient()
    owner_client.force_authenticate(user=owner)
    
    owner_response = owner_client.get('/api/orders/')
    # Handle paginated response
    if isinstance(owner_response.data, dict) and 'results' in owner_response.data:
        owner_orders = owner_response.data['results']
    elif isinstance(owner_response.data, list):
        owner_orders = owner_response.data
    else:
        owner_orders = []
    
    print(f"  Status Code: {owner_response.status_code}")
    print(f"  Orders returned: {len(owner_orders)}")
    
    print(f"\n  Orders by status:")
    owner_status_counts = {}
    for order in owner_orders:
        s = order.get('status', 'unknown')
        owner_status_counts[s] = owner_status_counts.get(s, 0) + 1
    for s, c in owner_status_counts.items():
        print(f"    {s}: {c}")
    
    # Validation
    print(f"\n{'='*70}")
    print("VALIDATION RESULTS")
    print("="*70)
    
    tests_passed = True
    
    # Test 1: Staff sees only active orders
    if len(staff_orders) == active_orders.count():
        print("  ✅ PASS: Staff sees correct number of active orders")
    else:
        print(f"  ❌ FAIL: Staff sees {len(staff_orders)}, expected {active_orders.count()}")
        tests_passed = False
    
    # Test 2: Staff sees no completed orders
    if len(staff_completed) == 0:
        print("  ✅ PASS: Staff sees NO completed orders")
    else:
        print(f"  ❌ FAIL: Staff sees {len(staff_completed)} completed orders")
        tests_passed = False
    
    # Test 3: Staff sees no cancelled orders
    if len(staff_cancelled) == 0:
        print("  ✅ PASS: Staff sees NO cancelled orders")
    else:
        print(f"  ❌ FAIL: Staff sees {len(staff_cancelled)} cancelled orders")
        tests_passed = False
    
    # Test 4: Owner sees all orders
    if len(owner_orders) == all_orders.count():
        print("  ✅ PASS: Owner sees ALL orders (including completed)")
    else:
        print(f"  ❌ FAIL: Owner sees {len(owner_orders)}, expected {all_orders.count()}")
        tests_passed = False
    
    print(f"\n{'='*70}")
    if tests_passed:
        print("✅ ALL TESTS PASSED - Staff orders filtering is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Fix needs review")
    print("="*70)
    
    return tests_passed

if __name__ == '__main__':
    validate_staff_orders_fix()
