"""
Migration for adding AuditLog model.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial') if '0001_initial' in [] else ('core', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('restaurants', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('user_email', models.EmailField(blank=True, max_length=254)),
                ('restaurant_name', models.CharField(blank=True, max_length=200)),
                ('action', models.CharField(choices=[
                    ('LOGIN_SUCCESS', 'Login Success'),
                    ('LOGIN_FAILED', 'Login Failed'),
                    ('LOGOUT', 'Logout'),
                    ('PASSWORD_CHANGE', 'Password Changed'),
                    ('ORDER_CREATED', 'Order Created'),
                    ('ORDER_STATUS_CHANGE', 'Order Status Changed'),
                    ('ORDER_COMPLETED', 'Order Completed'),
                    ('ORDER_CANCELLED', 'Order Cancelled'),
                    ('PAYMENT_INITIATED', 'Payment Initiated'),
                    ('PAYMENT_SUCCESS', 'Payment Successful'),
                    ('PAYMENT_FAILED', 'Payment Failed'),
                    ('CASH_COLLECTED', 'Cash Collected'),
                    ('REFUND_ISSUED', 'Refund Issued'),
                    ('STAFF_CREATED', 'Staff Created'),
                    ('STAFF_UPDATED', 'Staff Updated'),
                    ('STAFF_PERMISSION_CHANGE', 'Staff Permission Changed'),
                    ('STAFF_DEACTIVATED', 'Staff Deactivated'),
                    ('RESTAURANT_CREATED', 'Restaurant Created'),
                    ('RESTAURANT_UPDATED', 'Restaurant Updated'),
                    ('RESTAURANT_STATUS_CHANGE', 'Restaurant Status Changed'),
                    ('QR_REGENERATED', 'QR Code Regenerated'),
                    ('QR_SCANNED', 'QR Code Scanned'),
                    ('QR_VERIFIED', 'QR Verification Successful'),
                    ('QR_VERIFICATION_FAILED', 'QR Verification Failed'),
                    ('MENU_ITEM_CREATED', 'Menu Item Created'),
                    ('MENU_ITEM_UPDATED', 'Menu Item Updated'),
                    ('MENU_ITEM_DELETED', 'Menu Item Deleted'),
                    ('CATEGORY_CREATED', 'Category Created'),
                    ('CATEGORY_DELETED', 'Category Deleted'),
                ], db_index=True, max_length=50)),
                ('severity', models.CharField(choices=[
                    ('INFO', 'Info'),
                    ('WARNING', 'Warning'),
                    ('ERROR', 'Error'),
                    ('CRITICAL', 'Critical'),
                ], default='INFO', max_length=10)),
                ('entity_type', models.CharField(blank=True, max_length=50)),
                ('entity_id', models.CharField(blank=True, max_length=50)),
                ('entity_repr', models.CharField(blank=True, max_length=200)),
                ('old_value', models.JSONField(blank=True, null=True)),
                ('new_value', models.JSONField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('metadata', models.JSONField(default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('request_id', models.CharField(blank=True, max_length=50)),
                ('restaurant', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to='restaurants.restaurant'
                )),
                ('user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Audit Log',
                'verbose_name_plural': 'Audit Logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['restaurant', 'timestamp'], name='core_auditl_restaur_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'timestamp'], name='core_auditl_user_ti_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action', 'timestamp'], name='core_auditl_action_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['entity_type', 'entity_id'], name='core_auditl_entity_idx'),
        ),
    ]
