# cart/urls.py
from django.urls import path
from .views import (
    CartDetailView,
    AddToCartView,
    UpdateCartItemView,
    RemoveFromCartView,
    ClearCartView,
    ApplyCouponView,
    RemoveCouponView,
)

app_name = 'cart'

urlpatterns = [
    # Cart views
    path('', CartDetailView.as_view(), name='cart_detail'),
    path('add/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('update/<int:item_id>/', UpdateCartItemView.as_view(), name='update_cart_item'),
    path('remove/<int:item_id>/', RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('clear/', ClearCartView.as_view(), name='clear_cart'),

    # Coupon views
    path('apply-coupon/', ApplyCouponView.as_view(), name='apply_coupon'),
    path('remove-coupon/', RemoveCouponView.as_view(), name='remove_coupon'),
    path('', CartDetailView.as_view(), name='cart_detail'),
]