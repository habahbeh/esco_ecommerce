# dashboard/urls.py
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'dashboard'

# المسارات الرئيسية للوحة التحكم
urlpatterns = [
    # الصفحة الرئيسية للوحة التحكم
    path('', login_required(views.DashboardView.as_view()), name='index'),

    # مسارات الإشعارات
    path('notifications/', login_required(views.NotificationListView.as_view()), name='notifications'),
    path('notifications/mark-read/<uuid:pk>/', login_required(views.MarkNotificationAsReadView.as_view()),
         name='mark_notification_read'),
    path('notifications/mark-all-read/', login_required(views.MarkAllNotificationsAsReadView.as_view()),
         name='mark_all_notifications_read'),

    # إعدادات المستخدم الخاصة بلوحة التحكم
    path('settings/', login_required(views.DashboardSettingsView.as_view()), name='dashboard_settings'),

    # مسارات التقارير والإحصائيات
    path('reports/', login_required(views.ReportIndexView.as_view()), name='report_index'),
    path('reports/sales/', login_required(views.SalesReportView.as_view()), name='sales_report'),
    path('reports/products/', login_required(views.ProductReportView.as_view()), name='product_report'),
    path('reports/customers/', login_required(views.CustomerReportView.as_view()), name='customer_report'),
    path('reports/inventory/', login_required(views.InventoryReportView.as_view()), name='inventory_report'),
    path('reports/revenue/', login_required(views.RevenueReportView.as_view()), name='revenue_report'),
    path('reports/taxes/', login_required(views.TaxReportView.as_view()), name='tax_report'),
    path('reports/export/', login_required(views.ExportReportView.as_view()), name='export_report'),

    # إدارة ودجات لوحة التحكم
    path('widgets/', login_required(views.DashboardWidgetListView.as_view()), name='widget_list'),
    path('widgets/create/', login_required(views.DashboardWidgetCreateView.as_view()), name='widget_create'),
    path('widgets/<int:pk>/update/', login_required(views.DashboardWidgetUpdateView.as_view()), name='widget_update'),
    path('widgets/<int:pk>/delete/', login_required(views.DashboardWidgetDeleteView.as_view()), name='widget_delete'),
    path('widgets/reorder/', login_required(views.DashboardWidgetReorderView.as_view()), name='widget_reorder'),

    # واجهات برمجة التطبيقات AJAX
    path('api/chart-data/', login_required(views.ChartDataAPIView.as_view()), name='chart_data'),
    path('api/dashboard-stats/', login_required(views.DashboardStatsAPIView.as_view()), name='dashboard_stats'),
    path('api/users-autocomplete/', login_required(views.UserAutocompleteAPIView.as_view()), name='users_autocomplete'),

    # تضمين مسارات التطبيقات الأخرى
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('core/', include('core.urls', namespace='core')),
    path('products/', include('products.urls', namespace='products')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('checkout/', include('checkout.urls', namespace='checkout')),
    path('payment/', include('payment.urls', namespace='payment')),
]