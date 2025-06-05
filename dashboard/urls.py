# dashboard/urls.py
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'dashboard'

# المسارات الرئيسية للوحة التحكم
main_urlpatterns = [
    # الصفحة الرئيسية للوحة التحكم
    path('', views.DashboardView.as_view(), name='index'),
    # مسارات الإشعارات
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-read/<uuid:pk>/', views.MarkNotificationAsReadView.as_view(),
         name='mark_notification_read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsAsReadView.as_view(),
         name='mark_all_notifications_read'),
    # إعدادات المستخدم الخاصة بلوحة التحكم
    path('settings/', views.DashboardSettingsView.as_view(), name='dashboard_settings'),
    # البحث العام
    path('search/', views.GlobalSearchView.as_view(), name='global_search'),
]

# مسارات إدارة المستخدمين والأدوار
user_urlpatterns = [
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<uuid:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<uuid:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('users/<uuid:pk>/activate/', views.UserActivateView.as_view(), name='user_activate'),
    path('users/<uuid:pk>/deactivate/', views.UserDeactivateView.as_view(), name='user_deactivate'),
    path('users/<uuid:pk>/reset-password/', views.UserResetPasswordView.as_view(), name='user_reset_password'),

    # إدارة الأدوار والصلاحيات
    path('roles/', views.RoleListView.as_view(), name='role_list'),
    path('roles/create/', views.RoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='role_detail'),
    path('roles/<int:pk>/update/', views.RoleUpdateView.as_view(), name='role_update'),
    path('roles/<int:pk>/delete/', views.RoleDeleteView.as_view(), name='role_delete'),

    # إدارة العناوين
    path('users/<uuid:user_id>/addresses/', views.UserAddressListView.as_view(), name='user_address_list'),
    path('users/<uuid:user_id>/addresses/create/', views.UserAddressCreateView.as_view(), name='user_address_create'),
    path('addresses/<int:pk>/update/', views.UserAddressUpdateView.as_view(), name='user_address_update'),
    path('addresses/<int:pk>/delete/', views.UserAddressDeleteView.as_view(), name='user_address_delete'),

    # نشاط المستخدمين
    path('user-activity/', views.UserActivityListView.as_view(), name='user_activity_list'),
]

