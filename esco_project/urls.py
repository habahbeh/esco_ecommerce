from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # الإدارة - Admin
    path('admin/', admin.site.urls),
]

# المسارات مع دعم الترجمة - URL patterns with translation support
urlpatterns += i18n_patterns(
    # التطبيقات - Apps
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('dashboard/', include('dashboard.urls')),
    
    # تحويل اللغة - Language switching
    prefix_default_language=False
)

# إضافة مسارات للملفات الثابتة وملفات الوسائط في بيئة التطوير
# Add static and media URLs in development environment
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)