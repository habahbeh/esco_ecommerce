# dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # لوحة التحكم الرئيسية - Dashboard home
    path('', views.DashboardView.as_view(), name='index'),

    # ===== إدارة المنتجات ===== #
    # ===== Product Management ===== #
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<uuid:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<uuid:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<uuid:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('products/<uuid:pk>/review/', views.ProductReviewView.as_view(), name='product_review'),

    # متغيرات المنتج - Product variants
    path('products/<uuid:product_id>/variants/create/', views.ProductVariantCreateView.as_view(),
         name='variant_create'),
    path('products/variants/<int:pk>/update/', views.ProductVariantUpdateView.as_view(), name='variant_update'),
    path('products/variants/<int:pk>/delete/', views.ProductVariantDeleteView.as_view(), name='variant_delete'),

    # صور المنتج - Product images
    path('products/<uuid:product_id>/images/upload/', views.ProductImageUploadView.as_view(), name='image_upload'),
    path('products/images/<int:pk>/delete/', views.ProductImageDeleteView.as_view(), name='image_delete'),

    # ===== إدارة الفئات ===== #
    # ===== Category Management ===== #
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # ===== إدارة الخصومات ===== #
    # ===== Discount Management ===== #
    path('discounts/', views.DiscountListView.as_view(), name='discount_list'),
    path('discounts/create/', views.DiscountCreateView.as_view(), name='discount_create'),
    path('discounts/<int:pk>/update/', views.DiscountUpdateView.as_view(), name='discount_update'),
    path('discounts/<int:pk>/delete/', views.DiscountDeleteView.as_view(), name='discount_delete'),

    # ===== إدارة الطلبات ===== #
    # ===== Order Management ===== #
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<uuid:pk>/update-status/', views.OrderUpdateStatusView.as_view(), name='order_update_status'),

    # ===== التصدير والاستيراد ===== #
    # ===== Export and Import ===== #
    path('products/export/', views.ExportProductsView.as_view(), name='export_products'),
    path('products/import/', views.ImportProductsView.as_view(), name='import_products'),
]