"""
Migration: Align Order status/payment fields with PRD requirements.

Changes:
- Order.status: Only pending | preparing | completed (lowercase)
- Order.payment_status: Only pending | success (lowercase)
- Order.payment_method: cash | upi (lowercase, ONLINE -> UPI)

This migration updates existing data to use the new lowercase values.
"""

from django.db import migrations, models


def migrate_order_status_values(apps, schema_editor):
    """Convert uppercase status values to lowercase PRD-compliant values."""
    Order = apps.get_model('orders', 'Order')
    
    # Map old values to new values
    status_mapping = {
        'PENDING': 'pending',
        'AWAITING_PAYMENT': 'pending',  # Treat as pending
        'PREPARING': 'preparing',
        'READY': 'completed',  # Ready -> completed
        'COMPLETED': 'completed',
        'CANCELLED': 'completed',  # Mark cancelled as completed for historical
        'FAILED': 'pending',  # Failed -> pending
    }
    
    payment_status_mapping = {
        'PENDING': 'pending',
        'SUCCESS': 'success',
        'FAILED': 'pending',  # Failed -> pending
        'REFUNDED': 'success',  # Refunded -> success (was paid)
    }
    
    payment_method_mapping = {
        'CASH': 'cash',
        'ONLINE': 'upi',  # ONLINE -> upi
    }
    
    # Update all orders
    for old_val, new_val in status_mapping.items():
        Order.objects.filter(status=old_val).update(status=new_val)
    
    for old_val, new_val in payment_status_mapping.items():
        Order.objects.filter(payment_status=old_val).update(payment_status=new_val)
    
    for old_val, new_val in payment_method_mapping.items():
        Order.objects.filter(payment_method=old_val).update(payment_method=new_val)


def reverse_migrate_order_status_values(apps, schema_editor):
    """Reverse migration - convert lowercase back to uppercase."""
    Order = apps.get_model('orders', 'Order')
    
    # Only reverse the definite mappings
    Order.objects.filter(status='pending').update(status='PENDING')
    Order.objects.filter(status='preparing').update(status='PREPARING')
    Order.objects.filter(status='completed').update(status='COMPLETED')
    
    Order.objects.filter(payment_status='pending').update(payment_status='PENDING')
    Order.objects.filter(payment_status='success').update(payment_status='SUCCESS')
    
    Order.objects.filter(payment_method='cash').update(payment_method='CASH')
    Order.objects.filter(payment_method='upi').update(payment_method='ONLINE')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_add_order_item_attributes'),
    ]

    operations = [
        # First, run the data migration
        migrations.RunPython(
            migrate_order_status_values,
            reverse_migrate_order_status_values,
        ),
        
        # Then alter the field choices
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('preparing', 'Preparing'),
                    ('completed', 'Completed'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('success', 'Success'),
                ],
                default='pending',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('cash', 'Cash'),
                    ('upi', 'UPI'),
                ],
                default='cash',
                max_length=10,
            ),
        ),
    ]
