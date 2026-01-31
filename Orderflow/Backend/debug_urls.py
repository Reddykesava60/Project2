
import os
import sys
import django
from django.conf import settings
from django.urls import resolve
from django.urls.exceptions import Resolver404

# Force stdout flush
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def check_url(url_path):
    print(f"\n--- Checking: {url_path} ---")
    try:
        match = resolve(url_path)
        print(f"[MATCHED]")
        print(f"View Name: {match.view_name}")
        print(f"Callback: {match.func.__name__} (Class: {getattr(match.func, 'cls', 'N/A')})")
        print(f"Args: {match.args}")
        print(f"Kwargs: {match.kwargs}")
    except Resolver404:
        print(f"[FAILED] 404 Not Found")
    except Exception as e:
        print(f"[ERROR] {e}")

# Test with a fake UUID
fake_id = "550e8400-e29b-41d4-a716-446655440000"
check_url(f"/api/restaurants/{fake_id}/menu/")
check_url(f"/api/restaurants/slug/some-slug/")
