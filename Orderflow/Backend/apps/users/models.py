"""
Custom User model for DineFlow2.
Supports multiple roles: ADMIN, OWNER, STAFF
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from apps.core.models import UUIDModel


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.PLATFORM_ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(UUIDModel, AbstractUser):
    """
    Custom User model with role-based access.
    Uses email as username for authentication.
    """
    
    class Role(models.TextChoices):
        PLATFORM_ADMIN = 'platform_admin', 'Platform Admin'
        RESTAURANT_OWNER = 'restaurant_owner', 'Restaurant Owner'
        STAFF = 'staff', 'Restaurant Staff'
    
    username = None  # Remove username field
    email = models.EmailField('Email Address', unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RESTAURANT_OWNER,
    )
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    
    # Restaurant association (nullable for platform_admin)
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # Staff-specific permissions (also applies to owners)
    can_collect_cash = models.BooleanField(default=False)
    
    # Timestamps
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_platform_admin(self):
        return self.role == self.Role.PLATFORM_ADMIN
    
    @property
    def is_restaurant_owner(self):
        return self.role == self.Role.RESTAURANT_OWNER
    
    @property
    def is_restaurant_staff(self):
        return self.role == self.Role.STAFF


class LoginHistory(models.Model):
    """Track user login history for security auditing."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Login History'
        verbose_name_plural = 'Login Histories'
        ordering = ['-timestamp']
    
    def __str__(self):
        status = 'Success' if self.success else 'Failed'
        return f"{self.user.email} - {status} - {self.timestamp}"
