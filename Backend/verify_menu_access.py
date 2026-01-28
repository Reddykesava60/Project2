import os
import sys
import django
from django.test import RequestFactory, Client

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.restaurants.models import Restaurant

def verify_menu():
    print("=== VERIFYING PUBLIC MENU ACCESS ===")
    
    r = Restaurant.objects.first()
    if not r:
        print("❌ No restaurant found!")
        return

    print(f"Testing menu for: {r.name} (ID: {r.id})")
    
    c = Client()
    # Attempt to fetch menu without logging in
    response = c.get(f'/api/restaurants/{r.id}/menu/', HTTP_HOST='localhost')
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS: Menu is accessible publicly.")
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        # Only print first 200 chars of error
        print(f"Error: {response.content.decode()[:200]}")

if __name__ == '__main__':
    verify_menu()
