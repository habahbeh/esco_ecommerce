from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import SiteSettings


@receiver(post_save, sender=SiteSettings)
def clear_settings_cache(sender, instance, **kwargs):
    """
    مسح الكاش عند تحديث إعدادات الموقع
    Clear cache when site settings are updated
    """
    cache.delete('site_settings')
    print(f"تم مسح كاش الإعدادات بعد تحديث: {instance.site_name}")