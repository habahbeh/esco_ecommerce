from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        """
        تفعيل الإشارات عند تحميل التطبيق
        Activate signals when app is ready
        """
        import orders.signals  # استيراد ملف الإشارات
