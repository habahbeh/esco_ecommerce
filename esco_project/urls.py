# File: esco_project/urls.py
"""
URL configuration for esco_project.
الإعداد الرئيسي لروابط مشروع ESCO E-commerce
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import TemplateView, RedirectView
from django.contrib.sitemaps.views import sitemap, index as sitemap_index
from django.views.decorators.cache import cache_page
# from django.views.i18n import set_language, JavaScriptCatalog
from django.conf.urls.i18n import i18n_patterns

from core.sitemaps import StaticViewSitemap
from core.agent_views import MCPServerCardView, A2AAgentCardView, AgentSkillsView, APICatalogView, TrafficAdviceView
from core.llms_view import LlmsTxtView
from products.sitemaps import ProductSitemap, CategorySitemap, BrandSitemap
from blog.sitemaps import BlogPostSitemap, BlogCategorySitemap

sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'brands': BrandSitemap,
    'blog_posts': BlogPostSitemap,
    'blog_categories': BlogCategorySitemap,
}

# URLs التي لا تحتاج لغة (Language-independent URLs)
urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # Language and internationalization
    path('i18n/', include('django.conf.urls.i18n')),
    # path('set-language/', set_language, name='set_language'),

    # JavaScript translations
    # path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),

    # API endpoints (لا تحتاج ترجمة)
    path('api/', include([
        path('chatbot/', include('chatbot.urls', namespace='chatbot')),
        # يمكنك تفعيل هذه عند إنشاء ملفات API المناسبة
        # path('products/', include('products.api_urls', namespace='products_api')),
        # path('cart/', include('cart.api_urls', namespace='cart_api')),
        # path('orders/', include('orders.api_urls', namespace='orders_api')),
        # path('accounts/', include('accounts.api_urls', namespace='accounts_api')),
    ])),

    # Google Search Console verification
    path('google54ee986151e326dc.html', TemplateView.as_view(
        template_name='google54ee986151e326dc.html',
        content_type='text/html'
    ), name='google_verification'),

    # Favicon at root for Google and browsers
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico', permanent=True)),

    # Health check and system endpoints
    path('health/', TemplateView.as_view(template_name='health.html'), name='health_check'),
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt',
        content_type='text/plain'
    ), name='robots'),

    # LLMs
    path('llms.txt', LlmsTxtView.as_view(), name='llms-txt'),

    # IndexNow verification key
    path('a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.txt', lambda r: HttpResponse('a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6', content_type='text/plain')),

    # Sitemap index + per-section sitemaps — cached 6 hours since they query
    # 4k+ products/categories from DB and take 2-3s uncached. New products/
    # blog posts will appear within 6 hours of publishing, which is acceptable
    # for SEO (Googlebot doesn't crawl that often anyway).
    path('sitemap.xml',
         cache_page(60 * 60 * 6)(sitemap_index),
         {'sitemaps': sitemaps, 'sitemap_url_name': 'sitemaps'}),
    path('sitemap-<section>.xml',
         cache_page(60 * 60 * 6)(sitemap),
         {'sitemaps': sitemaps},
         name='sitemaps'),

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
    path('events/', include('events.urls', namespace='events')),

    # Blog - المدونة
    path('blog/', include('blog.urls', namespace='blog')),

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
urlpatterns += [
    path('.well-known/', include([
        path('mcp.json', MCPServerCardView.as_view(), name='mcp-server-card'),
        path('mcp/server-card.json', MCPServerCardView.as_view(), name='mcp-server-card-alt'),
        path('agent-card.json', A2AAgentCardView.as_view(), name='a2a-agent-card'),
        path('agent-skills/index.json', AgentSkillsView.as_view(), name='agent-skills'),
        path('api-catalog', APICatalogView.as_view(), name='api-catalog'),
        path('traffic-advice', TrafficAdviceView.as_view(), name='traffic-advice'),
    ])),

    # Strip /ar/ prefix — Arabic is the default language and uses no prefix,
    # so /ar/foo/ would 404. Permanent-redirect it to /foo/ instead.
    re_path(r'^ar/(?P<rest>.*)$',
            RedirectView.as_view(url='/%(rest)s', permanent=True, query_string=True),
            name='strip-ar-prefix'),

    # Strip doubled '/products/products/' prefix — old broken links that doubled the
    # path segment. 301 → /products/<rest>/
    re_path(r'^products/products/(?P<rest>.*)$',
            RedirectView.as_view(url='/products/%(rest)s', permanent=True, query_string=True),
            name='strip-doubled-products'),

    # ─── Legacy PrestaShop URL cleanup ───────────────────────────────────────
    # Google Search Console reported 11,115 URLs in "Not found (404)" — all from
    # the old PrestaShop site that's still in Google's index from months ago.
    # All redirects below 301 to /en/products/ so Google passes link equity and
    # stops treating them as broken pages.
    #
    # MAIN pattern (~11K URLs): faceted-filter URLs from the old shop.
    #   /en/2-2-categories?q=Availability-In stock/Brand-AIRFIT-BOSCH-...
    #   /ar/2-2-categories?q=العلامة-التجارية-...&page=N&order=...
    #   The /ar/ form is already handled by the strip-ar-prefix redirect above,
    #   which forwards to /2-2-categories... — this rule catches THAT next-hop.
    re_path(r'^(en/)?\d+-\d+-categories.*$',
            RedirectView.as_view(url='/en/products/', permanent=True),
            name='legacy-prestashop-faceted'),

    # Product-detail URLs: /en/<CategoryName>/<digits>-<slug>.html
    # CamelCase variant: /en/HAMMER/2932-RUBBER_HAMMER_FINDER.html
    # snake_case variant: /en/ceramic_fiber/2684-Braided_ceramic_fiber_18MM.html
    # Mixed-case: /en/Pneumatic_Cylinders/1450-Air_Cylinder_TN.html
    # (\w matches both upper and lower so we catch all variants now)
    re_path(r'^en/[A-Za-z][A-Za-z0-9_]*/\d+[-_].*$',
            RedirectView.as_view(url='/en/products/', permanent=True),
            name='legacy-prestashop-product'),

    # Category-listing URLs: /en/<digits>-<CategoryName> (e.g. /en/570-Electrical_Department)
    re_path(r'^en/\d+-[A-Za-z_][A-Za-z0-9_]*(\?.*)?/?$',
            RedirectView.as_view(url='/en/products/', permanent=True),
            name='legacy-prestashop-category'),

    # Pagination URLs from old shop: /en/2-2-categories or /en/100-Silencer?order=...
    re_path(r'^en/\d+-\d+-[A-Za-z]+/?$',
            RedirectView.as_view(url='/en/products/', permanent=True),
            name='legacy-prestashop-pagination'),

    # PrestaShop module/customer/checkout system URLs
    re_path(r'^(en/)?module/.*$',
            RedirectView.as_view(url='/en/products/', permanent=True),
            name='legacy-prestashop-module'),

    # Arabic legacy product URLs (mojibake'd UTF-8) that survived the
    # strip-ar-prefix redirect. Catches /<arabic-text>/<digits>-<...>.html
    re_path(r'^[^/]+/\d+-[^/]+\.html$',
            RedirectView.as_view(url='/', permanent=True),
            name='legacy-prestashop-arabic'),
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

# Blog is now active in the main urlpatterns above

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