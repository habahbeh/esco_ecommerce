# File: products/views/__init__.py
"""
Products views package
Organizes all product-related views into logical modules

This package provides a clean structure for product views:
- base_views: Base classes and mixins
- product_views: Core product views (list, detail, category)
- api_views: AJAX/API endpoints
- wishlist_views: Wishlist functionality
- comparison_views: Product comparison
- review_views: Product reviews and ratings
- search_views: Search functionality
- admin_views: Admin-specific views
- export_views: Data export functionality
- utils: Utility functions and decorators
"""

# Import all view classes and functions for easy access
from .base_views import (
    # Mixins
    OptimizedQueryMixin,
    FilterMixin,
    BreadcrumbMixin,
    PaginationMixin,

    # Base classes
    BaseProductListView,
    BaseProductDetailView,
    CachedListView,
    AdminRequiredMixin,
)

from .product_views import (
    # عروض التصنيفات (كانت سابقاً في category_views.py)
    CategoryListView,

    # عروض المنتجات الأساسية
    ProductListView,
    ProductDetailView,

    # عروض المنتجات المتخصصة
    SpecialOffersView,
    TagProductsView,
    BrandProductsView,
    NewProductsView,
    FeaturedProductsView,
    BestSellersView,
    ProductVariantDetailView
)

from .api_views import (
    # API view classes
    BaseAPIView,
    SearchSuggestionsView,
    ProductQuickViewView,
    ProductVariantDetailsView,
    ProductFiltersView,
    IncrementViewsView,
    Product360View,
    ProductStockCheckView,

    # Function views
    search_suggestions,
    product_quick_view,
    get_variant_details,
    increment_category_views,
    product_360_view,
)

from .wishlist_views import (
    # Wishlist view classes
    WishlistView,
    AddToWishlistView,
    RemoveFromWishlistView,
    ToggleWishlistView,
    ClearWishlistView,
    WishlistStatusView,
    WishlistProductsView,
)

from .comparison_views import (
    # Comparison view classes
    ComparisonView,
    AddToComparisonView,
    RemoveFromComparisonView,
    ClearComparisonView,
    ComparisonStatusView,
)

from .review_views import (
    # Review view classes
    ProductReviewListView,
    SubmitReviewView,
    VoteReviewHelpfulView,
    ReportReviewView,
    UserReviewsView,
    EditReviewView,
    DeleteReviewView,
)

from .search_views import (
    # Search view classes
    SearchView,
    AdvancedSearchView,
    SearchSuggestionsPageView,
    QuickSearchView,

    # Function views
    search_suggestions,
    quick_search_simple,
    advanced_search_view,
)

from .admin_views import (
    # Admin view classes
    AdminDashboardView,
    ProductBulkEditView,
    ReviewModerationView,
    ReviewModerationAPIView,
    ProductAnalyticsView,
)

from .export_views import (
    # Export view classes
    ExportProductsView,
    ExportReviewsView,
)

from .utils import (
    # Decorators
    ajax_required,
    rate_limit,
    cache_result,

    # Utility functions
    get_client_ip,
    validate_price,
    validate_integer,
    clean_search_query,
    build_search_filters,
    paginate_queryset,
    get_page_range,
    format_currency,
    calculate_discount,
    get_stock_status,
    generate_sku,
    validate_image_file,
    get_breadcrumbs,
    track_user_activity,
    get_popular_products,
    get_recommended_products,

    # Classes
    PerformanceMonitor,
)



# Version info
__version__ = '1.0.0'
__author__ = 'Products Team'

