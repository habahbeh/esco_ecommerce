# File: products/urls.py
"""
Updated URLs configuration for products app
Using professional search views
"""

from django.urls import path
from django.views.decorators.cache import cache_page
from django.http import JsonResponse

# Import product views
from .views.product_views import (
    ProductListView,
    ProductDetailView,
    CategoryListView,
    CategoryDetailView,
    SpecialOffersView,
    TagProductsView,
    BrandProductsView,
    NewProductsView,
    FeaturedProductsView,
    BestSellersView,
    ProductVariantDetailView,
)

from .views.review_views import (
    SubmitReviewView,
    ProductReviewListView,
    VoteReviewHelpfulView,
    ReportReviewView,
    UserReviewsView,
    EditReviewView,
    DeleteReviewView,
)

# Import search views
try:
    from .views.search_views import (
        SearchView,
        AdvancedSearchView,
        SearchSuggestionsPageView,
        QuickSearchView,
        search_suggestions,
        quick_search_simple,
        advanced_search_view,
    )

    SEARCH_VIEWS_AVAILABLE = True
except ImportError:
    SEARCH_VIEWS_AVAILABLE = False

app_name = 'products'


# Fallback search view if search_views not available
def fallback_search_view(request):
    """
    عرض البحث الاحتياطي - في حالة عدم توفر search_views
    Fallback search view - if search_views not available
    """
    from django.shortcuts import render
    from django.db.models import Q

    query = request.GET.get('q', '').strip()
    products = []

    if query:
        from .models import Product
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(description__icontains=query) |
            Q(description_en__icontains=query) |
            Q(sku__icontains=query),
            is_active=True,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images')[:50]

    return render(request, 'products/search_results.html', {
        'search_query': query,
        'products': products,
        'results_count': len(products),
        'title': f'نتائج البحث عن: {query}' if query else 'البحث في المنتجات',
    })


