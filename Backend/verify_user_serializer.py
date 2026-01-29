import os
import django
import sys
import json

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.restaurants.models import Restaurant, Staff
from apps.users.serializers import UserSerializer

User = get_user_model()

def verify_serializer():
    print("Verifying User Serializer Output...\n")
    
    email = "serializer_test_staff@example.com"
    
    # Cleanup
    User.objects.filter(email=email).delete()
    
    # Create Staff with permission
    user = User.objects.create_user(email=email, password="password123", role='staff', first_name="Staff", last_name="Serializer")
    # Determine owner/rest
    # Ideally should create a restaurant too but let's see if we can just mock the profile
    # Create a restaurant owner first to link
    owner = User.objects.create_user(email="owner_temp@example.com", password="pw", role='restaurant_owner')
    restaurant = Restaurant.objects.create(name="Temp Rest", owner=owner, slug="temp-rest")
    
    staff = Staff.objects.create(user=user, restaurant=restaurant, can_manage_stock=True)
    
    # Serialize
    serializer = UserSerializer(user)
    data = serializer.data
    
    print(json.dumps(data, indent=2))
    
    if 'can_manage_stock' in data:
        print(f"\n[PASS] can_manage_stock found: {data['can_manage_stock']}")
    else:
        print("\n[FAIL] can_manage_stock NOT found in serializer output.")

    # Cleanup
    staff.delete()
    restaurant.delete()
    owner.delete()
    user.delete()

if __name__ == "__main__":
    verify_serializer()
