from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_optimize_pageview_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='pageview',
            name='status_code',
            field=models.PositiveSmallIntegerField(db_index=True, default=200),
        ),
        migrations.AddIndex(
            model_name='pageview',
            index=models.Index(fields=['status_code', 'timestamp'], name='core_pagevi_status__7a7fcb_idx'),
        ),
    ]