# مسارات إدارة المنتجات
product_urlpatterns = [
    # إدارة المنتجات
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<uuid:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<uuid:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<uuid:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('products/<uuid:pk>/review/', views.ProductReviewView.as_view(), name='product_review'),

    # إدارة متغيرات المنتجات
    path('products/<uuid:product_id>/variants/create/', views.ProductVariantCreateView.as_view(),
         name='variant_create'),
    path('products/variants/<int:pk>/update/', views.ProductVariantUpdateView.as_view(), name='variant_update'),
    path('products/variants/<int:pk>/delete/', views.ProductVariantDeleteView.as_view(), name='variant_delete'),

    # إدارة صور المنتجات
    path('products/<uuid:product_id>/images/upload/', views.ProductImageUploadView.as_view(), name='image_upload'),
    path('products/images/<int:pk>/delete/', views.ProductImageDeleteView.as_view(), name='image_delete'),
    path('products/images/reorder/', views.ProductImageReorderView.as_view(), name='image_reorder'),

    # إدارة تقييمات المنتجات
    path('products/reviews/', views.ProductReviewListView.as_view(), name='product_review_list'),
    path('products/reviews/<int:pk>/approve/', views.ProductReviewApproveView.as_view(), name='product_review_approve'),
    path('products/reviews/<int:pk>/reject/', views.ProductReviewRejectView.as_view(), name='product_review_reject'),
    path('products/reviews/<int:pk>/delete/', views.ProductReviewDeleteView.as_view(), name='product_review_delete'),

    # إدارة الفئات
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # إدارة العلامات التجارية
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brands/<int:pk>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('brands/<int:pk>/update/', views.BrandUpdateView.as_view(), name='brand_update'),
    path('brands/<int:pk>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),

    # إدارة الوسوم
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tags/create/', views.TagCreateView.as_view(), name='tag_create'),
    path('tags/<int:pk>/update/', views.TagUpdateView.as_view(), name='tag_update'),
    path('tags/<int:pk>/delete/', views.TagDeleteView.as_view(), name='tag_delete'),

    # إدارة خصائص المنتجات
    path('attributes/', views.ProductAttributeListView.as_view(), name='attribute_list'),
    path('attributes/create/', views.ProductAttributeCreateView.as_view(), name='attribute_create'),
    path('attributes/<int:pk>/update/', views.ProductAttributeUpdateView.as_view(), name='attribute_update'),
    path('attributes/<int:pk>/delete/', views.ProductAttributeDeleteView.as_view(), name='attribute_delete'),

    # تعيينات مراجعة المنتجات
    path('review-assignments/', views.ProductReviewAssignmentListView.as_view(), name='review_assignment_list'),
    path('review-assignments/create/', views.ProductReviewAssignmentCreateView.as_view(),
         name='review_assignment_create'),
    path('review-assignments/<uuid:pk>/', views.ProductReviewAssignmentDetailView.as_view(),
         name='review_assignment_detail'),
    path('review-assignments/<uuid:pk>/complete/', views.ProductReviewAssignmentCompleteView.as_view(),
         name='review_assignment_complete'),

    # تصدير واستيراد المنتجات
    path('products/export/', views.ExportProductsView.as_view(), name='export_products'),
    path('products/import/', views.ImportProductsView.as_view(), name='import_products'),
]

# مسارات إدارة الطلبات والمبيعات
order_urlpatterns = [
    # إدارة الطلبات
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<uuid:pk>/update-status/', views.OrderUpdateStatusView.as_view(), name='order_update_status'),
    path('orders/<uuid:pk>/delete/', views.OrderDeleteView.as_view(), name='order_delete'),
    path('orders/<uuid:pk>/invoice/', views.OrderInvoiceView.as_view(), name='order_invoice'),
    path('orders/<uuid:pk>/shipping-label/', views.OrderShippingLabelView.as_view(), name='order_shipping_label'),

    # إدارة عناصر الطلبات
    path('orders/<uuid:order_id>/items/<int:pk>/update/', views.OrderItemUpdateView.as_view(),
         name='order_item_update'),
    path('orders/<uuid:order_id>/items/<int:pk>/delete/', views.OrderItemDeleteView.as_view(),
         name='order_item_delete'),

    # إدارة سلات التسوق
    path('carts/', views.CartListView.as_view(), name='cart_list'),
    path('carts/<uuid:pk>/', views.CartDetailView.as_view(), name='cart_detail'),
    path('carts/<uuid:pk>/delete/', views.CartDeleteView.as_view(), name='cart_delete'),
    path('carts/<uuid:pk>/convert-to-order/', views.CartConvertToOrderView.as_view(), name='cart_convert_to_order'),

    # إدارة المدفوعات
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/<uuid:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/<uuid:pk>/refund/', views.PaymentRefundView.as_view(), name='payment_refund'),

    # إدارة المعاملات المالية
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<uuid:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),

    # إدارة عمليات الاسترداد
    path('refunds/', views.RefundListView.as_view(), name='refund_list'),
    path('refunds/<uuid:pk>/', views.RefundDetailView.as_view(), name='refund_detail'),
    path('refunds/<uuid:pk>/approve/', views.RefundApproveView.as_view(), name='refund_approve'),
    path('refunds/<uuid:pk>/reject/', views.RefundRejectView.as_view(), name='refund_reject'),

    # إدارة الخصومات والكوبونات
    path('discounts/', views.DiscountListView.as_view(), name='discount_list'),
    path('discounts/create/', views.DiscountCreateView.as_view(), name='discount_create'),
    path('discounts/<int:pk>/', views.DiscountDetailView.as_view(), name='discount_detail'),
    path('discounts/<int:pk>/update/', views.DiscountUpdateView.as_view(), name='discount_update'),
    path('discounts/<int:pk>/delete/', views.DiscountDeleteView.as_view(), name='discount_delete'),
]

# مسارات جلسات الدفع
checkout_urlpatterns = [
    path('checkout-sessions/', views.CheckoutSessionListView.as_view(), name='checkout_session_list'),
    path('checkout-sessions/<uuid:pk>/', views.CheckoutSessionDetailView.as_view(), name='checkout_session_detail'),
    path('checkout-sessions/<uuid:pk>/delete/', views.CheckoutSessionDeleteView.as_view(),
         name='checkout_session_delete'),

    # إدارة طرق الدفع
    path('payment-methods/', views.PaymentMethodListView.as_view(), name='payment_method_list'),
    path('payment-methods/create/', views.PaymentMethodCreateView.as_view(), name='payment_method_create'),
    path('payment-methods/<int:pk>/', views.PaymentMethodDetailView.as_view(), name='payment_method_detail'),
    path('payment-methods/<int:pk>/update/', views.PaymentMethodUpdateView.as_view(), name='payment_method_update'),
    path('payment-methods/<int:pk>/delete/', views.PaymentMethodDeleteView.as_view(), name='payment_method_delete'),

    # إدارة طرق الشحن
    path('shipping-methods/', views.ShippingMethodListView.as_view(), name='shipping_method_list'),
    path('shipping-methods/create/', views.ShippingMethodCreateView.as_view(), name='shipping_method_create'),
    path('shipping-methods/<int:pk>/', views.ShippingMethodDetailView.as_view(), name='shipping_method_detail'),
    path('shipping-methods/<int:pk>/update/', views.ShippingMethodUpdateView.as_view(), name='shipping_method_update'),
    path('shipping-methods/<int:pk>/delete/', views.ShippingMethodDeleteView.as_view(), name='shipping_method_delete'),
]

