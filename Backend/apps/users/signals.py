"""
Signals for the Users app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Handle user creation events."""
    if created:
        # Add any post-creation logic here
        pass
