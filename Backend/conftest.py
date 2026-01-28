"""
Pytest configuration and fixtures for DineFlow2 tests.
"""
import pytest
from django.conf import settings
from rest_framework.test import APIClient
from apps.users.models import User
from apps.restaurants.models import Restaurant, Staff
from apps.menu.models import MenuCategory, MenuItem
from apps.orders.models import Order


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Platform admin user."""
    return User.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role='ADMIN',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def owner_user(db):
    """Restaurant owner user."""
    return User.objects.create_user(
        email='owner@test.com',
        password='testpass123',
        first_name='Owner',
        last_name='User',
        role='OWNER'
    )


@pytest.fixture
def staff_user(db):
    """Staff user."""
    return User.objects.create_user(
        email='staff@test.com',
        password='testpass123',
        first_name='Staff',
        last_name='User',
        role='STAFF'
    )


@pytest.fixture
def restaurant(db, owner_user):
    """Test restaurant."""
    return Restaurant.objects.create(
        name='Test Restaurant',
        slug='test-restaurant',
        owner=owner_user,
        currency='INR',
        status='ACTIVE'
    )


@pytest.fixture
def staff_profile(db, staff_user, restaurant):
    """Staff profile linked to restaurant."""
    return Staff.objects.create(
        user=staff_user,
        restaurant=restaurant,
        can_collect_cash=True,
        can_override_orders=False,
        is_active=True
    )


@pytest.fixture
def menu_category(db, restaurant):
    """Test menu category."""
    return MenuCategory.objects.create(
        restaurant=restaurant,
        name='Main Course',
        display_order=1,
        is_active=True
    )


@pytest.fixture
def menu_item(db, restaurant, menu_category):
    """Test menu item."""
    return MenuItem.objects.create(
        restaurant=restaurant,
        category=menu_category,
        name='Test Pizza',
        description='Delicious test pizza',
        price=499.00,
        is_available=True,
        is_active=True
    )


@pytest.fixture
def authenticated_client(api_client, owner_user):
    """API client authenticated as owner."""
    api_client.force_authenticate(user=owner_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """API client authenticated as admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user, staff_profile):
    """API client authenticated as staff."""
    api_client.force_authenticate(user=staff_user)
    return api_client
