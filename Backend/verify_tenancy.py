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

def verify_tenancy():
    print("=== TENANCY VERIFICATION ===")
    
    # 1. Check Restaurants
    restaurants = Restaurant.objects.all()
    print(f"\nFound {restaurants.count()} restaurants:")
    for r in restaurants:
        print(f"  [{r.id}] {r.name} (Slug: {r.slug}) (Owner: {r.owner.email})")
        
        # Check URL validity
        if not r.slug:
            print(f"    ❌ ERROR: Missing slug!")
        else:
            print(f"    ✅ QR URL: /r/{r.slug}")

    # 2. Check Owners
    print("\nChecking Owners:")
    owners = User.objects.filter(role=User.Role.RESTAURANT_OWNER)
    for o in owners:
        owned = r = Restaurant.objects.filter(owner=o).first()
        print(f"  {o.email}: Owns -> {owned.name if owned else 'None'}")
        if not owned:
            print(f"    ❌ ERROR: Owner has no restaurant!")

    # 3. Check Staff
    print("\nChecking Staff:")
    staff_users = User.objects.filter(role=User.Role.STAFF)
    for s in staff_users:
        try:
            profile = s.staff_profile
            print(f"  {s.email}: Linked to -> {profile.restaurant.name}")
        except Staff.DoesNotExist:
            print(f"  {s.email}: ❌ ERROR: No Staff Profile!")
        except Exception as e:
            print(f"  {s.email}: ❌ ERROR: {e}")

    # 4. Check Orders Isolation
    print("\nChecking Order Isolation (Sample):")
    for r in restaurants:
        orders = Order.objects.filter(restaurant=r).count()
        print(f"  {r.name}: {orders} orders")
        
        # Verify owner can see them
        owner_orders = Order.objects.filter(restaurant__owner=r.owner).count()
        if owner_orders != orders:
             print(f"    ❌ Owner Visibility Mismatch: Owner sees {owner_orders}, actual {orders}")
        else:
             print(f"    ✅ Owner sees all {orders} orders")

if __name__ == '__main__':
    verify_tenancy()
