# File: esco_project/urls.py
"""
URL configuration for esco_project.
الإعداد الرئيسي لروابط مشروع ESCO E-commerce
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from django.contrib.sitemaps.views import sitemap
from django.views.i18n import set_language, JavaScriptCatalog
from django.conf.urls.i18n import i18n_patterns

# Sitemaps (يمكن تفعيلها لاحقاً)
# from core.sitemaps import StaticViewSitemap
# from products.sitemaps import ProductSitemap, CategorySitemap

# sitemaps = {
#     'static': StaticViewSitemap,
#     'products': ProductSitemap,
#     'categories': CategorySitemap,
# }

# URLs التي لا تحتاج لغة (Language-independent URLs)
urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # Language and internationalization
    path('i18n/', include('django.conf.urls.i18n')),
    path('set-language/', set_language, name='set_language'),

    # JavaScript translations
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),

    # API endpoints (لا تحتاج ترجمة)
    path('api/', include([
        # يمكنك تفعيل هذه عند إنشاء ملفات API المناسبة
        # path('products/', include('products.api_urls', namespace='products_api')),
        # path('cart/', include('cart.api_urls', namespace='cart_api')),
        # path('orders/', include('orders.api_urls', namespace='orders_api')),
        # path('accounts/', include('accounts.api_urls', namespace='accounts_api')),
    ])),

    # Health check and system endpoints
    path('health/', TemplateView.as_view(template_name='health.html'), name='health_check'),
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt',
        content_type='text/plain'
    ), name='robots'),

    # Sitemap
    # path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),

    # Webhooks and external integrations (لا تحتاج ترجمة)
    path('webhooks/', include([
        # path('payment/', include('payment.webhook_urls')),
        # path('shipping/', include('shipping.webhook_urls')),
    ])),
]

# URLs التي تدعم الترجمة (Translatable URLs)
urlpatterns += i18n_patterns(
    # الصفحة الرئيسية - Homepage
    path('', include('core.urls', namespace='core')),

    # Products - المنتجات
    path('products/', include('products.urls', namespace='products')),
    path('shop/', RedirectView.as_view(url='/products/', permanent=True)),
    path('store/', RedirectView.as_view(url='/products/', permanent=True)),

    # User accounts - حسابات المستخدمين
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('auth/', include('django.contrib.auth.urls')),

    # Shopping cart - سلة التسوق
    path('cart/', include('cart.urls', namespace='cart')),
    path('checkout/', include('checkout.urls')),
    path('basket/', RedirectView.as_view(url='/cart/', permanent=True)),

    # Orders - الطلبات
    path('orders/', include('orders.urls', namespace='orders')),
    path('my-orders/', RedirectView.as_view(url='/orders/', permanent=True)),

    # Dashboard - لوحة التحكم
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('panel/', RedirectView.as_view(url='/dashboard/', permanent=True)),

    # Global search - البحث الشامل
    path('search/', RedirectView.as_view(url='/products/search/', permanent=True)),

    # Static pages - الصفحات الثابتة
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='pages/contact.html'), name='contact'),
    path('privacy/', TemplateView.as_view(template_name='pages/privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='pages/terms.html'), name='terms'),
    path('faq/', TemplateView.as_view(template_name='pages/faq.html'), name='faq'),
    path('shipping/', TemplateView.as_view(template_name='pages/shipping.html'), name='shipping_info'),
    path('returns/', TemplateView.as_view(template_name='pages/returns.html'), name='returns'),

    # Support pages - صفحات الدعم
    path('help/', TemplateView.as_view(template_name='pages/help.html'), name='help'),
    path('support/', RedirectView.as_view(url='/help/', permanent=True)),

    # Company pages - صفحات الشركة
    path('careers/', TemplateView.as_view(template_name='pages/careers.html'), name='careers'),
    path('news/', TemplateView.as_view(template_name='pages/news.html'), name='news'),

    path('payment/', include('payment.urls', namespace='payment')),
    path('checkout/', RedirectView.as_view(url='/payment/', permanent=True)),
    # Maintenance mode (يمكن تفعيلها عند الحاجة)
    # path('maintenance/', TemplateView.as_view(template_name='maintenance.html'), name='maintenance'),

    prefix_default_language=False,  # لا تضع اللغة الافتراضية في URL
)

# إعدادات البيئة التطويرية
if settings.DEBUG:
    # Django Debug Toolbar
    try:
        import debug_toolbar

        urlpatterns = [
                          path('__debug__/', include(debug_toolbar.urls)),
                      ] + urlpatterns
    except ImportError:
        pass

    # Serve media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Serve static files
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Development-only URLs
    urlpatterns += [
        # Test pages
        path('test/email/', TemplateView.as_view(template_name='test/email.html'), name='test_email'),
        path('test/404/', TemplateView.as_view(template_name='errors/404.html'), name='test_404'),
        path('test/500/', TemplateView.as_view(template_name='errors/500.html'), name='test_500'),
    ]

# معالجات الأخطاء المخصصة
handler404 = 'esco_project.views.page_not_found_view'
handler500 = 'esco_project.views.server_error_view'
handler403 = 'esco_project.views.permission_denied_view'
handler400 = 'esco_project.views.bad_request_view'

# تخصيص موقع الإدارة
admin.site.site_header = "ESCO E-commerce إدارة"
admin.site.site_title = "ESCO Admin"
admin.site.index_title = "مرحباً بك في لوحة تحكم ESCO"
admin.site.site_url = "/"  # رابط للعودة للموقع الرئيسي

# إعدادات إضافية للبيئة الإنتاجية
if not settings.DEBUG:
    # Security URLs for production
    urlpatterns += [
        # SSL and security
        path('.well-known/', include([
            # SSL certificate verification
            # path('acme-challenge/', include('acme.urls')),
        ])),
    ]

# URLs للتطبيقات الإضافية (يمكن تفعيلها لاحقاً)
# Uncomment when ready to use

# # Payment integration
# urlpatterns += i18n_patterns(
#     path('payment/', include('payment.urls', namespace='payment')),
#     path('checkout/', RedirectView.as_view(url='/payment/', permanent=True)),
# )

# # Wishlist
# urlpatterns += i18n_patterns(
#     path('wishlist/', include('wishlist.urls', namespace='wishlist')),
#     path('favorites/', RedirectView.as_view(url='/wishlist/', permanent=True)),
# )

# # Reviews and ratings
# urlpatterns += i18n_patterns(
#     path('reviews/', include('reviews.urls', namespace='reviews')),
# )

# # Coupons and discounts
# urlpatterns += i18n_patterns(
#     path('coupons/', include('coupons.urls', namespace='coupons')),
#     path('discounts/', RedirectView.as_view(url='/coupons/', permanent=True)),
# )

# # Blog
# urlpatterns += i18n_patterns(
#     path('blog/', include('blog.urls', namespace='blog')),
#     path('news/', RedirectView.as_view(url='/blog/', permanent=True)),
# )

# # Notifications
# urlpatterns += i18n_patterns(
#     path('notifications/', include('notifications.urls', namespace='notifications')),
# )

# # Vendor/Multi-vendor support
# urlpatterns += i18n_patterns(
#     path('vendors/', include('vendors.urls', namespace='vendors')),
#     path('seller/', RedirectView.as_view(url='/vendors/', permanent=True)),
# )

# # Inventory management
# urlpatterns += i18n_patterns(
#     path('inventory/', include('inventory.urls', namespace='inventory')),
# )

# تعليق توضيحي للمطورين
"""
هيكل الروابط:

1. روابط النظام (بدون ترجمة):
   - /admin/ - لوحة الإدارة
   - /api/ - API endpoints
   - /health/ - فحص النظام
   - /robots.txt - ملف الروبوتات

2. روابط الموقع (مع دعم الترجمة):
   - / - الصفحة الرئيسية
   - /products/ - المنتجات
   - /accounts/ - الحسابات
   - /cart/ - سلة التسوق
   - /orders/ - الطلبات
   - /dashboard/ - لوحة التحكم

3. صفحات ثابتة:
   - /about/ - من نحن
   - /contact/ - اتصل بنا
   - /privacy/ - سياسة الخصوصية

4. معالجة الأخطاء:
   - 404, 500, 403, 400 pages

ملاحظات:
- يدعم اللغتين العربية والإنجليزية
- URLs مرتبة حسب الأولوية
- يمكن تفعيل تطبيقات إضافية عند الحاجة
"""