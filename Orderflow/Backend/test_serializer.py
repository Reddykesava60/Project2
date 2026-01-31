import os
import sys
import django
from django.conf import settings

# Force stdout flush
sys.stdout.reconfigure(encoding='utf-8')

# Configure settings before setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from rest_framework.renderers import JSONRenderer
from apps.menu.models import MenuItem, MenuCategory
from apps.menu.serializers import MenuCategoryPublicSerializer
from apps.restaurants.models import Restaurant
from apps.users.models import User

# Mock objects (in memory mostly, ensuring we don't break DB if possible, but serializers need models)
# Since we can't easily mock DB in this script without creating records, we'll try to use existing or create dummy if simpler.
# Actually, creating dummy objects is safer for testing.

try:
    # 1. Setup Data
    user, _ = User.objects.get_or_create(email="test_serializer@example.com", defaults={"role": "owner"})
    restaurant, _ = Restaurant.objects.get_or_create(owner=user, name="Serializer Test", slug="serializer-test")
    category, _ = MenuCategory.objects.get_or_create(restaurant=restaurant, name="Test Category")
    
    # 2. Create Items
    # Unlimited Stock
    item_unlimited, _ = MenuItem.objects.get_or_create(
        category=category, restaurant=restaurant, name="Unlimited Item", 
        defaults={"price": 100, "stock_quantity": None, "is_available": True}
    )
    
    # Limited Stock (Available)
    item_limited, _ = MenuItem.objects.get_or_create(
        category=category, restaurant=restaurant, name="Limited Item", 
        defaults={"price": 100, "stock_quantity": 10, "is_available": True}
    )
    
    # Out of Stock (0 available)
    item_out, _ = MenuItem.objects.get_or_create(
        category=category, restaurant=restaurant, name="Out Item", 
        defaults={"price": 100, "stock_quantity": 0, "is_available": True} # is_available=True to test dynamic filter
    )
    
    # Explicitly Unavailable
    item_unavailable, _ = MenuItem.objects.get_or_create(
        category=category, restaurant=restaurant, name="Unavailable Item", 
        defaults={"price": 100, "stock_quantity": 10, "is_available": False}
    )
    
    # 3. Test Serializer
    print("\n--- Testing MenuCategoryPublicSerializer ---")
    serializer = MenuCategoryPublicSerializer(category)
    data = serializer.data
    
    import json
    print(json.dumps(data, indent=2))
    
    items = data['items']
    names = [i['name'] for i in items]
    
    print("\n--- Results ---")
    print(f"Items found: {names}")
    
    if "Unlimited Item" in names:
        u_item = next(i for i in items if i['name'] == "Unlimited Item")
        print(f"Unlimited Item Stock: {u_item['stock_quantity']} (Expected: None)")
    else:
        print("FAIL: Unlimited Item missing")

    if "Limited Item" in names:
        l_item = next(i for i in items if i['name'] == "Limited Item")
        print(f"Limited Item Stock: {l_item['stock_quantity']} (Expected: 10)")
        
    if "Out Item" in names:
        print("FAIL: Out Item should be hidden (0 stock)")
    else:
        print("PASS: Out Item hidden")
        
    if "Unavailable Item" in names:
         print("FAIL: Unavailable Item should be hidden")
    else:
        print("PASS: Unavailable Item hidden")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

