from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import OrderItem, Order

@receiver(pre_delete, sender=OrderItem)
def restore_stock_on_delete(sender, instance, **kwargs):
    """
    Handle stock restoration when an OrderItem is deleted.
    - If Order was PAID: Increment stock_quantity (Restock)
    - If Order was PENDING: Decrement reserved_stock (Release)
    """
    try:
        # Check if menu_item exists (it might be null)
        if not instance.menu_item:
            return

        # Get parent order details
        # Since this is pre_delete, the relation should still be valid
        order = instance.order
        
        if order.payment_status == 'success':
            # Item was physically sold, so we must add it back to inventory
            instance.menu_item.restock(instance.quantity, mark_available=True)
        else:
            # Item was only reserved, so we just release the reservation
            instance.menu_item.release_stock(instance.quantity)
            
    except (Order.DoesNotExist, Exception):
        # Fail silently to prevent blocking deletion
        pass
