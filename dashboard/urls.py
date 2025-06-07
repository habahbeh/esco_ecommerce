from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from . import views
from dashboard.views.accounts import UserAddressSaveView, UserAddressGetView, UserAddressDeleteView, UserAddressListPartialView

app_name = 'dashboard'

urlpatterns = [
    # ========================= المصادقة وتسجيل الدخول =========================
    path('login/', views.dashboard_login, name='dashboard_login'),
    path('logout/', views.dashboard_logout, name='logout'),
    path('access-denied/', views.dashboard_access_denied, name='dashboard_access_denied'),

    # ========================= الصفحة الرئيسية =========================
    path('', views.DashboardHomeView.as_view(), name='dashboard_home'),

    # ========================= إدارة المستخدمين =========================
    # قائمة المستخدمين
    path('accounts/users/', views.UserListView.as_view(), name='dashboard_users'),
    # path('accounts/users/<str:user_id>/', views.UserDetailView.as_view(), name='dashboard_user_detail'),
    # path('accounts/users/create/', views.UserFormView.as_view(), name='dashboard_user_create'),
    # path('accounts/users/<str:user_id>/edit/', views.UserFormView.as_view(), name='dashboard_user_edit'),
    path('accounts/users/detail/<uuid:user_id>/', views.UserDetailView.as_view(), name='dashboard_user_detail'),
    path('accounts/users/create/', views.UserFormView.as_view(), name='dashboard_user_create'),
    path('accounts/users/edit/<uuid:user_id>/', views.UserFormView.as_view(), name='dashboard_user_edit'),
    path('accounts/users/<str:user_id>/delete/', views.UserDeleteView.as_view(), name='dashboard_user_delete'),

    path('accounts/users/<uuid:user_id>/addresses/', views.UserAddressListView.as_view(), name='dashboard_user_address_list'),
    path('accounts/users/<uuid:user_id>/addresses/create/', views.UserAddressFormView.as_view(), name='dashboard_user_address_create'),
    path('accounts/users/<uuid:user_id>/addresses/<int:address_id>/edit/', views.UserAddressFormView.as_view(),
         name='dashboard_user_address_edit'),

    path('accounts/users/address/save/', UserAddressSaveView.as_view(), name='dashboard_user_address_save'),
    path('accounts/users/address/get/', UserAddressGetView.as_view(), name='dashboard_user_address_get'),
    # path('accounts/users/address/delete/', UserAddressDeleteView.as_view(), name='dashboard_user_address_delete'),
    path('accounts/api/address/delete/', UserAddressDeleteView.as_view(), name='dashboard_user_address_delete'),
    path('accounts/users/<uuid:user_id>/addresses/<int:address_id>/delete/', views.UserAddressDeleteView.as_view(), name='dashboard_user_address_delete'),

    path('accounts/users/address/list-partial/', UserAddressListPartialView.as_view(),
         name='dashboard_user_address_list_partial'),

    path('accounts/users/<uuid:user_id>/reset-password/', views.UserResetPasswordView.as_view(), name='dashboard_user_reset_password'),

    # إدارة الأدوار
    path('accounts/roles/', views.RoleListView.as_view(), name='dashboard_roles'),
    path('accounts/roles/create/', views.RoleFormView.as_view(), name='dashboard_role_create'),
    path('accounts/roles/<str:role_id>/edit/', views.RoleFormView.as_view(), name='dashboard_role_edit'),
    path('accounts/roles/<str:role_id>/delete/', views.RoleDeleteView.as_view(), name='dashboard_role_delete'),

    # ========================= إدارة المنتجات =========================
    # قائمة المنتجات
    path('products/', views.ProductListView.as_view(), name='dashboard_products'),
    path('products/<str:product_id>/', views.ProductDetailView.as_view(), name='dashboard_product_detail'),
    path('products/create/', views.ProductFormView.as_view(), name='dashboard_product_create'),
    path('products/<str:product_id>/edit/', views.ProductFormView.as_view(), name='dashboard_product_edit'),
    path('products/<str:product_id>/delete/', views.ProductDeleteView.as_view(), name='dashboard_product_delete'),
    path('products/bulk-actions/', views.ProductBulkActionsView.as_view(), name='dashboard_product_bulk_actions'),

    # إدارة الفئات
    path('products/categories/', views.CategoryListView.as_view(), name='dashboard_categories'),
    path('products/categories/create/', views.CategoryFormView.as_view(), name='dashboard_category_create'),
    path('products/categories/<str:category_id>/edit/', views.CategoryFormView.as_view(),
         name='dashboard_category_edit'),
    path('products/categories/<str:category_id>/delete/', views.CategoryDeleteView.as_view(),
         name='dashboard_category_delete'),

    # إدارة العلامات التجارية
    path('products/brands/', views.BrandListView.as_view(), name='dashboard_brands'),
    path('products/brands/create/', views.BrandFormView.as_view(), name='dashboard_brand_create'),
    path('products/brands/<str:brand_id>/edit/', views.BrandFormView.as_view(), name='dashboard_brand_edit'),
    path('products/brands/<str:brand_id>/delete/', views.BrandDeleteView.as_view(), name='dashboard_brand_delete'),

    # إدارة الوسوم
    path('products/tags/', views.TagListView.as_view(), name='dashboard_tags'),
    path('products/tags/create/', views.TagFormView.as_view(), name='dashboard_tag_create'),
    path('products/tags/<str:tag_id>/edit/', views.TagFormView.as_view(), name='dashboard_tag_edit'),
    path('products/tags/<str:tag_id>/delete/', views.TagDeleteView.as_view(), name='dashboard_tag_delete'),

    # إدارة الخصومات
    path('products/discounts/', views.DiscountListView.as_view(), name='dashboard_discounts'),
    path('products/discounts/create/', views.DiscountFormView.as_view(), name='dashboard_discount_create'),
    path('products/discounts/<str:discount_id>/edit/', views.DiscountFormView.as_view(),
         name='dashboard_discount_edit'),
    path('products/discounts/<str:discount_id>/delete/', views.DiscountDeleteView.as_view(),
         name='dashboard_discount_delete'),

    # إدارة التقييمات
    path('products/reviews/', views.ReviewListView.as_view(), name='dashboard_reviews'),
    path('products/reviews/<str:review_id>/', views.ReviewDetailView.as_view(), name='dashboard_review_detail'),
    path('products/reviews/<str:review_id>/action/', views.review_action, name='dashboard_review_action'),

    # ========================= إدارة الطلبات =========================
    path('orders/', views.OrderListView.as_view(), name='dashboard_orders'),
    path('orders/<str:order_id>/', views.OrderDetailView.as_view(), name='dashboard_order_detail'),
    path('orders/create/', views.OrderCreateView.as_view(), name='dashboard_order_create'),
    path('orders/<str:order_id>/update-status/', views.OrderUpdateStatusView.as_view(),
         name='dashboard_order_update_status'),
    path('orders/<str:order_id>/update-payment-status/', views.OrderUpdatePaymentStatusView.as_view(),
         name='dashboard_order_update_payment_status'),
    path('orders/<str:order_id>/cancel/', views.OrderCancelView.as_view(), name='dashboard_order_cancel'),
    path('orders/<str:order_id>/print/', views.OrderPrintView.as_view(), name='dashboard_order_print'),
    path('orders/search/', views.order_search, name='dashboard_order_search'),
    path('orders/dashboard/', views.OrderDashboardView.as_view(), name='dashboard_order_dashboard'),
    path('orders/reports/', views.OrderReportsView.as_view(), name='dashboard_order_reports'),
    path('orders/export/', views.OrderExportView.as_view(), name='dashboard_order_export'),

    # ========================= إدارة عمليات الدفع =========================
    # إدارة جلسات الدفع
    path('checkout/sessions/', views.CheckoutSessionListView.as_view(), name='dashboard_checkout_sessions'),
    path('checkout/sessions/<str:session_id>/', views.CheckoutSessionDetailView.as_view(),
         name='dashboard_checkout_session_detail'),

    # إدارة طرق الشحن
    path('checkout/shipping-methods/', views.ShippingMethodListView.as_view(), name='dashboard_shipping_methods'),
    path('checkout/shipping-methods/create/', views.ShippingMethodFormView.as_view(),
         name='dashboard_shipping_method_create'),
    path('checkout/shipping-methods/<str:method_id>/edit/', views.ShippingMethodFormView.as_view(),
         name='dashboard_shipping_method_edit'),
    path('checkout/shipping-methods/<str:method_id>/delete/', views.ShippingMethodDeleteView.as_view(),
         name='dashboard_shipping_method_delete'),

    # إدارة طرق الدفع
    path('checkout/payment-methods/', views.PaymentMethodListView.as_view(), name='dashboard_payment_methods'),
    path('checkout/payment-methods/create/', views.PaymentMethodFormView.as_view(),
         name='dashboard_payment_method_create'),
    path('checkout/payment-methods/<str:method_id>/edit/', views.PaymentMethodFormView.as_view(),
         name='dashboard_payment_method_edit'),
    path('checkout/payment-methods/<str:method_id>/delete/', views.PaymentMethodDeleteView.as_view(),
         name='dashboard_payment_method_delete'),

    # إدارة كوبونات الخصم
    path('checkout/coupons/', views.CouponListView.as_view(), name='dashboard_coupons'),
    path('checkout/coupons/create/', views.CouponFormView.as_view(), name='dashboard_coupon_create'),
    path('checkout/coupons/<str:coupon_id>/edit/', views.CouponFormView.as_view(), name='dashboard_coupon_edit'),
    path('checkout/coupons/<str:coupon_id>/delete/', views.CouponDeleteView.as_view(), name='dashboard_coupon_delete'),

    # تقارير عملية الدفع
    path('checkout/reports/', views.CheckoutReportsView.as_view(), name='dashboard_checkout_reports'),

    # ========================= إدارة المدفوعات =========================
    # المعاملات المالية
    path('payment/transactions/', views.TransactionListView.as_view(), name='dashboard_transaction_list'),
    path('payment/transactions/<str:pk>/', views.TransactionDetailView.as_view(), name='dashboard_transaction_detail'),
    path('payment/transactions/<str:pk>/update-status/', views.UpdateTransactionStatusView.as_view(),
         name='dashboard_transaction_update_status'),
    path('payment/transactions/create/', views.TransactionCreateView.as_view(), name='dashboard_transaction_create'),

    # المدفوعات
    path('payment/payments/', views.PaymentListView.as_view(), name='dashboard_payment_list'),
    path('payment/payments/<str:pk>/', views.PaymentDetailView.as_view(), name='dashboard_payment_detail'),
    path('payment/payments/<str:pk>/update-status/', views.PaymentUpdateStatusView.as_view(),
         name='dashboard_payment_update_status'),
    path('payment/payments/create/', views.PaymentCreateView.as_view(), name='dashboard_payment_create'),

    # طلبات استرداد المبالغ
    path('payment/refunds/', views.RefundListView.as_view(), name='dashboard_refund_list'),
    path('payment/refunds/<str:pk>/', views.RefundDetailView.as_view(), name='dashboard_refund_detail'),
    path('payment/refunds/create/<str:payment_id>/', views.RefundCreateView.as_view(), name='dashboard_refund_create'),
    path('payment/refunds/<str:pk>/update-status/', views.RefundUpdateStatusView.as_view(),
         name='dashboard_refund_update_status'),

    # لوحة معلومات المدفوعات
    path('payment/dashboard/', views.PaymentDashboardView.as_view(), name='dashboard_payment_dashboard'),

    # ========================= التقارير والإحصائيات =========================
    path('reports/', views.ReportIndexView.as_view(), name='dashboard_reports'),
    path('reports/sales/', views.SalesReportView.as_view(), name='dashboard_sales_report'),
    path('reports/products/', views.ProductReportView.as_view(), name='dashboard_product_report'),
    path('reports/customers/', views.CustomerReportView.as_view(), name='dashboard_customer_report'),
    path('reports/inventory/', views.InventoryReportView.as_view(), name='dashboard_inventory_report'),
    path('reports/revenue/', views.RevenueReportView.as_view(), name='dashboard_revenue_report'),
    path('reports/tax/', views.TaxReportView.as_view(), name='dashboard_tax_report'),
    path('reports/export/', views.ExportReportView.as_view(), name='dashboard_export_report'),
    path('reports/export-data/', views.ExportReportDataView.as_view(), name='dashboard_export_report_data'),

    # ========================= الإشعارات =========================
    path('notifications/', views.NotificationAPIView.as_view(), name='dashboard_notifications'),

    # ========================= الإعدادات =========================
    # إعدادات الموقع
    path('settings/site/', views.SiteSettingsView.as_view(), name='dashboard_site_settings'),
    path('settings/email/', views.EmailSettingsView.as_view(), name='dashboard_email_settings'),
    path('settings/payment-gateways/', views.PaymentGatewaySettingsView.as_view(),
         name='dashboard_payment_gateway_settings'),
    path('settings/payment-gateways/<str:gateway_id>/', views.PaymentGatewaySettingsView.as_view(),
         name='dashboard_payment_gateway_settings'),
    path('settings/shipping/', views.ShippingSettingsView.as_view(), name='dashboard_shipping_settings'),
    path('settings/tax/', views.TaxSettingsView.as_view(), name='dashboard_tax_settings'),
    path('settings/currency/', views.CurrencySettingsView.as_view(), name='dashboard_currency_settings'),
    path('settings/language/', views.LanguageSettingsView.as_view(), name='dashboard_language_settings'),
    path('settings/maintenance/', views.MaintenanceModeView.as_view(), name='dashboard_maintenance_mode'),
    path('settings/cache/', views.CacheManagementView.as_view(), name='dashboard_cache_management'),
    path('settings/backup/', views.BackupSettingsView.as_view(), name='dashboard_backup_settings'),
    path('settings/api/', views.APISettingsView.as_view(), name='dashboard_api_settings'),
    path('settings/social-media/', views.SocialMediaSettingsView.as_view(), name='dashboard_social_media_settings'),
    path('settings/security/', views.SecuritySettingsView.as_view(), name='dashboard_security_settings'),

    # إعدادات لوحة التحكم
    path('settings/dashboard/', views.DashboardSettingsView.as_view(), name='dashboard_dashboard_settings'),
    path('settings/widgets/', views.WidgetSettingsView.as_view(), name='dashboard_widget_settings'),

    # ========================= واجهات برمجة التطبيقات API =========================
    path('api/stats/', views.DashboardStatsAPIView.as_view(), name='dashboard_stats_api'),
    path('api/chart-data/', views.ChartDataAPIView.as_view(), name='dashboard_chart_data'),
    path('api/users/autocomplete/', views.UserAutocompleteAPIView.as_view(), name='dashboard_user_autocomplete'),
    path('api/products/autocomplete/', views.ProductAutocompleteAPIView.as_view(),
         name='dashboard_product_autocomplete'),
    path('api/orders/autocomplete/', views.OrderAutocompleteAPIView.as_view(), name='dashboard_order_autocomplete'),
    path('api/order-status-update/', views.OrderUpdateStatusView.as_view(), name='dashboard_order_status_update_api'),
    path('api/product-stock-update/', views.ProductStockUpdateAPIView.as_view(),
         name='dashboard_product_stock_update_api'),
    path('api/widget-data/', views.DashboardWidgetDataAPIView.as_view(), name='dashboard_widget_data_api'),
    path('api/payment-chart/', views.PaymentAPIView.as_view(), name='dashboard_payment_chart_api'),
]