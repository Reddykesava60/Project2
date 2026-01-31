"""
Migration: Add MenuItemAttribute model.

Creates a model for configurable menu item attributes:
- restaurant_id for tenant isolation
- Supports number, select, multiselect, boolean types
- Options for select/multiselect
- Price modifiers for premium options
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0003_restaurant_qr_secret'),
        ('menu', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuItemAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Internal name (e.g., egg_count)', max_length=100)),
                ('display_name', models.CharField(help_text='Display name (e.g., Number of Eggs)', max_length=100)),
                ('attribute_type', models.CharField(
                    choices=[
                        ('number', 'Number'),
                        ('select', 'Select'),
                        ('multiselect', 'Multi-Select'),
                        ('boolean', 'Boolean'),
                    ],
                    default='select',
                    max_length=20,
                )),
                ('options', models.JSONField(blank=True, default=list, help_text='Available options for select/multiselect types')),
                ('default_value', models.JSONField(blank=True, help_text='Default value for this attribute', null=True)),
                ('min_value', models.IntegerField(blank=True, null=True)),
                ('max_value', models.IntegerField(blank=True, null=True)),
                ('price_modifier', models.DecimalField(decimal_places=2, default=0, help_text='Additional price per unit/selection', max_digits=10)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_required', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('menu_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='menu.menuitem')),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='menu_item_attributes', to='restaurants.restaurant')),
            ],
            options={
                'verbose_name': 'Menu Item Attribute',
                'verbose_name_plural': 'Menu Item Attributes',
                'ordering': ['menu_item', 'display_order', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='menuitemattribute',
            index=models.Index(fields=['restaurant', 'menu_item'], name='menu_menuitemattr_rest_item_idx'),
        ),
        migrations.AddConstraint(
            model_name='menuitemattribute',
            constraint=models.UniqueConstraint(fields=['menu_item', 'name'], name='unique_menu_item_attribute_name'),
        ),
    ]
