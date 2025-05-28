from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    # عرض سلة التسوق - View shopping cart
    path('', views.CartView.as_view(), name='cart'),

    # إضافة منتج إلى السلة - Add product to cart
    path('add/<uuid:product_id>/', views.AddToCartView.as_view(), name='add_to_cart'),

    # تحديث كمية عنصر في السلة - Update item quantity in cart
    path('update/<int:item_id>/', views.UpdateCartView.as_view(), name='update_cart'),

    # إزالة عنصر من السلة - Remove item from cart
    path('remove/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),

    # الدفع - Checkout
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
]