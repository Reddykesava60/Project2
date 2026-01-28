
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.restaurants.models import Restaurant, Staff
from apps.menu.models import MenuCategory, MenuItem

User = get_user_model()

def seed():
    print("Seeding data...")

    # 1. Create Superuser
    if not User.objects.filter(email='admin@dineflow.com').exists():
        User.objects.create_superuser(
            email='admin@dineflow.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        print("Created Admin: admin@dineflow.com")
    
    # 2. Create Owner
    if not User.objects.filter(email='owner@restaurant.com').exists():
        owner = User.objects.create_user(
            email='owner@restaurant.com',
            password='owner123',
            first_name='Luigi',
            last_name='Mario',
            role=User.Role.RESTAURANT_OWNER
        )
        print("Created Owner: owner@restaurant.com")
    else:
        owner = User.objects.get(email='owner@restaurant.com')

    # 3. Create Restaurant
    restaurant, created = Restaurant.objects.get_or_create(
        slug='italian-place',
        defaults={
            'name': 'The Italian Place',
            'owner': owner,
            'currency': 'INR',
            'status': Restaurant.Status.ACTIVE
        }
    )
    if created:
        print("Created Restaurant: The Italian Place")
        # Link owner to restaurant
        owner.restaurant = restaurant
        owner.save()
    else:
        print("Restaurant already exists")

    # 4. Create Staff
    if not User.objects.filter(email='staff@restaurant.com').exists():
        staff_user = User.objects.create_user(
            email='staff@restaurant.com',
            password='staff123',
            first_name='Mario',
            last_name='Bros',
            role=User.Role.STAFF,
            restaurant=restaurant  # Link staff user to restaurant
        )
        Staff.objects.create(
            user=staff_user,
            restaurant=restaurant,
            can_collect_cash=True,
            can_override_orders=False
        )
        print("Created Staff: staff@restaurant.com")
    else:
        # Ensure existing staff user has restaurant linked
        staff_user = User.objects.get(email='staff@restaurant.com')
        if not staff_user.restaurant:
            staff_user.restaurant = restaurant
            staff_user.save()
            print("Fixed Staff restaurant link")
    
    # 5. Create Menu
    cat_pizza, _ = MenuCategory.objects.get_or_create(
        restaurant=restaurant,
        name='Pizzas',
        defaults={'display_order': 1}
    )
    
    if not cat_pizza.items.exists():
        MenuItem.objects.create(
            category=cat_pizza,
            restaurant=restaurant,
            name='Margherita',
            description='Tomato, Mozzarella, Basil',
            price=350.00,
            is_vegetarian=True
        )
        MenuItem.objects.create(
            category=cat_pizza,
            restaurant=restaurant,
            name='Pepperoni',
            description='Spicy Pepperoni, Mozzarella',
            price=450.00
        )
        print("Created Menu Items for Pizzas")

    cat_pastas, _ = MenuCategory.objects.get_or_create(
        restaurant=restaurant,
        name='Pastas',
        defaults={'display_order': 2}
    )
    
    if not cat_pastas.items.exists():
        MenuItem.objects.create(
            category=cat_pastas,
            restaurant=restaurant,
            name='Arrabbiata',
            description='Spicy Tomato Sauce, Penne',
            price=300.00,
            is_vegetarian=True,
            is_vegan=True
        )
        print("Created Menu Items for Pastas")

    print("Seeding Complete!")

if __name__ == '__main__':
    seed()
