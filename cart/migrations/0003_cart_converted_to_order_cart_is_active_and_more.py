# Generated by Django 5.2.1 on 2025-06-03 16:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0002_initial'),
        ('products', '0002_reviewimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='converted_to_order',
            field=models.BooleanField(default=False, help_text='تشير إلى ما إذا كانت السلة قد تم تحويلها إلى طلب', verbose_name='تم تحويلها إلى طلب'),
        ),
        migrations.AddField(
            model_name='cart',
            name='is_active',
            field=models.BooleanField(default=True, help_text='تشير إلى ما إذا كانت السلة نشطة أو تم تحويلها إلى طلب', verbose_name='نشطة'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='applied_discount',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='applied_to_cart_items', to='products.productdiscount', verbose_name='الخصم المطبق'),
        ),
    ]