def search_suggestions_api(request):
    """
    API لاقتراحات البحث - إرجاع JSON
    Search suggestions API - returns JSON
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        from .models import Product, Category, Brand

        # البحث في المنتجات
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(name_en__icontains=query),
            is_active=True,
            status='published'
        ).select_related('category', 'brand')[:5]

        for product in products:
            suggestions.append({
                'type': 'product',
                'title': product.name,
                'url': product.get_absolute_url() if hasattr(product, 'get_absolute_url') else '#',
                'image': product.main_image.url if hasattr(product, 'main_image') and product.main_image else '',
                'price': str(getattr(product, 'current_price', getattr(product, 'base_price', 0))),
            })

        # البحث في الفئات
        categories = Category.objects.filter(
            Q(name__icontains=query) | Q(name_en__icontains=query),
            is_active=True
        )[:3]

        for category in categories:
            suggestions.append({
                'type': 'category',
                'title': category.name,
                'url': category.get_absolute_url() if hasattr(category, 'get_absolute_url') else '#',
                'count': category.products.filter(is_active=True, status='published').count(),
            })

    return JsonResponse({'suggestions': suggestions})


# Main URL patterns
urlpatterns = [
    # البحث - استخدام الـ views المحترفة إذا كانت متوفرة
    path('search/',
         SearchView.as_view() if SEARCH_VIEWS_AVAILABLE else fallback_search_view,
         name='product_search'),

    path('search/quick/',
         QuickSearchView.as_view() if SEARCH_VIEWS_AVAILABLE else fallback_search_view,
         name='quick_search'),

    path('search/advanced/',
         AdvancedSearchView.as_view() if SEARCH_VIEWS_AVAILABLE else fallback_search_view,
         name='advanced_search'),

    path('search/suggestions-page/',
         SearchSuggestionsPageView.as_view() if SEARCH_VIEWS_AVAILABLE else fallback_search_view,
         name='search_suggestions_page'),

    # APIs للبحث
    path('api/search/suggestions/',
         search_suggestions if SEARCH_VIEWS_AVAILABLE else search_suggestions_api,
         name='search_suggestions'),

    # API للبحث السريع (إضافية)
    path('api/search/quick/',
         quick_search_simple if SEARCH_VIEWS_AVAILABLE else fallback_search_view,
         name='api_quick_search'),

    # الصفحة الرئيسية للمنتجات
    path('', ProductListView.as_view(), name='product_list'),

    # قوائم المنتجات الخاصة
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),
    path('featured/', FeaturedProductsView.as_view(), name='featured_products'),
    path('new/', NewProductsView.as_view(), name='new_products'),
    path('bestsellers/', BestSellersView.as_view(), name='best_sellers'),
    path('offers/', SpecialOffersView.as_view(), name='special_offers'),

    # المنتجات حسب الفئة
    path('category/<slug:category_slug>/', ProductListView.as_view(), name='category_products'),
    path('category/<slug:slug>/detail/', CategoryDetailView.as_view(), name='category_detail'),

    # المنتجات حسب العلامة التجارية والوسوم
    path('brand/<slug:brand_slug>/', BrandProductsView.as_view(), name='brand_products'),
    path('tag/<slug:tag_slug>/', TagProductsView.as_view(), name='tag_products'),

    # تفاصيل المنتج
    path('<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('variant/<int:variant_id>/', ProductVariantDetailView.as_view(), name='variant_detail'),

    # URLs التقييمات - أضف هذه الأسطر الجديدة
    path('product/<int:product_id>/add-review/', SubmitReviewView.as_view(), name='add_review'),
    path('product/<slug:product_slug>/reviews/', ProductReviewListView.as_view(), name='product_reviews'),
    path('review/<int:review_id>/vote/', VoteReviewHelpfulView.as_view(), name='vote_review'),
    path('review/<int:review_id>/report/', ReportReviewView.as_view(), name='report_review'),
    path('review/<int:review_id>/edit/', EditReviewView.as_view(), name='edit_review'),
    path('review/<int:review_id>/delete/', DeleteReviewView.as_view(), name='delete_review'),
    path('my-reviews/', UserReviewsView.as_view(), name='user_reviews'),

]

# URLs محسنة مع التخزين المؤقت للإنتاج
cached_urlpatterns = [
    # تخزين مؤقت لقائمة المنتجات لمدة 5 دقائق
    path('cached/', cache_page(300)(ProductListView.as_view()), name='cached_product_list'),

    # تخزين مؤقت للفئات لمدة 10 دقائق
    path('cached/categories/', cache_page(600)(CategoryListView.as_view()), name='cached_category_list'),

    # تخزين مؤقت للعروض لمدة 15 دقيقة
    path('cached/offers/', cache_page(900)(SpecialOffersView.as_view()), name='cached_special_offers'),

    # تخزين مؤقت للبحث لمدة 5 دقائق
    path('cached/search/',
         cache_page(300)(SearchView.as_view() if SEARCH_VIEWS_AVAILABLE else fallback_search_view),
         name='cached_search'),
]

# إضافة URLs المخزنة مؤقتاً في الإنتاج
from django.conf import settings

if not settings.DEBUG:
    urlpatterns.extend(cached_urlpatterns)


# Helper functions for URL generation
def get_product_url(product):
    """الحصول على رابط المنتج"""
    from django.urls import reverse
    try:
        return reverse('products:product_detail', kwargs={'slug': product.slug})
    except:
        return '#'


def get_category_url(category):
    """الحصول على رابط الفئة"""
    from django.urls import reverse
    try:
        return reverse('products:category_products', kwargs={'category_slug': category.slug})
    except:
        return '#'


def get_search_url(query=''):
    """الحصول على رابط البحث"""
    from django.urls import reverse
    url = reverse('products:product_search')
    if query:
        url += f'?q={query}'
    return url


def get_advanced_search_url(**filters):
    """الحصول على رابط البحث المتقدم مع الفلاتر"""
    from django.urls import reverse
    from django.http import QueryDict

    url = reverse('products:advanced_search')
    if filters:
        params = QueryDict(mutable=True)
        for key, value in filters.items():
            if isinstance(value, list):
                params.setlist(key, value)
            else:
                params[key] = value
        url += f'?{params.urlencode()}'
    return url


# URLs للتطوير والاختبار
if settings.DEBUG:
    urlpatterns += [
        # URLs للاختبار
        path('debug/list/', ProductListView.as_view(paginate_by=5), name='debug_product_list'),
        path('debug/search/', fallback_search_view, name='debug_search'),

        # اختبار الـ views المحترفة
        path('debug/advanced-search/',
             AdvancedSearchView.as_view() if SEARCH_VIEWS_AVAILABLE else fallback_search_view,
             name='debug_advanced_search'),

        # اختبار البحث السريع
        path('debug/quick-search/',
             QuickSearchView.as_view() if SEARCH_VIEWS_AVAILABLE else fallback_search_view,
             name='debug_quick_search'),

        # اختبار APIs
        path('debug/api/suggestions/',
             search_suggestions if SEARCH_VIEWS_AVAILABLE else search_suggestions_api,
             name='debug_search_suggestions'),
    ]

# معلومات للمطور
VIEW_STATUS = {
    'search_views_available': SEARCH_VIEWS_AVAILABLE,
    'primary_search_view': 'SearchView' if SEARCH_VIEWS_AVAILABLE else 'fallback_search_view',
    'quick_search_available': SEARCH_VIEWS_AVAILABLE,
    'advanced_search_available': SEARCH_VIEWS_AVAILABLE,
    'search_api_available': SEARCH_VIEWS_AVAILABLE,
    'cache_enabled': not settings.DEBUG,
    'imported_views': [
        'SearchView' if SEARCH_VIEWS_AVAILABLE else None,
        'QuickSearchView' if SEARCH_VIEWS_AVAILABLE else None,
        'AdvancedSearchView' if SEARCH_VIEWS_AVAILABLE else None,
        'search_suggestions' if SEARCH_VIEWS_AVAILABLE else 'search_suggestions_api',
    ]
}

# تسجيل معلومات التشغيل
import logging

logger = logging.getLogger(__name__)

if SEARCH_VIEWS_AVAILABLE:
    logger.info("Products URLs: Using professional search views")
else:
    logger.warning("Products URLs: Using fallback search views - check search_views.py")

# في النهاية، تصدير معلومات مفيدة
__all__ = [
    'urlpatterns',
    'get_product_url',
    'get_category_url',
    'get_search_url',
    'get_advanced_search_url',
    'VIEW_STATUS',
    'SEARCH_VIEWS_AVAILABLE',
    'fallback_search_view',
    'search_suggestions_api',
]