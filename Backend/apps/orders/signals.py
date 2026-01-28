"""
Signals for the Orders app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderItem
from .emails import send_staff_order_notification
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def handle_order_created(sender, instance, created, **kwargs):
    """Send notifications when order is created."""
    if created:
        # Notify restaurant staff via email
        send_staff_order_notification(instance)
        logger.info(f"Order {instance.order_number} created, staff notified")


@receiver(post_save, sender=OrderItem)
def update_menu_item_stats(sender, instance, created, **kwargs):
    """Update menu item order count when order item is created."""
    if created and instance.menu_item:
        instance.menu_item.increment_times_ordered(instance.quantity)
