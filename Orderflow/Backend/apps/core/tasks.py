from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.core.files.storage import default_storage
import logging

from apps.orders.models import Order, OrderReservation
from apps.menu.models import MenuItem

logger = logging.getLogger(__name__)

@shared_task
def cleanup_stale_orders():
    """
    Cleaner for stale pending orders.
    Releases reserved stock and deletes orders that have been pending for too long.
    """
    # Threshold: Orders older than 30 minutes
    # (Adjust based on business logic, e.g., end of day)
    threshold = timezone.now() - timedelta(minutes=30)
    
    # Find pending, unpaid orders
    stale_orders = Order.objects.filter(
        status='pending',
        payment_status='pending',
        created_at__lt=threshold
    )
    
    count = 0
    for order in stale_orders:
        try:
            with transaction.atomic():
                # Release reserved stock for each item
                for item in order.items.select_related('menu_item').all():
                    if item.menu_item:
                        item.menu_item.release_stock(item.quantity)
                
                # Delete the order
                # Use query-set delete to bypass Order.delete() method protection
                # which is intended to prevent manual UI deletion.
                Order.objects.filter(pk=order.pk).delete()
                count += 1
                
        except Exception as e:
            logger.error(f"Error cleaning up stale order {order.pk}: {e}")
            
    return f"Cleaned up {count} stale orders."

@shared_task
def cleanup_qr_images():
    """
    Clean up generated QR code images that are no longer needed.
    """
    # Simply listing media/qr_codes directory processing is complex without path knowledge.
    # For now, we assume standard Django storage.
    # This is a placeholder for file cleanup if we store QRs physically.
    # Since we likely generate them on fly or store urls, this might be optional.
    pass
@shared_task
def cleanup_expired_reservations():
    """
    Release stock for expired reservations.
    Time critical: Should run every minute.
    """
    now = timezone.now()
    expired_reservations = OrderReservation.objects.filter(
        status=OrderReservation.Status.ACTIVE,
        expires_at__lt=now
    )
    
    count = 0
    for reservation in expired_reservations:
        try:
            with transaction.atomic():
                # Release reserved stock (JSON field items)
                # Items structure: [{'menu_item_id': 'uuid', 'quantity': 1, ...}]
                for item in reservation.items:
                    menu_item_id = item.get('menu_item_id')
                    quantity = int(item.get('quantity', 0))
                    
                    if menu_item_id and quantity > 0:
                        # Find item and release stock
                        try:
                            menu_item = MenuItem.objects.get(id=menu_item_id)
                            menu_item.release_stock(quantity)
                        except MenuItem.DoesNotExist:
                            # Item deleted? Just continue
                            pass
                            
                reservation.status = OrderReservation.Status.EXPIRED
                reservation.save()
                count += 1
                
        except Exception as e:
            logger.error(f"Error cleaning up reservation {reservation.id}: {e}")
            
    if count > 0:
        logger.info(f"Released stock for {count} expired reservations.")
    return f"Expired {count} reservations."
