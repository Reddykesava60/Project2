"""
Automatic cleanup utilities for Orders.

Requirement:
- pending cash orders older than end of day must be deleted

Interpretation:
- If a CASH order is still unpaid (payment_status=PENDING) and still pending
  (status=PENDING) after the local restaurant day rolls over, it is stale and
  must be deleted.
"""

from __future__ import annotations

import logging
from typing import Optional

import datetime
from django.conf import settings
from django.utils import timezone

from apps.restaurants.models import Restaurant

from .models import Order

logger = logging.getLogger(__name__)


def _get_tzinfo(tz_name: Optional[str]):
    """
    Best-effort timezone resolver.
    Falls back to Django's default timezone.
    """
    if not tz_name:
        return timezone.get_default_timezone()

    try:
        # Python 3.9+
        from zoneinfo import ZoneInfo

        return ZoneInfo(tz_name)
    except Exception:
        return timezone.get_default_timezone()


def cleanup_stale_pending_cash_orders(now=None) -> int:
    """
    Delete stale pending cash orders across all restaurants.

    Returns:
        Number of Order rows deleted (not including cascaded related rows).
    """
    now = now or timezone.now()

    deleted_orders = 0

    # Keep it DB-friendly: small per-restaurant deletes, tenant-scoped.
    restaurants = Restaurant.objects.all().only("id", "timezone")
    for restaurant in restaurants:
        tz = _get_tzinfo(getattr(restaurant, "timezone", None) or getattr(settings, "TIME_ZONE", None))
        local_now = timezone.localtime(now, tz)
        start_of_today_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_utc = start_of_today_local.astimezone(datetime.timezone.utc)

        qs = Order.objects.filter(
            restaurant=restaurant,
            payment_method='cash',
            payment_status='pending',
            status='pending',
            created_at__lt=cutoff_utc,
        )

        count = qs.count()
        if count:
            # Signal (restore_stock_on_delete) handles stock release automatically
            # via pre_delete hook on OrderItem.
            
            # qs._raw_delete(qs.db) -> This causes IntegrityError on SQLite if FKs exist
            # Use standard delete() to handle cascades properly
            deleted, _ = qs.delete()
            deleted_orders += deleted

    if deleted_orders:
        logger.info("Cleaned up %s stale pending cash orders", deleted_orders)

    return deleted_orders


def cleanup_expired_reservations():
    """
    Release stock for expired reservations.
    """
    from apps.orders.models import OrderReservation
    from apps.menu.models import MenuItem
    
    now = timezone.now()
    expired = OrderReservation.objects.filter(
        status=OrderReservation.Status.ACTIVE,
        expires_at__lt=now
    )
    
    count = expired.count()
    if count:
        for res in expired:
            reserved_items = res.items # List of dicts
            for item in reserved_items:
                try:
                    menu_item = MenuItem.objects.get(id=item['menu_item_id'])
                    # Quantity in reservation items is string or int? 
                    # Implementation of OrderReservationCreateSerializer stores them.
                    # Usually coming from serializer it's python types, but let's ensure int.
                    qty = int(item['quantity'])
                    menu_item.release_stock(qty)
                except (MenuItem.DoesNotExist, ValueError):
                    pass
            
            res.status = OrderReservation.Status.EXPIRED
            res.save()
            
        logger.info(f"Cleaned up {count} expired reservations")
    return count

