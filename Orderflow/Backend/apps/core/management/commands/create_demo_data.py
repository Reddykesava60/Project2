"""
Management command to create demo data for DineFlow2.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.restaurants.models import Restaurant, Staff
from apps.menu.models import MenuCategory, MenuItem

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates demo data for testing the application'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')

        # Create demo owner
        owner, created = User.objects.get_or_create(
            email='owner@restaurant.com',
            defaults={
                'first_name': 'Restaurant',
                'last_name': 'Owner',
                'role': 'OWNER',
                'is_active': True,
            }
        )
        if created:
            owner.set_password('owner123')
            owner.save()
            self.stdout.write(self.style.SUCCESS(f'Created owner: {owner.email}'))
        else:
            self.stdout.write(f'Owner already exists: {owner.email}')

        # Create demo restaurant
        restaurant, created = Restaurant.objects.get_or_create(
            owner=owner,
            defaults={
                'name': 'Demo Restaurant',
                'slug': 'demo-restaurant',
                'description': 'A demo restaurant for testing',
                'address': '123 Main Street, Mumbai',
                'phone': '+91 9876543210',
                'email': 'demo@restaurant.com',
                'status': 'ACTIVE',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created restaurant: {restaurant.name}'))
        else:
            self.stdout.write(f'Restaurant already exists: {restaurant.name}')

        # Create demo staff
        staff, created = User.objects.get_or_create(
            email='staff@restaurant.com',
            defaults={
                'first_name': 'Staff',
                'last_name': 'Member',
                'role': 'STAFF',
                'is_active': True,
            }
        )
        if created:
            staff.set_password('staff123')
            staff.save()
            self.stdout.write(self.style.SUCCESS(f'Created staff: {staff.email}'))
        else:
            self.stdout.write(f'Staff already exists: {staff.email}')

        # Create staff profile linking staff user to restaurant
        from apps.restaurants.models import Staff as StaffProfile
        staff_profile, created = StaffProfile.objects.get_or_create(
            user=staff,
            defaults={
                'restaurant': restaurant,
                'is_active': True,
                'position': 'Server',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created staff profile for: {staff.email}'))

        # Create menu categories
        categories_data = [
            ('Starters', 'Delicious appetizers to begin your meal', 1),
            ('Main Course', 'Hearty main dishes', 2),
            ('Beverages', 'Refreshing drinks', 3),
            ('Desserts', 'Sweet endings', 4),
        ]

        categories = {}
        for name, description, order in categories_data:
            category, created = MenuCategory.objects.get_or_create(
                restaurant=restaurant,
                name=name,
                defaults={
                    'description': description,
                    'display_order': order,
                    'is_active': True,
                }
            )
            categories[name] = category
            if created:
                self.stdout.write(f'Created category: {name}')

        # Create menu items
        menu_items_data = [
            # Starters
            ('Starters', 'Paneer Tikka', 'Marinated cottage cheese grilled to perfection', 249.00, True, False),
            ('Starters', 'Veg Spring Rolls', 'Crispy rolls stuffed with vegetables', 199.00, True, True),
            ('Starters', 'Chicken Wings', 'Spicy crispy chicken wings', 299.00, False, False),
            ('Starters', 'Mushroom Manchurian', 'Indo-Chinese style mushroom balls', 229.00, True, True),
            # Main Course
            ('Main Course', 'Butter Chicken', 'Creamy tomato-based chicken curry', 399.00, False, False),
            ('Main Course', 'Dal Makhani', 'Rich and creamy black lentils', 249.00, True, False),
            ('Main Course', 'Veg Biryani', 'Fragrant basmati rice with vegetables', 299.00, True, True),
            ('Main Course', 'Paneer Butter Masala', 'Cottage cheese in rich tomato gravy', 329.00, True, False),
            ('Main Course', 'Chicken Biryani', 'Aromatic rice with tender chicken', 349.00, False, False),
            # Beverages
            ('Beverages', 'Fresh Lime Soda', 'Refreshing lime drink', 79.00, True, True),
            ('Beverages', 'Mango Lassi', 'Sweet mango yogurt drink', 129.00, True, False),
            ('Beverages', 'Masala Chai', 'Traditional Indian spiced tea', 49.00, True, False),
            ('Beverages', 'Cold Coffee', 'Chilled coffee with ice cream', 149.00, True, False),
            # Desserts
            ('Desserts', 'Gulab Jamun', 'Deep-fried milk dumplings in syrup', 129.00, True, False),
            ('Desserts', 'Ice Cream Sundae', 'Vanilla ice cream with toppings', 179.00, True, False),
            ('Desserts', 'Chocolate Brownie', 'Warm brownie with ice cream', 199.00, True, False),
        ]

        for cat_name, name, description, price, is_veg, is_vegan in menu_items_data:
            item, created = MenuItem.objects.get_or_create(
                restaurant=restaurant,
                category=categories[cat_name],
                name=name,
                defaults={
                    'description': description,
                    'price': price,
                    'is_vegetarian': is_veg,
                    'is_vegan': is_vegan,
                    'is_available': True,
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'Created menu item: {name}')

        self.stdout.write(self.style.SUCCESS('\nDemo data created successfully!'))
        self.stdout.write('\n--- Demo Credentials ---')
        self.stdout.write('Admin: admin@dineflow.com / admin123')
        self.stdout.write('Owner: owner@restaurant.com / owner123')
        self.stdout.write('Staff: staff@restaurant.com / staff123')
