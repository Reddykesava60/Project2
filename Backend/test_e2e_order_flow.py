"""
END-TO-END TEST: Order Completion Flow
======================================
1. Create 2 orders
2. Staff sees 2 orders
3. Complete 1 order
4. Staff must now see only 1
5. Owner must see 1 pending + 1 completed
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')
django.setup()

from rest_framework.test import APIClient
from apps.users.models import User
from apps.orders.models import Order
from apps.restaurants.models import Restaurant
from apps.menu.models import MenuItem

def test_order_completion_flow():
    print("="*70)
    print("END-TO-END TEST: Order Completion Flow")
    print("="*70)
    
    # Setup
    staff = User.objects.get(email='staff@restaurant.com')
    owner = User.objects.get(email='owner@restaurant.com')
    restaurant = staff.staff_profile.restaurant
    
    # Get a menu item
    product = MenuItem.objects.filter(category__restaurant=restaurant).first()
    if not product:
        print("❌ No products found, cannot test")
        return
    
    staff_client = APIClient()
    staff_client.force_authenticate(user=staff)
    
    owner_client = APIClient()
    owner_client.force_authenticate(user=owner)
    
    # Count existing orders
    initial_staff_count = len(staff_client.get('/api/orders/active/').data)
    print(f"\n1. Initial staff orders: {initial_staff_count}")
    
    # Create 2 new orders
    print("\n2. Creating 2 test orders...")
    order1_resp = staff_client.post('/api/orders/staff/create/', {
        'restaurant': str(restaurant.id),
        'customer_name': 'E2E Test Customer 1',
        'items': [{'menu_item_id': str(product.id), 'quantity': 1}]
    }, format='json')
    
    order2_resp = staff_client.post('/api/orders/staff/create/', {
        'restaurant': str(restaurant.id),
        'customer_name': 'E2E Test Customer 2',
        'items': [{'menu_item_id': str(product.id), 'quantity': 1}]
    }, format='json')
    
    if order1_resp.status_code not in [200, 201] or order2_resp.status_code not in [200, 201]:
        print(f"❌ Failed to create orders: {order1_resp.status_code}, {order2_resp.status_code}")
        print(f"   Order 1 error: {order1_resp.data}")
        print(f"   Order 2 error: {order2_resp.data}")
        return
    
    order1_id = order1_resp.data.get('id')
    order2_id = order2_resp.data.get('id')
    print(f"   Created order 1: {order1_id}")
    print(f"   Created order 2: {order2_id}")
    
    # Check staff sees both
    staff_orders = staff_client.get('/api/orders/active/').data
    print(f"\n3. Staff now sees: {len(staff_orders)} orders")
    
    new_order_ids = {order1_id, order2_id}
    staff_sees_both = sum(1 for o in staff_orders if o['id'] in new_order_ids) == 2
    print(f"   Staff sees both new orders: {'✅' if staff_sees_both else '❌'}")
    
    # Complete order 1
    print(f"\n4. Completing order 1...")
    complete_resp = staff_client.post(f'/api/orders/{order1_id}/update_status/', {
        'status': 'COMPLETED'
    }, format='json')
    
    if complete_resp.status_code == 200:
        print("   ✅ Order 1 marked as COMPLETED")
    else:
        print(f"   ❌ Failed: {complete_resp.status_code} - {complete_resp.data}")
    
    # Check staff now sees only 1 new order
    staff_orders_after = staff_client.get('/api/orders/active/').data
    new_orders_visible = [o for o in staff_orders_after if o['id'] in new_order_ids]
    
    print(f"\n5. AFTER COMPLETION:")
    print(f"   Staff sees: {len(staff_orders_after)} total orders")
    print(f"   Staff sees new orders: {len(new_orders_visible)}")
    
    # Check if completed order is hidden
    completed_hidden = not any(o['id'] == order1_id for o in staff_orders_after)
    pending_visible = any(o['id'] == order2_id for o in staff_orders_after)
    
    print(f"\n   Completed order hidden from staff: {'✅' if completed_hidden else '❌'}")
    print(f"   Pending order visible to staff: {'✅' if pending_visible else '❌'}")
    
    # Check owner sees both
    owner_resp = owner_client.get('/api/orders/')
    owner_orders = owner_resp.data.get('results', []) if isinstance(owner_resp.data, dict) else owner_resp.data
    owner_new_orders = [o for o in owner_orders if o['id'] in new_order_ids]
    
    print(f"\n6. Owner sees: {len(owner_orders)} total orders")
    print(f"   Owner sees new orders: {len(owner_new_orders)}")
    
    owner_completed = [o for o in owner_new_orders if o['status'] == 'completed']
    owner_active = [o for o in owner_new_orders if o['status'] != 'completed']
    
    print(f"   Owner completed: {len(owner_completed)}")
    print(f"   Owner active: {len(owner_active)}")
    
    # Final validation
    print(f"\n{'='*70}")
    print("VALIDATION RESULTS")
    print("="*70)
    
    all_pass = True
    
    if completed_hidden:
        print("  ✅ PASS: Completed order immediately hidden from Staff")
    else:
        print("  ❌ FAIL: Completed order still visible to Staff")
        all_pass = False
    
    if pending_visible:
        print("  ✅ PASS: Pending order still visible to Staff")
    else:
        print("  ❌ FAIL: Pending order not visible to Staff")
        all_pass = False
    
    if len(owner_new_orders) == 2:
        print("  ✅ PASS: Owner sees both orders (completed + pending)")
    else:
        print(f"  ❌ FAIL: Owner sees {len(owner_new_orders)} instead of 2")
        all_pass = False
    
    if len(owner_completed) == 1:
        print("  ✅ PASS: Owner sees 1 completed order")
    else:
        print(f"  ❌ FAIL: Owner sees {len(owner_completed)} completed orders")
        all_pass = False
    
    # Cleanup - delete test orders
    print("\n7. Cleaning up test orders...")
    Order.objects.filter(id__in=[order1_id, order2_id]).delete()
    print("   Test orders deleted")
    
    print(f"\n{'='*70}")
    if all_pass:
        print("✅ ALL E2E TESTS PASSED!")
    else:
        print("❌ SOME E2E TESTS FAILED")
    print("="*70)

if __name__ == '__main__':
    test_order_completion_flow()
