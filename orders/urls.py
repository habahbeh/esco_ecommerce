from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # صفحة الشكر بعد إتمام الطلب - Thank you page after order completion
    path('thank-you/<uuid:order_id>/', views.ThankYouView.as_view(), name='thank_you'),

    # قائمة الطلبات للمستخدم - User's order list
    path('', views.OrderListView.as_view(), name='order_list'),

    # تفاصيل الطلب - Order details
    path('<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),

    # تتبع الطلب - Track order
    path('track/', views.TrackOrderView.as_view(), name='track_order'),

    # إلغاء الطلب - Cancel order
    path('cancel/<uuid:order_id>/', views.cancel_order, name='cancel_order'),

]