import os
import sys
import django

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.restaurants.models import Restaurant

def fix_links():
    print("=== FIXING OWNER LINKS ===")
    owners = User.objects.filter(role=User.Role.RESTAURANT_OWNER)
    count = 0
    for o in owners:
        # Find owned restaurant
        rest = Restaurant.objects.filter(owner=o).first()
        if rest:
            if o.restaurant != rest:
                print(f"Linking {o.email} -> {rest.name}")
                o.restaurant = rest
                o.save()
                count += 1
            else:
                print(f"{o.email} is already linked.")
        else:
            print(f"Skipping {o.email} (No restaurant owned)")
    
    print(f"Fixed {count} owners.")

if __name__ == '__main__':
    fix_links()
