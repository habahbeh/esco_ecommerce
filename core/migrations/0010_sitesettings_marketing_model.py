from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_sitesettings_gemini_api_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='marketing_model',
            field=models.CharField(blank=True, default='openrouter/free', max_length=100, verbose_name='نموذج الذكاء الاصطناعي'),
        ),
    ]
