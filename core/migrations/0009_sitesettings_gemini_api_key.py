from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_add_company_profile_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='gemini_api_key',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='مفتاح Gemini API'),
        ),
    ]
