"""Test staff orders API endpoint."""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Add testserver to allowed hosts before setup
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

django.setup()

from rest_framework.test import APIClient
from apps.users.models import User
from apps.orders.models import Order

# Test /orders/active/ endpoint as staff
client = APIClient()
staff = User.objects.get(email='staff@restaurant.com')
client.force_authenticate(user=staff)

print("="*60)
print("TESTING /api/orders/active/ AS STAFF")
print("="*60)

response = client.get('/api/orders/active/')
print(f"Status Code: {response.status_code}")
print(f"Order Count: {len(response.data) if isinstance(response.data, list) else 'Not a list'}")

if isinstance(response.data, list):
    print("\nOrders returned:")
    for order in response.data:
        status = order.get('status', 'unknown')
        customer = order.get('customer_name', 'unknown')
        print(f"  - Status: {status}, Customer: {customer}")
    
    # Check for bad statuses
    completed = [o for o in response.data if o.get('status') == 'COMPLETED']
    cancelled = [o for o in response.data if o.get('status') == 'CANCELLED']
    
    print(f"\n❌ COMPLETED orders returned: {len(completed)}")
    print(f"❌ CANCELLED orders returned: {len(cancelled)}")
    
    if completed or cancelled:
        print("\n🚨 BUG CONFIRMED: Staff sees completed/cancelled orders!")
    else:
        print("\n✅ CORRECT: Staff only sees active orders")

print("\n" + "="*60)
print("TESTING /api/orders/ (base list) AS STAFF")
print("="*60)

response2 = client.get('/api/orders/')
print(f"Status Code: {response2.status_code}")
if hasattr(response2, 'data'):
    data2 = response2.data
    if isinstance(data2, list):
        print(f"Order Count: {len(data2)}")
        for order in data2:
            status = order.get('status', 'unknown')
            customer = order.get('customer_name', 'unknown')
            print(f"  - Status: {status}, Customer: {customer}")
    elif isinstance(data2, dict) and 'results' in data2:
        print(f"Order Count: {len(data2['results'])}")
        for order in data2['results']:
            status = order.get('status', 'unknown')
            customer = order.get('customer_name', 'unknown')
            print(f"  - Status: {status}, Customer: {customer}")

print("\n" + "="*60)
print("COMPARING WITH DATABASE DIRECTLY")
print("="*60)

# Direct DB query
active_statuses = ['PENDING', 'AWAITING_PAYMENT', 'PREPARING', 'READY']
staff_profile = staff.staff_profile
all_orders = Order.objects.filter(restaurant=staff_profile.restaurant)
active_orders = all_orders.filter(status__in=active_statuses)

print(f"Total orders in restaurant: {all_orders.count()}")
print(f"Active orders in restaurant: {active_orders.count()}")
print(f"API returned: {len(response.data) if isinstance(response.data, list) else 'N/A'}")
