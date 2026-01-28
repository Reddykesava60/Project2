"""
PHASE 2: Complete API Trace
===========================
Test the exact endpoint the frontend calls and log everything.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')
django.setup()

from rest_framework.test import APIClient
from apps.users.models import User
from apps.orders.models import Order
from django.db import connection
from django.test.utils import CaptureQueriesContext
import json

print("="*70)
print("PHASE 2: COMPLETE API TRACE")
print("="*70)

# Get staff user
staff = User.objects.get(email='staff@restaurant.com')
restaurant_id = str(staff.staff_profile.restaurant_id)

print(f"\nStaff User: {staff.email}")
print(f"Staff Role: {staff.role}")
print(f"Restaurant ID: {restaurant_id}")

# Create client
client = APIClient()
client.force_authenticate(user=staff)

print("\n" + "="*70)
print("CALLING: GET /api/orders/active/?restaurant=" + restaurant_id)
print("="*70)

# Capture SQL queries
with CaptureQueriesContext(connection) as context:
    response = client.get('/api/orders/active/', {'restaurant': restaurant_id})

print(f"\nHTTP Status: {response.status_code}")

# Show SQL queries executed
print("\n" + "-"*70)
print("SQL QUERIES EXECUTED:")
print("-"*70)
for i, query in enumerate(context.captured_queries):
    sql = query['sql']
    # Only show order-related queries
    if 'orders_order' in sql.lower():
        print(f"\nQuery {i+1}:")
        print(sql[:500] + "..." if len(sql) > 500 else sql)

# Show response data
print("\n" + "-"*70)
print("API RESPONSE:")
print("-"*70)

if isinstance(response.data, list):
    print(f"Total orders returned: {len(response.data)}")
    print("\nOrders in response:")
    for order in response.data:
        print(f"  ID: {order.get('id', 'N/A')[:8]}... | Status: {order.get('status', 'N/A'):20} | Customer: {order.get('customer_name', 'N/A')}")
    
    # Check for completed orders
    completed = [o for o in response.data if o.get('status') in ['completed', 'COMPLETED']]
    cancelled = [o for o in response.data if o.get('status') in ['cancelled', 'CANCELLED']]
    
    print(f"\n⚠️  COMPLETED orders in response: {len(completed)}")
    print(f"⚠️  CANCELLED orders in response: {len(cancelled)}")
else:
    print(f"Response type: {type(response.data)}")
    print(json.dumps(response.data, indent=2, default=str)[:1000])

# Compare with direct database query
print("\n" + "="*70)
print("PHASE 1 vs PHASE 2 COMPARISON")
print("="*70)

# Direct DB query matching what get_queryset should return
active_statuses = ['PENDING', 'AWAITING_PAYMENT', 'PREPARING', 'READY']
db_active = Order.objects.filter(
    restaurant=staff.staff_profile.restaurant,
    status__in=active_statuses
)
db_all = Order.objects.filter(restaurant=staff.staff_profile.restaurant)

print(f"\nDirect DB (all orders): {db_all.count()}")
print(f"Direct DB (active only): {db_active.count()}")
print(f"API Response count: {len(response.data) if isinstance(response.data, list) else 'N/A'}")

# Final verdict
print("\n" + "="*70)
print("VERDICT")
print("="*70)

if isinstance(response.data, list):
    api_count = len(response.data)
    if api_count == db_active.count():
        print("✅ API returns ONLY active orders (matches DB filter)")
    elif api_count == db_all.count():
        print("❌ API returns ALL orders (filtering not working)")
    else:
        print(f"⚠️  Mismatch: API={api_count}, DB Active={db_active.count()}, DB All={db_all.count()}")
    
    if len(completed) > 0:
        print("❌ COMPLETED orders are leaking through!")
    else:
        print("✅ No COMPLETED orders in response")
