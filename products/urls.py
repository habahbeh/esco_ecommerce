# File: products/urls.py
"""
Updated URLs configuration for products app
Compatible with the new organized views structure
"""

from django.urls import path, include
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

# Import views from the new organized structure
from .views import (
    # Main product views
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

    # Search views
    SearchView,
    AdvancedSearchView,
    SearchSuggestionsPageView,

    # API views
    search_suggestions,
    product_quick_view,
    get_variant_details,
    increment_category_views,
    product_360_view,

    # Wishlist views
    wishlist_view,
    add_to_wishlist,
    remove_from_wishlist,
    toggle_wishlist,

    # Comparison views
    comparison_view,
    add_to_comparison,

    # Review views
    submit_review,
    vote_review_helpful,
    report_review,

    # Admin views
    bulk_action_products,
    reset_product_stats,
    duplicate_product,

    # Export views
    export_products,
    export_reviews,
)

app_name = 'products'

# API URLs patterns
api_patterns = [
    # Search API
    path('search/suggestions/', search_suggestions, name='search_suggestions'),

    # Product API
    path('product/<int:product_id>/quick-view/', product_quick_view, name='product_quick_view'),
    path('product/<int:product_id>/360-view/', product_360_view, name='product_360_view'),
    path('variant/<int:variant_id>/details/', get_variant_details, name='variant_details'),

    # Wishlist API
    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/toggle/<int:product_id>/', toggle_wishlist, name='toggle_wishlist'),

    # Comparison API
    path('comparison/add/', add_to_comparison, name='add_to_comparison'),

    # Review API
    path('review/submit/<int:product_id>/', submit_review, name='submit_review'),
    path('review/<int:review_id>/vote/', vote_review_helpful, name='vote_review_helpful'),
    path('review/<int:review_id>/report/', report_review, name='report_review'),

    # Analytics API
    path('category/<int:category_id>/increment-views/', increment_category_views, name='increment_category_views'),
]

# Admin URLs patterns
admin_patterns = [
    # Bulk operations
    path('bulk-actions/', bulk_action_products, name='bulk_action_products'),
    path('<int:product_id>/reset-stats/', reset_product_stats, name='reset_product_stats'),
    path('<int:product_id>/duplicate/', duplicate_product, name='duplicate_product'),

    # Export
    path('export/', export_products, name='export_products'),
    path('export/reviews/', export_reviews, name='export_reviews'),
]

# Main URL patterns
urlpatterns = [
    # Home and listing pages
    path('', ProductListView.as_view(), name='product_list'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('search/', SearchView.as_view(), name='search'),
    path('search/advanced/', AdvancedSearchView.as_view(), name='advanced_search'),
    path('search/suggestions/', SearchSuggestionsPageView.as_view(), name='search_suggestions_page'),

    # Special product listings
    path('offers/', SpecialOffersView.as_view(), name='special_offers'),
    path('new/', NewProductsView.as_view(), name='new_products'),
    path('featured/', FeaturedProductsView.as_view(), name='featured_products'),
    path('bestsellers/', BestSellersView.as_view(), name='best_sellers'),

    # Category-based listings
    path('category/<slug:category_slug>/', ProductListView.as_view(), name='category_products'),
    path('category/<slug:slug>/detail/', CategoryDetailView.as_view(), name='category_detail'),

    # Tag and brand listings
    path('tag/<slug:tag_slug>/', TagProductsView.as_view(), name='tag_products'),
    path('brand/<slug:brand_slug>/', BrandProductsView.as_view(), name='brand_products'),

    # Product detail
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),

    # User features
    path('wishlist/', wishlist_view, name='wishlist'),
    path('comparison/', comparison_view, name='comparison'),

    # API endpoints
    path('api/', include(api_patterns)),

    # Admin endpoints (staff only)
    path('admin/', include(admin_patterns)),
]

# Cache configurations for better performance
# These decorators can be applied to specific views

# Cache product list for 5 minutes, vary by user agent
cached_product_list = cache_page(300)(
    vary_on_headers('User-Agent')(ProductListView.as_view())
)

# Cache category list for 10 minutes
cached_category_list = cache_page(600)(CategoryListView.as_view())

# Cache special offers for 15 minutes
cached_special_offers = cache_page(900)(SpecialOffersView.as_view())

# Alternative URL patterns with caching (can replace main patterns if needed)
cached_urlpatterns = [
    path('', cached_product_list, name='cached_product_list'),
    path('categories/', cached_category_list, name='cached_category_list'),
    path('offers/', cached_special_offers, name='cached_special_offers'),
]

# URL patterns for different view types (for reference)
VIEW_TYPE_PATTERNS = {
    'list_views': [
        'product_list',
        'category_list',
        'new_products',
        'featured_products',
        'best_sellers',
        'special_offers'
    ],
    'detail_views': [
        'product_detail',
        'category_detail'
    ],
    'search_views': [
        'search',
        'advanced_search'
    ],
    'user_features': [
        'wishlist',
        'comparison'
    ],
    'api_endpoints': [
        'search_suggestions',
        'product_quick_view',
        'add_to_wishlist',
        'toggle_wishlist'
    ]
}

