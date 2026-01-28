import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.users.serializers import UserSerializer

def verify_serializer():
    print("=== SERIALIZER OUTPUT CHECK ===")
    
    owner = User.objects.filter(email='owner@restaurant.com').first()
    if not owner:
        print("❌ No owner found")
        return

    print(f"Owner Role: '{owner.role}'")
    
    serializer = UserSerializer(owner)
    data = serializer.data
    
    print("\nSerialized Data:")
    print(f"  id: {data['id']}")
    print(f"  email: {data['email']}")
    print(f"  role: {data['role']}")
    print(f"  restaurant_id: {data.get('restaurant_id')}")
    print(f"  restaurant_name: {data.get('restaurant_name')}")
    
    if data.get('restaurant_id'):
        print("✅ Restaurant ID present")
    else:
        print("❌ Restaurant ID MISSING!")

if __name__ == '__main__':
    verify_serializer()
