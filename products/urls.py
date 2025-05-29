from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product URLs
    path('', views.ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:category_slug>/', views.ProductListView.as_view(), name='category_products'),

    # Special pages
    path('special-offers/', views.special_offers_view, name='special_offers'),
    path('search/', views.ProductListView.as_view(), name='product_search'),

    # API endpoints
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('api/product/<int:product_id>/quick-view/', views.product_quick_view, name='product_quick_view'),

    # Wishlist URLs
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('api/wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('api/wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Comparison URLs
    path('compare/', views.comparison_view, name='comparison'),
    path('api/compare/add/', views.add_to_comparison, name='add_to_comparison'),

    # Review URLs
    path('api/product/<int:product_id>/review/', views.submit_review, name='submit_review'),
]