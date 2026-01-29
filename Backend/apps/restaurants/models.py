"""
Restaurant and Staff models for DineFlow2.
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify
from apps.core.models import BaseModel


class Restaurant(BaseModel):
    """
    Restaurant model - the core tenant entity.
    Each restaurant belongs to one owner and can have multiple staff.
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        SUSPENDED = 'SUSPENDED', 'Suspended'
    
    class SubscriptionTier(models.TextChoices):
        FREE = 'FREE', 'Free'
        BASIC = 'BASIC', 'Basic'
        PREMIUM = 'PREMIUM', 'Premium'
        ENTERPRISE = 'ENTERPRISE', 'Enterprise'
    
    # Basic Info
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='restaurants/logos/', blank=True, null=True)
    
    # Owner relationship
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_restaurants'
    )
    
    # Status & Subscription
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    subscription_tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE
    )
    subscription_active = models.BooleanField(default=True)
    
    # Settings
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    currency = models.CharField(max_length=3, default='INR')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.08)
    
    # QR Settings
    qr_version = models.PositiveIntegerField(default=1)
    qr_secret = models.CharField(max_length=64, blank=True)  # HMAC secret for QR verification
    
    # Contact Info
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Restaurant'
        verbose_name_plural = 'Restaurants'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure unique slug
            original_slug = self.slug
            counter = 1
            while Restaurant.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        # Generate QR secret if not set
        if not self.qr_secret:
            import secrets
            self.qr_secret = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def increment_qr_version(self):
        """Increment QR version to invalidate old QR codes."""
        self.qr_version += 1
        self.save(update_fields=['qr_version', 'updated_at'])
    
    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE and self.subscription_active


class Staff(BaseModel):
    """
    Staff model - employees of a restaurant.
    Links a user to a restaurant with specific permissions.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='staff_members'
    )
    
    # Permissions
    can_collect_cash = models.BooleanField(default=False)
    can_override_orders = models.BooleanField(default=False)
    can_manage_stock = models.BooleanField(
        default=False,
        help_text='Allow staff to update item availability and stock quantities'
    )
    is_active = models.BooleanField(default=True)
    
    # Work info
    position = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Members'
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} @ {self.restaurant.name}"


class ApiKey(BaseModel):
    """
    API Key for restaurant integrations.
    """
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='api_keys'
    )
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
    
    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"
