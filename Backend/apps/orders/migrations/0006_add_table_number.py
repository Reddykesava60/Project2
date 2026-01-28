"""
Migration for adding table_number field to Order model.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_remove_customer_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='table_number',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