# All exportable items
__all__ = [
    # Base views and mixins
    'CachedMixin',
    'OptimizedQueryMixin',
    'FilterMixin',
    'BreadcrumbMixin',
    'PaginationMixin',
    'BaseProductListView',
    'BaseProductDetailView',
    'CachedListView',
    'AdminRequiredMixin',

    # Product views
    'ProductListView',
    'ProductDetailView',
    'CategoryListView',
    'CategoryDetailView',
    'SpecialOffersView',
    'TagProductsView',
    'BrandProductsView',
    'NewProductsView',
    'FeaturedProductsView',
    'BestSellersView',
    'ProductVariantDetailView',

    # API views
    'BaseAPIView',
    'SearchSuggestionsView',
    'ProductQuickViewView',
    'ProductVariantDetailsView',
    'ProductFiltersView',
    'IncrementViewsView',
    'Product360View',
    'ProductStockCheckView',
    'search_suggestions',
    'product_quick_view',
    'get_variant_details',
    'increment_category_views',
    'product_360_view',

    # Wishlist views
    'WishlistView',
    'AddToWishlistView',
    'RemoveFromWishlistView',
    'ToggleWishlistView',
    'ClearWishlistView',
    'WishlistStatusView',
    'WishlistProductsView',

    # Comparison views
    'ComparisonView',
    'AddToComparisonView',
    'RemoveFromComparisonView',
    'ClearComparisonView',
    'ComparisonStatusView',

    # Review views
    'ProductReviewListView',
    'SubmitReviewView',
    'VoteReviewHelpfulView',
    'ReportReviewView',
    'UserReviewsView',
    'EditReviewView',
    'DeleteReviewView',

    # Search views
    'SearchView',
    'AdvancedSearchView',
    'SearchSuggestionsPageView',
    'QuickSearchView',
    'search_suggestions',
    'quick_search_simple',
    'advanced_search_view',

    # Admin views
    'AdminDashboardView',
    'ProductBulkEditView',
    'ReviewModerationView',
    'ReviewModerationAPIView',
    'ProductAnalyticsView',

    # Export views
    'ExportProductsView',
    'ExportReviewsView',

    # Utils
    'ajax_required',
    'rate_limit',
    'cache_result',
    'get_client_ip',
    'validate_price',
    'validate_integer',
    'clean_search_query',
    'build_search_filters',
    'paginate_queryset',
    'get_page_range',
    'format_currency',
    'calculate_discount',
    'get_stock_status',
    'generate_sku',
    'validate_image_file',
    'get_breadcrumbs',
    'track_user_activity',
    'get_popular_products',
    'get_recommended_products',
    'PerformanceMonitor',
]

# Convenience imports for URLs
product_list = ProductListView.as_view()
product_detail = ProductDetailView.as_view()
category_list = CategoryListView.as_view()
category_detail = CategoryDetailView.as_view()
search_results = SearchView.as_view()
advanced_search = AdvancedSearchView.as_view()
special_offers = SpecialOffersView.as_view()
new_products = NewProductsView.as_view()
featured_products = FeaturedProductsView.as_view()
best_sellers = BestSellersView.as_view()

# View mappings for easy reference
VIEW_MAPPINGS = {
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
    'wishlist': WishlistView,
    'comparison': ComparisonView,
    'admin_dashboard': AdminDashboardView,
}


def get_view_class(view_name: str):
    """
    Get view class by name

    Args:
        view_name: Name of the view

    Returns:
        View class or None if not found

    Example:
        >>> from products.views import get_view_class
        >>> ProductListView = get_view_class('product_list')
    """
    return VIEW_MAPPINGS.get(view_name)


def get_available_views():
    """
    Get list of all available view names

    Returns:
        List of view names
    """
    return list(VIEW_MAPPINGS.keys())


# Performance and monitoring
def get_view_performance_stats():
    """
    Get performance statistics for all views
    This would typically integrate with monitoring systems
    """
    from django.core.cache import cache
    from django.utils import timezone

    stats = {}
    today = timezone.now().date()

    for view_name in VIEW_MAPPINGS.keys():
        cache_key = f'view_performance:{view_name}:{today}'
        performance_data = cache.get(cache_key, {})

        if performance_data:
            avg_time = (performance_data.get('total_time', 0) /
                        performance_data.get('total_requests', 1))
            stats[view_name] = {
                'requests': performance_data.get('total_requests', 0),
                'avg_time': round(avg_time, 3),
                'max_time': performance_data.get('max_time', 0),
                'min_time': performance_data.get('min_time', 0),
            }

    return stats


# Module documentation
def get_module_info():
    """
    Get information about this module
    """
    return {
        'name': 'products.views',
        'version': __version__,
        'author': __author__,
        'description': 'Comprehensive views package for product management',
        'modules': [
            'base_views - Base classes and mixins',
            'product_views - Core product functionality',
            'api_views - AJAX/API endpoints',
            'wishlist_views - Wishlist management',
            'comparison_views - Product comparison',
            'review_views - Review and rating system',
            'search_views - Search functionality',
            'admin_views - Administrative tools',
            'export_views - Data export utilities',
            'utils - Helper functions and decorators'
        ],
        'total_views': len(__all__),
        'class_based_views': len([item for item in __all__ if item.endswith('View')]),
        'function_based_views': len(
            [item for item in __all__ if not item.endswith('View') and not item.startswith('get_')]),
    }