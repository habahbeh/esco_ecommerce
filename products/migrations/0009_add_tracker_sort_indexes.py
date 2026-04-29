from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_merge_20260424_1403'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['-updated_at'], name='products_pr_updated_9f1a2b_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['stock_quantity'], name='products_pr_stock_q_3e7c1d_idx'),
        ),
    ]
