from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """
    إضافة عناصر الطلب مباشرة في صفحة تحرير الطلب
    Add order items directly in the order edit page
    """
    model = OrderItem
    extra = 0
    readonly_fields = (
    'product_name', 'product_id', 'variant_name', 'variant_id', 'quantity', 'unit_price', 'total_price')
    fields = ('product_name', 'variant_name', 'quantity', 'unit_price', 'total_price')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # منع إضافة عناصر طلب جديدة - Prevent adding new order items
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    إدارة الطلبات - تسمح للمشرفين بعرض وإدارة طلبات المستخدمين
    Order admin - allows administrators to view and manage user orders
    """
    list_display = (
    'order_number', 'full_name', 'email', 'phone', 'status_colored', 'payment_status_colored', 'grand_total',
    'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'full_name', 'email', 'phone')
    readonly_fields = (
    'order_number', 'user', 'cart', 'total_price', 'shipping_cost', 'tax_amount', 'grand_total', 'created_at',
    'updated_at')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    fieldsets = (
        (_('معلومات الطلب'), {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'payment_method', 'payment_id', 'notes')
        }),
        (_('معلومات العميل'), {
            'fields': ('full_name', 'email', 'phone')
        }),
        (_('معلومات الشحن'), {
            'fields': (
            'shipping_address', 'shipping_city', 'shipping_state', 'shipping_country', 'shipping_postal_code')
        }),
        (_('معلومات المدفوعات'), {
            'fields': ('total_price', 'shipping_cost', 'tax_amount', 'grand_total')
        }),
        (_('معلومات النظام'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )

    def status_colored(self, obj):
        """عرض حالة الطلب بلون مميز - Display order status with distinctive color"""
        colors = {
            'pending': 'blue',
            'processing': 'orange',
            'shipped': 'purple',
            'delivered': 'green',
            'cancelled': 'red',
            'refunded': 'gray',
        }
        status_display = dict(Order.STATUS_CHOICES).get(obj.status, obj.status)
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status_display)

    status_colored.short_description = _("حالة الطلب")

    def payment_status_colored(self, obj):
        """عرض حالة الدفع بلون مميز - Display payment status with distinctive color"""
        colors = {
            'pending': 'blue',
            'paid': 'green',
            'failed': 'red',
            'refunded': 'purple',
        }
        status_display = dict(Order.PAYMENT_STATUS_CHOICES).get(obj.payment_status, obj.payment_status)
        color = colors.get(obj.payment_status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status_display)

    payment_status_colored.short_description = _("حالة الدفع")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    إدارة عناصر الطلب - تسمح للمشرفين بعرض عناصر الطلبات
    Order item admin - allows administrators to view order items
    """
    list_display = ('order', 'product_name', 'variant_name', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'product_name')
    readonly_fields = (
    'order', 'product_name', 'product_id', 'variant_name', 'variant_id', 'quantity', 'unit_price', 'total_price')

    def has_add_permission(self, request):
        # منع إضافة عناصر طلب جديدة - Prevent adding new order items
        return False

    def has_change_permission(self, request, obj=None):
        # منع تعديل عناصر الطلب - Prevent changing order items
        return False