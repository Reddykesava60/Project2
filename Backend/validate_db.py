"""Validate database order statuses."""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.orders.models import Order
from django.db.models import Count

print("="*60)
print("DATABASE ORDER STATUS VALIDATION")
print("="*60)

print("\nAll orders:")
for o in Order.objects.all().order_by('status', 'created_at'):
    print(f"  ID: {str(o.id)[:8]}... | Status: {o.status:20} | Customer: {o.customer_name}")

print("\n" + "="*60)
print("STATUS DISTRIBUTION:")
print("="*60)
stats = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
for s in stats:
    print(f"  {s['status']:20}: {s['count']}")

print("\n" + "="*60)
print("VALIDATION CHECKS:")
print("="*60)

# Check for any NULL statuses
null_status = Order.objects.filter(status__isnull=True).count()
print(f"  Orders with NULL status: {null_status} {'❌ FIX REQUIRED' if null_status > 0 else '✅'}")

# Check for empty string statuses
empty_status = Order.objects.filter(status='').count()
print(f"  Orders with empty status: {empty_status} {'❌ FIX REQUIRED' if empty_status > 0 else '✅'}")

# Check completed orders are properly marked
completed = Order.objects.filter(status='COMPLETED').count()
print(f"  Completed orders: {completed} ✅")

# Check all statuses are valid
valid_statuses = ['PENDING', 'AWAITING_PAYMENT', 'PREPARING', 'READY', 'COMPLETED', 'CANCELLED', 'FAILED']
invalid = Order.objects.exclude(status__in=valid_statuses).count()
print(f"  Orders with invalid status: {invalid} {'❌ FIX REQUIRED' if invalid > 0 else '✅'}")

print("\n" + "="*60)
if null_status == 0 and empty_status == 0 and invalid == 0:
    print("✅ DATABASE VALIDATION PASSED")
else:
    print("❌ DATABASE HAS ISSUES - FIX REQUIRED")
print("="*60)
