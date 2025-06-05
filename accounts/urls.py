# accounts/urls.py
"""
مسارات تطبيق الحسابات
Accounts app URLs
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = []
# urlpatterns = [
#     # تسجيل المستخدمين - User registration
#     path('register/', views.RegisterView.as_view(), name='register'),
#     path('register/done/', views.RegisterDoneView.as_view(), name='register_done'),
#     path('verify-email/<str:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
#     path('resend-verification/', views.ResendVerificationEmailView.as_view(), name='resend_verification'),
#
#     # تسجيل الدخول والخروج - Login and logout
#     path('login/', views.LoginView.as_view(), name='login'),
#     path('logout/', views.LogoutView.as_view(), name='logout'),
#
#     # استعادة كلمة المرور - Password reset
#     path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
#     path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
#     path('password-reset/confirm/<str:token>/', views.CustomPasswordResetConfirmView.as_view(),
#          name='password_reset_confirm'),
#     path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
#
#     # الملف الشخصي - Profile
#     path('profile/', views.ProfileView.as_view(), name='profile'),
#     path('profile/password/', views.ChangePasswordView.as_view(), name='change_password'),
#     path('profile/notifications/', views.NotificationPreferencesView.as_view(), name='notification_preferences'),
#
#     # العناوين - Addresses
#     path('addresses/', views.AddressListView.as_view(), name='address_list'),
#     path('addresses/add/', views.AddressCreateView.as_view(), name='address_add'),
#     path('addresses/<int:pk>/edit/', views.AddressUpdateView.as_view(), name='address_edit'),
#     path('addresses/<int:pk>/delete/', views.AddressDeleteView.as_view(), name='address_delete'),
#
#     # سجل الطلبات - Order history
#     path('orders/', views.OrderHistoryView.as_view(), name='order_history'),
#     path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
#
#     # لوحة تحكم المشرفين - Admin dashboard
#     path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
#
#     # إدارة المستخدمين - User management
#     path('admin/users/', views.UserListView.as_view(), name='admin_user_list'),
#     path('admin/users/add/', views.UserCreateView.as_view(), name='admin_user_add'),
#     path('admin/users/<uuid:pk>/', views.UserDetailView.as_view(), name='admin_user_detail'),
#     path('admin/users/<uuid:pk>/edit/', views.UserUpdateView.as_view(), name='admin_user_edit'),
#     path('admin/users/<uuid:pk>/reset-password/', views.UserPasswordResetView.as_view(),
#          name='admin_user_reset_password'),
#     path('admin/users/<uuid:pk>/toggle-active/', views.UserActivateDeactivateView.as_view(),
#          name='admin_user_toggle_active'),
#     path('admin/users/<uuid:pk>/verify/', views.UserVerifyView.as_view(), name='admin_user_verify'),
#
#     # إدارة الأدوار - Role management
#     path('admin/roles/', views.RoleListView.as_view(), name='admin_role_list'),
#     path('admin/roles/add/', views.RoleCreateView.as_view(), name='admin_role_add'),
#     path('admin/roles/<int:pk>/edit/', views.RoleUpdateView.as_view(), name='admin_role_edit'),
#     path('admin/roles/<int:pk>/delete/', views.RoleDeleteView.as_view(), name='admin_role_delete'),
#
#     # سجل النشاطات - Activity log
#     path('admin/activities/', views.UserActivityListView.as_view(), name='admin_activity_list'),
# ]