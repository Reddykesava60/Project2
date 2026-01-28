import os
import sys
import django
from django.test import Client

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.restaurants.models import Restaurant

def verify_access():
    print("=== VERIFYING PUBLIC ACCESS ===")
    
    r = Restaurant.objects.first()
    if not r:
        print("❌ No restaurant found!")
        return

    print(f"Restaurant: {r.name}")
    print(f"  ID: {r.id}")
    print(f"  Slug: {r.slug}")
    print(f"  Status: {r.status}")

    c = Client()
    
    # 1. Test Slug Access (Customer View)
    slug_url = f'/api/restaurants/slug/{r.slug}/'
    print(f"\nTesting Slug URL: {slug_url}")
    resp_slug = c.get(slug_url, HTTP_HOST='localhost')
    if resp_slug.status_code == 200:
        print("✅ Slug Access: SUCCESS")
    else:
        print(f"❌ Slug Access: FAILED ({resp_slug.status_code})")
        print(f"Error: {resp_slug.content.decode()[:200]}")

    # 2. Test ID Access (Owner View - Frontend Bug Workaround)
    id_url = f'/api/restaurants/slug/{r.id}/'
    print(f"\nTesting ID URL on Endpoint: {id_url}")
    resp_id = c.get(id_url, HTTP_HOST='localhost')
    if resp_id.status_code == 200:
        print("✅ ID Access (Workaround): SUCCESS")
    else:
        print(f"❌ ID Access (Workaround): FAILED ({resp_id.status_code})")
        # Expected to fail initially

if __name__ == '__main__':
    verify_access()
