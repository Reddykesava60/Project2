from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models import F
from .models import OrderItem

@receiver(post_delete, sender=OrderItem)
def restore_stock_on_delete(sender, instance, **kwargs):
    """
    Restore stock when an OrderItem is deleted.
    This handles:
    1. Order cancellation/deletion
    2. Stale order cleanup
    """
    try:
        if instance.menu_item and instance.menu_item.stock_quantity is not None:
            # Use F() expression to avoid race conditions
            instance.menu_item.stock_quantity = F('stock_quantity') + instance.quantity
            instance.menu_item.save(update_fields=['stock_quantity'])
    except Exception:
        # Menu item might be deleted already, or stock cleanup not needed
        pass
