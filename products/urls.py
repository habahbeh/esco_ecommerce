# File: products/urls.py
"""
Updated URLs configuration for products app
"""

from django.urls import path
from django.http import JsonResponse
from django.urls import re_path

# Import product views (بعد دمج category_views.py في product_views.py)
from .views.product_views import (
    CategoryListView,  # الآن يتم استيرادها من product_views.py بدلاً من category_views.py
    ProductListView,
    ProductDetailView,
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
            # Q(description_en__icontains=query) |
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
         search_suggestions if SEARCH_VIEWS_AVAILABLE else fallback_search_view,
         name='search_suggestions'),

    # API للبحث السريع
    path('api/search/quick/',
         quick_search_simple if SEARCH_VIEWS_AVAILABLE else fallback_search_view,
         name='api_quick_search'),

    # الصفحة الرئيسية للمنتجات
    path('', ProductListView.as_view(), name='product_list'),

    # قوائم المنتجات الخاصة
    # path('categories/', CategoryListView.as_view(), name='category_list'),  # تم تحديثها لاستخدام CategoryListView من product_views.py
    # path('category/<slug:category_slug>/', ProductListView.as_view(), name='category_products'),
    re_path(r'category/(?P<category_slug>[-\w\u0600-\u06FF]+)/', ProductListView.as_view(), name='category_products'),

    path('featured/', FeaturedProductsView.as_view(), name='featured_products'),
    path('new/', NewProductsView.as_view(), name='new_products'),
    path('bestsellers/', BestSellersView.as_view(), name='best_sellers'),
    path('offers/', SpecialOffersView.as_view(), name='special_offers'),

    # المنتجات حسب العلامة التجارية والوسوم
    # path('brand/<slug:brand_slug>/', BrandProductsView.as_view(), name='brand_products'),
    re_path(r'brand/(?P<brand_slug>[-\w\u0600-\u06FF]+)/', BrandProductsView.as_view(), name='brand_products'),
    path('tag/<slug:tag_slug>/', TagProductsView.as_view(), name='tag_products'),

    # تفاصيل المنتج
    # path('<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    re_path(r'products/(?P<slug>[-\w\u0600-\u06FF]+)/$', ProductDetailView.as_view(), name='product_detail'),

    path('variant/<int:variant_id>/', ProductVariantDetailView.as_view(), name='variant_detail'),

    # URLs التقييمات
    path('product/<int:product_id>/add-review/', SubmitReviewView.as_view(), name='add_review'),
    path('product/<slug:product_slug>/reviews/', ProductReviewListView.as_view(), name='product_reviews'),
    path('review/<int:review_id>/vote/', VoteReviewHelpfulView.as_view(), name='vote_review'),
    path('review/<int:review_id>/report/', ReportReviewView.as_view(), name='report_review'),
    path('review/<int:review_id>/edit/', EditReviewView.as_view(), name='edit_review'),
    path('review/<int:review_id>/delete/', DeleteReviewView.as_view(), name='delete_review'),
    path('my-reviews/', UserReviewsView.as_view(), name='user_reviews'),
]


# URLs للتطوير والاختبار
from django.conf import settings

if settings.DEBUG:
    urlpatterns += [
        # URLs للاختبار
        path('debug/list/', ProductListView.as_view(paginate_by=5), name='debug_product_list'),

        # اختبار الـ views المحترفة
        path('debug/advanced-search/',
             AdvancedSearchView.as_view() if SEARCH_VIEWS_AVAILABLE else fallback_search_view,
             name='debug_advanced_search'),
    ]

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

# معلومات للمطور
VIEW_STATUS = {
    'search_views_available': SEARCH_VIEWS_AVAILABLE,
    'primary_search_view': 'SearchView' if SEARCH_VIEWS_AVAILABLE else 'fallback_search_view',
    'quick_search_available': SEARCH_VIEWS_AVAILABLE,
    'advanced_search_available': SEARCH_VIEWS_AVAILABLE,
    'search_api_available': SEARCH_VIEWS_AVAILABLE,
    'cache_enabled': False,  # تم تغييره إلى False لإزالة التخزين المؤقت
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

# تصدير معلومات مفيدة
__all__ = [
    'urlpatterns',
    'get_product_url',
    'get_category_url',
    'get_search_url',
    'get_advanced_search_url',
    'VIEW_STATUS',
    'SEARCH_VIEWS_AVAILABLE',
    'fallback_search_view',
]