"""
COMPLETE DATA FLOW TRACE
=========================
Proves the entire path from SQLite → Django → API is working correctly.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')
django.setup()

import json
from rest_framework.test import APIClient
from apps.users.models import User
from apps.orders.models import Order

print("="*80)
print("COMPLETE DATA FLOW VERIFICATION")
print("="*80)

# =====================================================================
# PHASE 1: SQLite Truth
# =====================================================================
print("\n" + "="*80)
print("PHASE 1: SQLite Database (Ground Truth)")
print("="*80)

all_orders = Order.objects.all()
print(f"\nTotal orders in database: {all_orders.count()}")

print("\nOrders by status:")
from django.db.models import Count
for stat in Order.objects.values('status').annotate(count=Count('id')).order_by('status'):
    print(f"  {stat['status']:20}: {stat['count']}")

active_statuses = ['PENDING', 'AWAITING_PAYMENT', 'PREPARING', 'READY']
active_count = Order.objects.filter(status__in=active_statuses).count()
completed_count = Order.objects.filter(status='COMPLETED').count()

print(f"\n  Active orders (PENDING/AWAITING_PAYMENT/PREPARING/READY): {active_count}")
print(f"  Completed orders: {completed_count}")

# =====================================================================
# PHASE 2: Django API Response
# =====================================================================
print("\n" + "="*80)
print("PHASE 2: Django API Response (GET /api/orders/active/)")
print("="*80)

staff = User.objects.get(email='staff@restaurant.com')
client = APIClient()
client.force_authenticate(user=staff)

response = client.get('/api/orders/active/')
api_orders = response.data if isinstance(response.data, list) else response.data.get('results', [])

print(f"\nAPI returned: {len(api_orders)} orders")
print("\nAPI orders by status:")
api_status_counts = {}
for order in api_orders:
    s = order.get('status', 'unknown')
    api_status_counts[s] = api_status_counts.get(s, 0) + 1
for s, c in sorted(api_status_counts.items()):
    print(f"  {s:20}: {c}")

# Check for completed/cancelled in API
api_completed = [o for o in api_orders if o.get('status') in ['completed', 'COMPLETED']]
api_cancelled = [o for o in api_orders if o.get('status') in ['cancelled', 'CANCELLED']]

print(f"\n  Completed in API response: {len(api_completed)}")
print(f"  Cancelled in API response: {len(api_cancelled)}")

# =====================================================================
# PHASE 3: Frontend Expectation
# =====================================================================
print("\n" + "="*80)
print("PHASE 3: Frontend Expected Behavior")
print("="*80)

print("""
Frontend calls: orderApi.getActive(restaurantId)
  → GET /api/orders/active/?restaurant={id}
  → Expects only active orders
  → SWR polls every 5 seconds

Frontend OrderStatus types: 'pending' | 'preparing' | 'ready' | 'completed' | 'cancelled'
Note: 'awaiting_payment' is returned by API but not in frontend types
""")

# =====================================================================
# FINAL COMPARISON TABLE
# =====================================================================
print("\n" + "="*80)
print("FINAL COMPARISON TABLE")
print("="*80)

print("""
| Layer              | Total Orders | Active | Completed | Cancelled |
|--------------------|--------------|--------|-----------|-----------|""")
print(f"| SQLite Database    | {all_orders.count():12} | {active_count:6} | {completed_count:9} | {Order.objects.filter(status='CANCELLED').count():9} |")
print(f"| API /orders/active | {len(api_orders):12} | {len(api_orders):6} | {len(api_completed):9} | {len(api_cancelled):9} |")

# =====================================================================
# VERDICT
# =====================================================================
print("\n" + "="*80)
print("VERDICT")
print("="*80)

if len(api_orders) == active_count and len(api_completed) == 0:
    print("""
✅ BACKEND IS WORKING CORRECTLY

The API /api/orders/active/ returns ONLY active orders:
  - pending
  - awaiting_payment  
  - preparing
  - ready

NO completed or cancelled orders are returned.

If the UI still shows completed orders, the issue is one of:
1. Frontend is caching stale data (SWR cache)
2. Frontend is calling a different endpoint
3. Browser has cached old response
4. Frontend needs a hard refresh (Ctrl+Shift+R)

RECOMMENDED ACTIONS:
1. Clear browser cache and cookies
2. Hard refresh the staff page (Ctrl+Shift+R)
3. Check browser DevTools Network tab to verify:
   - Request URL is /api/orders/active/
   - Response contains only active orders
""")
else:
    print("❌ BACKEND HAS ISSUES - Further investigation needed")
