from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_add_performance_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchSynonym',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('terms', models.TextField(help_text='مصطلحات مفصولة بفاصلة - مثال: موبايل, جوال, هاتف', verbose_name='المصطلحات المترادفة')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
            ],
            options={
                'verbose_name': 'مرادف بحث',
                'verbose_name_plural': 'مرادفات البحث',
            },
        ),
        migrations.CreateModel(
            name='SearchQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.CharField(max_length=255, unique=True, verbose_name='عبارة البحث')),
                ('count', models.PositiveIntegerField(default=1, verbose_name='عدد المرات')),
                ('results_count', models.PositiveIntegerField(default=0, verbose_name='عدد النتائج')),
                ('last_searched', models.DateTimeField(auto_now=True, verbose_name='آخر بحث')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
            ],
            options={
                'verbose_name': 'استعلام بحث',
                'verbose_name_plural': 'استعلامات البحث',
                'ordering': ['-count'],
            },
        ),
    ]
