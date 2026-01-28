import os
import sys
import django
from django.test import RequestFactory
from django.conf import settings

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.restaurants.models import Restaurant
from apps.restaurants.views import RestaurantViewSet

def verify_fixes():
    print("=== VERIFYING FIXES ===")
    
    # 1. Check for Broken Staff Roles
    broken_staff = User.objects.filter(role='STAFF') # Uppercase
    if broken_staff.exists():
        print(f"❌ FOUND {broken_staff.count()} USERS WITH BROKEN ROLE 'STAFF':")
        for u in broken_staff:
            print(f"  - {u.email}")
            # Optional: Fix them?
            # u.role = 'staff'
            # u.save()
            # print("  FIXED.")
    else:
        print("✅ No broken uppercase 'STAFF' roles found.")

    # 2. Check QR Image Generation
    r = Restaurant.objects.first()
    if not r:
        print("❌ No restaurant found to test QR.")
        return

    print(f"\nTesting QR Image for {r.name} ({r.slug})...")
    factory = RequestFactory()
    request = factory.get(f'/api/restaurants/{r.id}/qr_image/')
    request.user = r.owner
    
    view = RestaurantViewSet.as_view({'get': 'qr_image'})
    response = view(request, pk=r.id)
    
    print(f"Response Status: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type', '')}")
    
    if response.status_code == 200 and response.get('Content-Type') == 'image/png':
        print(f"✅ QR Image Generation SUCCESS. Size: {len(response.content)} bytes")
    else:
        print(f"❌ QR Generation FAILED.")

if __name__ == '__main__':
    verify_fixes()