# URL name to view class mapping (for documentation)
URL_VIEW_MAPPING = {
    'product_list': ProductListView,
    'product_detail': ProductDetailView,
    'category_list': CategoryListView,
    'category_detail': CategoryDetailView,
    'search': SearchView,
    'advanced_search': AdvancedSearchView,
    'special_offers': SpecialOffersView,
    'new_products': NewProductsView,
    'featured_products': FeaturedProductsView,
    'best_sellers': BestSellersView,
    'tag_products': TagProductsView,
    'brand_products': BrandProductsView,
    'wishlist': 'wishlist_view (function)',
    'comparison': 'comparison_view (function)',
}

# SEO-friendly URL patterns (alternative naming)
seo_urlpatterns = [
    # Arabic URL patterns for better SEO
    path('المنتجات/', ProductListView.as_view(), name='products_ar'),
    path('الفئات/', CategoryListView.as_view(), name='categories_ar'),
    path('البحث/', SearchView.as_view(), name='search_ar'),
    path('العروض/', SpecialOffersView.as_view(), name='offers_ar'),
    path('الجديد/', NewProductsView.as_view(), name='new_ar'),
    path('المميز/', FeaturedProductsView.as_view(), name='featured_ar'),
    path('الأكثر-مبيعا/', BestSellersView.as_view(), name='bestsellers_ar'),
    path('قائمة-الأمنيات/', wishlist_view, name='wishlist_ar'),
    path('المقارنة/', comparison_view, name='comparison_ar'),
]

# Mobile-specific URL patterns (if needed)
mobile_urlpatterns = [
    path('m/', ProductListView.as_view(template_name='products/mobile/product_list.html'),
         name='mobile_product_list'),
    path('m/product/<slug:slug>/', ProductDetailView.as_view(template_name='products/mobile/product_detail.html'),
         name='mobile_product_detail'),
]

# Development/Testing URL patterns
debug_urlpatterns = [
    path('debug/product-list/', ProductListView.as_view(paginate_by=5), name='debug_product_list'),
    path('debug/search/', SearchView.as_view(), name='debug_search'),
]


# Conditional URL inclusion based on settings
def get_conditional_urls():
    """
    Return additional URL patterns based on Django settings
    """
    from django.conf import settings

    additional_patterns = []

    # Add SEO patterns if enabled
    if getattr(settings, 'ENABLE_ARABIC_URLS', False):
        additional_patterns.extend(seo_urlpatterns)

    # Add mobile patterns if mobile support is enabled
    if getattr(settings, 'ENABLE_MOBILE_URLS', False):
        additional_patterns.extend(mobile_urlpatterns)

    # Add debug patterns in development
    if settings.DEBUG:
        additional_patterns.extend(debug_urlpatterns)

    return additional_patterns


# Add conditional URLs to main patterns
urlpatterns.extend(get_conditional_urls())


# URL resolver helper functions
def get_product_url(product):
    """
    Get URL for a product
    """
    from django.urls import reverse
    return reverse('products:product_detail', kwargs={'slug': product.slug})


def get_category_url(category):
    """
    Get URL for a category
    """
    from django.urls import reverse
    return reverse('products:category_products', kwargs={'category_slug': category.slug})


def get_search_url(query=None, **filters):
    """
    Get search URL with optional query and filters
    """
    from django.urls import reverse
    from django.http import QueryDict

    url = reverse('products:search')
    if query or filters:
        params = QueryDict(mutable=True)
        if query:
            params['q'] = query
        for key, value in filters.items():
            if isinstance(value, list):
                params.setlist(key, value)
            else:
                params[key] = value
        url += f'?{params.urlencode()}'

    return url


# URL pattern validation
def validate_url_patterns():
    """
    Validate URL patterns for common issues
    """
    issues = []

    # Check for duplicate names
    names = []
    for pattern in urlpatterns:
        if hasattr(pattern, 'name') and pattern.name:
            if pattern.name in names:
                issues.append(f"Duplicate URL name: {pattern.name}")
            names.append(pattern.name)

    # Check for conflicting patterns
    patterns = [str(pattern.pattern) for pattern in urlpatterns]

    return issues


# Usage example in settings or management command:
# from products.urls import validate_url_patterns
# issues = validate_url_patterns()
# if issues:
#     print("URL Issues found:", issues)

# Documentation
"""
URL Organization:

1. Main URLs (/)
   - Product listing and search
   - Category navigation
   - Special collections

2. API URLs (/api/)
   - AJAX endpoints
   - JSON responses
   - Real-time features

3. Admin URLs (/admin/)
   - Staff-only operations
   - Bulk actions
   - Export functions

4. User Features
   - Wishlist management
   - Product comparison
   - Review system

View Performance:
- Use cache_page decorator for frequently accessed views
- Implement vary_on_headers for user-specific caching
- Consider using cached_urlpatterns for production

SEO Considerations:
- Implement Arabic URLs for better local SEO
- Use meaningful slug patterns
- Ensure proper URL structure hierarchy

Mobile Support:
- Separate mobile templates if needed
- Mobile-specific URL patterns
- Responsive design considerations
"""