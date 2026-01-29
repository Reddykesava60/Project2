
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.request import Request
from apps.users.models import User
from apps.restaurants.models import Restaurant
from apps.menu.models import MenuCategory, MenuItem
from apps.menu.serializers import MenuCategoryPublicSerializer, MenuCategorySerializer
from apps.menu.views import MenuItemViewSet

def verify_compliance():
    print("--- Setting up Test Data ---")
    # 1. Create/Get Owner
    email = "testowner_compliance@example.com"
    owner, _ = User.objects.get_or_create(email=email, defaults={
        'first_name': "Compliance",
        'last_name': "Tester",
        'role': 'restaurant_owner',
        'is_active': True
    })
    
    # 2. Create/Get Restaurant
    restaurant, _ = Restaurant.objects.get_or_create(owner=owner, defaults={
        'name': "Compliance Resto",
        'slug': "compliance-resto",
        'status': 'ACTIVE'
    })

    # 3. Create Category
    category, _ = MenuCategory.objects.get_or_create(
        restaurant=restaurant, 
        name="Compliance Category"
    )
    
    # 4. Create Items with various states
    # A: Active, Available, Stock=10  -> Visible to ALL
    item_a, _ = MenuItem.objects.get_or_create(category=category, restaurant=restaurant, name="Item A", defaults={'price': 10, 'is_active': True, 'is_available': True, 'stock_quantity': 10})
    item_a.stock_quantity = 10; item_a.is_active = True; item_a.is_available = True; item_a.save()
    
    # B: Active, Available, Stock=0   -> Visible to Owner ONLY
    item_b, _ = MenuItem.objects.get_or_create(category=category, restaurant=restaurant, name="Item B", defaults={'price': 10, 'is_active': True, 'is_available': True, 'stock_quantity': 0})
    item_b.stock_quantity = 0; item_b.is_active = True; item_b.is_available = True; item_b.save()
    
    # C: Active, Unavailable          -> Visible to Owner ONLY
    item_c, _ = MenuItem.objects.get_or_create(category=category, restaurant=restaurant, name="Item C", defaults={'price': 10, 'is_active': True, 'is_available': False})
    item_c.is_available = False; item_c.save()
    
    # D: Inactive                     -> Visible to Owner ONLY
    item_d, _ = MenuItem.objects.get_or_create(category=category, restaurant=restaurant, name="Item D", defaults={'price': 10, 'is_active': False})
    item_d.is_active = False; item_d.save()

    print("\n--- Verifying Public View (Customer) ---")
    # Public serializer should ONLY show active_items which are filtered
    # HACK: logic is in to_representation, but it relies on 'items' being pre-filtered usually? 
    # Wait, the serializer method to_representation overrode active_items.
    # Let's inspect the serialization result directly.
    
    # To properly simulate, we need to make sure the serializer has context if needed, but here it doesn't strictly need it for basic method.
    pub_serializer = MenuCategoryPublicSerializer(category)
    data = pub_serializer.data
    public_items = data.get('items', [])
    
    print(f"Public items count: {len(public_items)}")
    visible_names = [i['name'] for i in public_items]
    print(f"Visible items: {visible_names}")
    
    if "Item A" in visible_names and "Item B" not in visible_names and "Item C" not in visible_names and "Item D" not in visible_names:
        print("SUCCESS: Public view correctly hides unavailable/out-of-stock items.")
    else:
        print("FAILURE: Public view leaked items!")
        if "Item B" in visible_names: print(" - Item B (Stock=0) is visible (FAIL)")
        if "Item C" in visible_names: print(" - Item C (Unavailable) is visible (FAIL)")

    print("\n--- Verifying Owner View ---")
    # Owner serializer (MenuCategorySerializer)
    owner_serializer = MenuCategorySerializer(category)
    owner_data = owner_serializer.data
    owner_items = owner_data.get('items', [])
    
    print(f"Owner items count: {len(owner_items)}")
    owner_names = [i['name'] for i in owner_items]
    
    if all(name in owner_names for name in ["Item A", "Item B", "Item C", "Item D"]):
        print("SUCCESS: Owner view sees ALL items.")
    else:
        print("FAILURE: Owner view missing items!")
        print(f"Seen: {owner_names}")

if __name__ == "__main__":
    verify_compliance()
