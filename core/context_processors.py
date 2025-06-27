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


# def static_content(request):
#     """
#     إضافة المحتوى الثابت الشائع للقوالب
#     Add common static content to templates
#     """
#     static_contents = {}
#     # for key in ['about', 'terms_conditions', 'privacy_policy']:
#     for key in ['about']:
#         try:
#             content = StaticContent.objects.get(key=key)
#             static_contents[key] = content
#         except StaticContent.DoesNotExist:
#             static_contents[key] = None
#
#     return {
#         'static_contents': static_contents
#     }

