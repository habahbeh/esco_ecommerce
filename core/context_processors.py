from django.core.cache import cache
from .models import SiteSettings


def site_settings(request):
    """
    إضافة إعدادات الموقع لجميع القوالب مع التخزين المؤقت
    Add site settings to all templates with caching
    """
    # محاولة الحصول على الإعدادات من الكاش
    settings = cache.get('site_settings')

    if settings is None:
        # إذا لم تكن في الكاش، احصل عليها من قاعدة البيانات
        settings = SiteSettings.get_settings()
        # حفظها في الكاش لمدة ساعة
        cache.set('site_settings', settings, 3600)

    return {
        'site_settings': settings
    }