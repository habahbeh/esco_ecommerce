from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # تسجيل المستخدمين - User registration
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # الملف الشخصي - Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # سجل الطلبات - Order history
    path('orders/', views.OrderHistoryView.as_view(), name='order_history'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]