# مسارات التقارير والإحصائيات
report_urlpatterns = [
    path('reports/', views.ReportIndexView.as_view(), name='report_index'),
    path('reports/sales/', views.SalesReportView.as_view(), name='sales_report'),
    path('reports/products/', views.ProductReportView.as_view(), name='product_report'),
    path('reports/customers/', views.CustomerReportView.as_view(), name='customer_report'),
    path('reports/inventory/', views.InventoryReportView.as_view(), name='inventory_report'),
    path('reports/revenue/', views.RevenueReportView.as_view(), name='revenue_report'),
    path('reports/taxes/', views.TaxReportView.as_view(), name='tax_report'),
    path('reports/export/', views.ExportReportView.as_view(), name='export_report'),

    # إدارة ودجات لوحة التحكم
    path('widgets/', views.DashboardWidgetListView.as_view(), name='widget_list'),
    path('widgets/create/', views.DashboardWidgetCreateView.as_view(), name='widget_create'),
    path('widgets/<int:pk>/update/', views.DashboardWidgetUpdateView.as_view(), name='widget_update'),
    path('widgets/<int:pk>/delete/', views.DashboardWidgetDeleteView.as_view(), name='widget_delete'),
    path('widgets/reorder/', views.DashboardWidgetReorderView.as_view(), name='widget_reorder'),
]

# مسارات الإعدادات العامة
settings_urlpatterns = [
    path('site-settings/', views.SiteSettingsView.as_view(), name='site_settings'),
    path('email-settings/', views.EmailSettingsView.as_view(), name='email_settings'),
    path('tax-settings/', views.TaxSettingsView.as_view(), name='tax_settings'),
    path('shipping-settings/', views.ShippingSettingsView.as_view(), name='shipping_settings'),
    path('payment-settings/', views.PaymentSettingsView.as_view(), name='payment_settings'),
    path('api-settings/', views.APISettingsView.as_view(), name='api_settings'),
    path('theme-settings/', views.ThemeSettingsView.as_view(), name='theme_settings'),
    path('language-settings/', views.LanguageSettingsView.as_view(), name='language_settings'),
    path('backup/', views.BackupView.as_view(), name='backup'),
    path('restore/', views.RestoreView.as_view(), name='restore'),
]

# مسارات المصادقة
auth_urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('two-factor/', views.TwoFactorSetupView.as_view(), name='two_factor_setup'),
]

# جمع جميع المسارات معًا
urlpatterns = [
    # مسارات المصادقة لا تحتاج إلى login_required
    path('auth/', include((auth_urlpatterns, app_name), namespace='auth')),

    # جميع المسارات الأخرى تتطلب تسجيل الدخول
    path('', include(main_urlpatterns)),
    path('users/', include((user_urlpatterns, app_name), namespace='users')),
    path('products/', include((product_urlpatterns, app_name), namespace='products')),
    path('orders/', include((order_urlpatterns, app_name), namespace='orders')),
    path('checkout/', include((checkout_urlpatterns, app_name), namespace='checkout')),
    path('reports/', include((report_urlpatterns, app_name), namespace='reports')),
    path('settings/', include((settings_urlpatterns, app_name), namespace='settings')),

    # واجهات برمجة التطبيقات AJAX
    path('api/', include([
        path('chart-data/', views.ChartDataAPIView.as_view(), name='chart_data'),
        path('dashboard-stats/', views.DashboardStatsAPIView.as_view(), name='dashboard_stats'),
        path('products-autocomplete/', views.ProductAutocompleteAPIView.as_view(), name='products_autocomplete'),
        path('users-autocomplete/', views.UserAutocompleteAPIView.as_view(), name='users_autocomplete'),
        path('categories-tree/', views.CategoriesTreeAPIView.as_view(), name='categories_tree'),
    ])),
]