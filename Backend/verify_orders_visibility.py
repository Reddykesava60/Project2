import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.restaurants.models import Restaurant, Staff
from apps.orders.models import Order

def verify_visibility():
    print("=== ORDER VISIBILITY CHECK ===")
    
    # Get test users
    owner = User.objects.filter(role='restaurant_owner', email='owner@restaurant.com').first()
    staff = User.objects.filter(role='staff', email='staff@restaurant.com').first()
    
    if not owner or not staff:
        print("❌ Missing seeded users (owner/staff)")
        return

    # Get Staff Profile
    try:
        staff_profile = staff.staff_profile
        staff_restaurant = staff_profile.restaurant
    except Exception as e:
        print(f"❌ Staff profile error: {e}")
        return

    # Get Owner Restaurant
    owner_restaurant = Restaurant.objects.filter(owner=owner).first()

    print(f"Owner: {owner.email} -> Restaurant: {owner_restaurant.name}")
    print(f"Staff: {staff.email} -> Restaurant: {staff_restaurant.name}")

    if owner_restaurant != staff_restaurant:
        print("❌ CRITICAL: Owner and Staff serve different restaurants!")
        return

    # Simulate Owner Query
    # OrderViewSet: Order.objects.filter(restaurant__owner=user)
    owner_orders = list(Order.objects.filter(restaurant__owner=owner).values_list('id', flat=True))
    print(f"\nOwner sees {len(owner_orders)} orders.")

    # Simulate Staff Query
    # OrderViewSet: Order.objects.filter(restaurant=staff_profile.restaurant)
    staff_orders = list(Order.objects.filter(restaurant=staff_profile.restaurant).values_list('id', flat=True))
    print(f"Staff sees {len(staff_orders)} orders.")

    # Compare
    owner_set = set(owner_orders)
    staff_set = set(staff_orders)
    
    if owner_set == staff_set:
        print("✅ SUCCESS: Order Visibility is IDENTICAL.")
    else:
        print(f"❌ MISMATCH: Owner has {len(owner_set)}, Staff has {len(staff_set)}")
        diff = owner_set.symmetric_difference(staff_set)
        print(f"Diff IDs: {diff}")

if __name__ == '__main__':
    verify_visibility()
