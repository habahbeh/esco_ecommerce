from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """
        تفعيل الإشارات عند تحميل التطبيق
        Activate signals when app is ready
        """
        import accounts.signals  # استيراد ملف الإشارات