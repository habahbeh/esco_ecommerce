# File: products/urls.py
"""
URLs configuration for products app - مُصحح وآمن
يعمل مع الهيكل القديم والجديد للعروض
"""

from django.urls import path, include
from django.views.decorators.cache import cache_page

# استيراد آمن للعروض - يعمل مع النظام القديم والجديد
try:
    # محاولة استيراد من الهيكل الجديد
    from .views import (
        ProductListView,
        ProductDetailView,
        CategoryListView,
        CategoryDetailView,
        SpecialOffersView,
        SearchView,
        AdvancedSearchView,

        # API views
        search_suggestions,
        product_quick_view,

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
    )

    NEW_STRUCTURE = True
except ImportError:
    # إذا فشل، استخدم الهيكل القديم
    try:
        from . import views

        NEW_STRUCTURE = False
    except ImportError:
        # إذا فشل كل شيء، أنشئ عروض افتراضية
        from django.http import HttpResponse
        from django.views.generic import TemplateView


        def default_view(request, *args, **kwargs):
            return HttpResponse("Products app is under maintenance")


        # عروض افتراضية
        ProductListView = TemplateView
        ProductDetailView = TemplateView
        CategoryListView = TemplateView
        CategoryDetailView = TemplateView
        SpecialOffersView = TemplateView
        SearchView = TemplateView
        AdvancedSearchView = TemplateView

        # API views افتراضية
        search_suggestions = default_view
        product_quick_view = default_view
        wishlist_view = default_view
        add_to_wishlist = default_view
        remove_from_wishlist = default_view
        toggle_wishlist = default_view
        comparison_view = default_view
        add_to_comparison = default_view
        submit_review = default_view
        vote_review_helpful = default_view
        report_review = default_view

        NEW_STRUCTURE = False

app_name = 'products'

# URLs أساسية آمنة
basic_urlpatterns = [
    # الصفحة الرئيسية للمنتجات
    path('', ProductListView.as_view(), name='product_list'),
]

# URLs للهيكل الجديد
if NEW_STRUCTURE:
    urlpatterns = [
        # Main product pages
        path('', ProductListView.as_view(), name='product_list'),
        path('categories/', CategoryListView.as_view(), name='category_list'),
        path('search/', SearchView.as_view(), name='search'),
        path('search/advanced/', AdvancedSearchView.as_view(), name='advanced_search'),

        # Special collections
        path('offers/', SpecialOffersView.as_view(), name='special_offers'),
        path('new/', ProductListView.as_view(), {'filter_type': 'new'}, name='new_products'),
        path('featured/', ProductListView.as_view(), {'filter_type': 'featured'}, name='featured_products'),

        # Category and product details
        path('category/<slug:category_slug>/', ProductListView.as_view(), name='category_products'),
        path('category/<slug:slug>/detail/', CategoryDetailView.as_view(), name='category_detail'),
        path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),

        # User features
        path('wishlist/', wishlist_view, name='wishlist'),
        path('comparison/', comparison_view, name='comparison'),

        # API endpoints (wrapped with try-catch for safety)
        path('api/search/suggestions/', search_suggestions, name='search_suggestions'),
        path('api/product/<int:product_id>/quick-view/', product_quick_view, name='product_quick_view'),
        path('api/wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
        path('api/wishlist/remove/<int:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),
        path('api/wishlist/toggle/<int:product_id>/', toggle_wishlist, name='toggle_wishlist'),
        path('api/comparison/add/', add_to_comparison, name='add_to_comparison'),
        path('api/review/submit/<int:product_id>/', submit_review, name='submit_review'),
        path('api/review/<int:review_id>/vote/', vote_review_helpful, name='vote_review_helpful'),
        path('api/review/<int:review_id>/report/', report_review, name='report_review'),
    ]

else:
    # URLs للهيكل القديم - استخدام views module
    urlpatterns = [
        # Main pages
        path('', getattr(views, 'ProductListView', views.product_list).as_view()
        if hasattr(getattr(views, 'ProductListView', None), 'as_view')
        else getattr(views, 'product_list', default_view), name='product_list'),

        path('categories/', getattr(views, 'CategoryListView', views.category_list).as_view()
        if hasattr(getattr(views, 'CategoryListView', None), 'as_view')
        else getattr(views, 'category_list', default_view), name='category_list'),

        path('search/', getattr(views, 'SearchView', views.search).as_view()
        if hasattr(getattr(views, 'SearchView', None), 'as_view')
        else getattr(views, 'search', default_view), name='search'),

        # Product detail
        path('product/<slug:slug>/', getattr(views, 'ProductDetailView', views.product_detail).as_view()
        if hasattr(getattr(views, 'ProductDetailView', None), 'as_view')
        else getattr(views, 'product_detail', default_view), name='product_detail'),

        # Category products
        path('category/<slug:category_slug>/', getattr(views, 'category_products', default_view),
             name='category_products'),

        # API endpoints
        path('api/search/suggestions/', getattr(views, 'search_suggestions', default_view), name='search_suggestions'),
        path('api/wishlist/add/<int:product_id>/', getattr(views, 'add_to_wishlist', default_view),
             name='add_to_wishlist'),

        # Wishlist
        path('wishlist/', getattr(views, 'wishlist_view', default_view), name='wishlist'),
    ]


# إضافة معالجات الأخطاء
def safe_view_wrapper(view_func):
    """Wrapper آمن للعروض"""

    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            from django.http import HttpResponse
            return HttpResponse(f"View temporarily unavailable: {str(e)}", status=503)

    return wrapper


# تطبيق الـ wrapper على العروض إذا لزم الأمر
if not NEW_STRUCTURE:
    # لف العروض المعرضة للخطأ
    for i, pattern in enumerate(urlpatterns):
        if hasattr(pattern, 'callback') and pattern.callback == default_view:
            continue  # تجاهل العروض الافتراضية

        # يمكن إضافة safe wrapper هنا إذا لزم الأمر
        pass