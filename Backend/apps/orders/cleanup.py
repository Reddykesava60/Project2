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
            # qs._raw_delete(qs.db) -> This causes IntegrityError on SQLite if FKs exist
            # Use standard delete() to handle cascades properly
            deleted, _ = qs.delete()
            deleted_orders += deleted

    if deleted_orders:
        logger.info("Cleaned up %s stale pending cash orders", deleted_orders)

    return deleted_orders

