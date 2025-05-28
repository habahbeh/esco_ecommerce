from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # قائمة التصنيفات - Category list
    path('categories/', views.CategoryListView.as_view(), name='category_list'),

    # تفاصيل التصنيف - Category detail
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),

    # تفاصيل المنتج - Product detail
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # البحث عن المنتجات - Product search
    path('search/', views.ProductSearchView.as_view(), name='product_search'),

    # العروض الخاصة - Special offers
    path('special-offers/', views.SpecialOffersView.as_view(), name='special_offers'),
]