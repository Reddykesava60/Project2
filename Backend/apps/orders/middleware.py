"""
Orders middleware.

Includes a lightweight once-per-day cleanup to remove stale pending cash orders.
"""

from __future__ import annotations

import threading

from django.utils import timezone

from .cleanup import cleanup_stale_pending_cash_orders

_lock = threading.Lock()
_last_cleanup_utc_date = None


class PendingCashOrderCleanupMiddleware:
    """
    Opportunistic daily cleanup.

    Runs at most once per process per UTC day on the first incoming request.
    This avoids adding external schedulers while still meeting the "auto cleanup"
    requirement, and the operation is idempotent.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._maybe_cleanup()
        return self.get_response(request)

    def _maybe_cleanup(self):
        global _last_cleanup_utc_date

        today_utc = timezone.now().date()
        with _lock:
            if _last_cleanup_utc_date == today_utc:
                return

            cleanup_stale_pending_cash_orders()
            _last_cleanup_utc_date = today_utc

