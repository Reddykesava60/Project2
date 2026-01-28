"""
Script to fix incorrect role values in the database.
Migrates: ADMIN -> platform_admin, OWNER -> restaurant_owner, STAFF -> staff
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def fix_roles():
    print("Fixing user roles in database...")
    
    # Mapping of old (incorrect) to new (correct) role values
    role_mapping = {
        'ADMIN': 'platform_admin',
        'OWNER': 'restaurant_owner',
        'STAFF': 'staff',
        # Also handle any that might already be correct but in wrong case
        'admin': 'platform_admin',
        'owner': 'restaurant_owner',
        'staff': 'staff',
        # Handle the full form that might exist
        'platform_admin': 'platform_admin',  # Keep as is
        'restaurant_owner': 'restaurant_owner',  # Keep as is
    }
    
    users = User.objects.all()
    fixed_count = 0
    
    for user in users:
        old_role = user.role
        new_role = role_mapping.get(old_role)
        
        if new_role and new_role != old_role:
            print(f"Fixing {user.email}: {old_role} -> {new_role}")
            user.role = new_role
            user.save(update_fields=['role'])
            fixed_count += 1
        elif new_role is None:
            print(f"WARNING: Unknown role for {user.email}: {old_role}")
        else:
            print(f"OK: {user.email} already has correct role: {old_role}")
    
    print(f"\nFixed {fixed_count} user(s)")
    print("\nCurrent user roles:")
    for user in User.objects.all():
        print(f"  {user.email}: {user.role}")

if __name__ == '__main__':
    fix_roles()
