"""
Tests for User model and authentication.
"""
import pytest
from apps.users.models import User


@pytest.mark.unit
class TestUserModel:
    """Test User model functionality."""
    
    def test_create_user(self, db):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='OWNER'
        )
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.role == 'OWNER'
        assert not user.is_superuser
    
    def test_create_superuser(self, db):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        assert user.is_superuser
        assert user.is_staff
        assert user.role == 'ADMIN'
    
    def test_user_string_representation(self, owner_user):
        """Test __str__ method."""
        assert str(owner_user) == 'Owner User (owner@test.com)'
    
    def test_role_properties(self, owner_user, staff_user, admin_user):
        """Test role helper properties."""
        assert owner_user.is_restaurant_owner
        assert not owner_user.is_restaurant_staff
        assert not owner_user.is_platform_admin
        
        assert staff_user.is_restaurant_staff
        assert not staff_user.is_restaurant_owner
        
        assert admin_user.is_platform_admin


@pytest.mark.integration
class TestAuthenticationAPI:
    """Test authentication API endpoints."""
    
    def test_login_success(self, api_client, owner_user):
        """Test successful login."""
        response = api_client.post('/api/auth/token/', {
            'email': 'owner@test.com',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_login_invalid_credentials(self, api_client, owner_user):
        """Test login with wrong password."""
        response = api_client.post('/api/auth/token/', {
            'email': 'owner@test.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401
    
    def test_token_refresh(self, api_client, owner_user):
        """Test refreshing access token."""
        # Get initial tokens
        login_response = api_client.post('/api/auth/token/', {
            'email': 'owner@test.com',
            'password': 'testpass123'
        })
        refresh_token = login_response.data['refresh']
        
        # Refresh token
        response = api_client.post('/api/auth/token/refresh/', {
            'refresh': refresh_token
        })
        assert response.status_code == 200
        assert 'access' in response.data
