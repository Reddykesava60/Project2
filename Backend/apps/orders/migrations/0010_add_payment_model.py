"""
Migration: Add Payment model.

Creates a standalone Payment model with:
- restaurant_id for tenant isolation
- order FK for linking to orders
- method: cash | upi
- status: pending | success
- External payment gateway fields
- Staff collection tracking
"""

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('restaurants', '0003_restaurant_qr_secret'),
        ('orders', '0009_align_status_with_prd'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('method', models.CharField(choices=[('cash', 'Cash'), ('upi', 'UPI')], max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('success', 'Success')], default='pending', max_length=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('external_id', models.CharField(blank=True, help_text='Payment gateway transaction ID', max_length=100)),
                ('external_status', models.CharField(blank=True, max_length=50)),
                ('gateway_response', models.JSONField(blank=True, default=dict, help_text='Raw gateway response')),
                ('collected_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('collected_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='collected_payments', to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='orders.order')),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='restaurants.restaurant')),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['restaurant', 'created_at'], name='orders_paym_restaur_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['order'], name='orders_paym_order_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status'], name='orders_paym_status_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['external_id'], name='orders_paym_external_idx'),
        ),
    ]
