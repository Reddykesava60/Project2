"""
Migration for adding order-level preferences: is_parcel and spicy_level.
These fields are required by the frontend and PRD.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_add_table_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='is_parcel',
            field=models.BooleanField(
                default=False,
                help_text='Whether this order is for takeaway/parcel'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='spicy_level',
            field=models.CharField(
                choices=[
                    ('normal', 'Normal'),
                    ('medium', 'Medium'),
                    ('high', 'High'),
                ],
                default='normal',
                max_length=10,
                help_text='Overall spice level preference for the order'
            ),
        ),
    ]
