"""
Migration for adding item-level attributes to OrderItem.
Supports customizations like egg count, extra toppings, etc.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_add_order_preferences'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='attributes',
            field=models.JSONField(
                default=dict,
                blank=True,
                help_text='Item-specific customizations (e.g., {"egg_count": 2, "extra_toppings": ["cheese", "onion"]})'
            ),
        ),
    ]
