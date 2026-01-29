"""
Management command to clean up stale pending cash orders.

This command should be run via cron or task scheduler at end of each day
(or early morning) to expire unpaid cash orders from the previous day.

Usage:
    python manage.py cleanup_stale_orders
    python manage.py cleanup_stale_orders --dry-run

Schedule (crontab example):
    # Run at 00:05 every day
    5 0 * * * cd /path/to/backend && python manage.py cleanup_stale_orders

Windows Task Scheduler:
    Create a task that runs at 00:05 daily:
    powershell -Command "cd C:\\path\\to\\backend; python manage.py cleanup_stale_orders"
"""

import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.cleanup import cleanup_stale_pending_cash_orders, _get_tzinfo
from apps.orders.models import Order
from apps.restaurants.models import Restaurant


class Command(BaseCommand):
    help = 'Clean up stale pending cash orders that were not paid by end of day'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--restaurant',
            type=str,
            help='Only clean up orders for a specific restaurant (by slug)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        restaurant_slug = options.get('restaurant')
        
        now = timezone.now()
        self.stdout.write(f"Starting stale order cleanup at {now}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no orders will be deleted'))
            
            # Count what would be deleted
            from apps.orders.cleanup import _get_tzinfo
            
            total_stale = 0
            restaurants = Restaurant.objects.all()
            if restaurant_slug:
                restaurants = restaurants.filter(slug=restaurant_slug)
                
            for restaurant in restaurants:
                tz = _get_tzinfo(restaurant.timezone)
                local_now = timezone.localtime(now, tz)
                start_of_today = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
                cutoff_utc = start_of_today.astimezone(datetime.timezone.utc)
                
                stale_count = Order.objects.filter(
                    restaurant=restaurant,
                    payment_method='cash',
                    payment_status='pending',
                    status='pending',
                    created_at__lt=cutoff_utc,
                ).count()
                
                if stale_count > 0:
                    self.stdout.write(
                        f"  {restaurant.name}: {stale_count} stale orders would be deleted"
                    )
                    total_stale += stale_count
                    
            self.stdout.write(self.style.SUCCESS(
                f"DRY RUN complete. {total_stale} orders would be deleted."
            ))
        else:
            # Actually delete
            deleted_count = cleanup_stale_pending_cash_orders(now)
            
            if deleted_count > 0:
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully cleaned up {deleted_count} stale pending cash orders"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    "No stale orders found to clean up"
                ))
