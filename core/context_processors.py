from .models import SiteSettings

def site_settings(request):
    """
    معالج سياق لإعدادات الموقع - يضيف إعدادات الموقع إلى سياق القالب
    Site settings context processor - adds site settings to template context
    """
    settings = SiteSettings.get_settings()
    return {'site_settings': settings}