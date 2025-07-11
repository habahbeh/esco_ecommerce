# Generated by Django 5.2.1 on 2025-06-21 19:25

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_slideritem'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaticContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, unique=True, verbose_name='المفتاح')),
                ('content_ar', ckeditor.fields.RichTextField(verbose_name='المحتوى بالعربية')),
                ('content_en', ckeditor.fields.RichTextField(verbose_name='المحتوى بالإنجليزية')),
                ('last_updated', models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')),
            ],
            options={
                'verbose_name': 'محتوى ثابت',
                'verbose_name_plural': 'محتويات ثابتة',
            },
        ),
    ]
