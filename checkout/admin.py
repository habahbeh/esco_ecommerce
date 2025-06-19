# checkout/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import CheckoutSession, PaymentMethod, ShippingMethod, Coupon, CouponUsage

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'payment_type', 'is_active', 'is_default', 'sort_order')
    list_filter = ('is_active', 'payment_type')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'code', 'payment_type', 'description', 'icon')
        }),
        (_('رسوم ومبالغ'), {
            'fields': ('fee_fixed', 'fee_percentage', 'min_amount', 'max_amount')
        }),
        (_('تعليمات'), {
            'fields': ('instructions',)
        }),
        (_('الإعدادات'), {
            'fields': ('is_active', 'is_default', 'sort_order')
        }),
        (_('بيانات API'), {
            'fields': ('api_credentials',)
        }),
        (_('طوابع زمنية'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'base_cost', 'free_shipping_threshold', 'is_active', 'is_default', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'code', 'description', 'icon')
        }),
        (_('التكاليف'), {
            'fields': ('base_cost', 'free_shipping_threshold')
        }),
        (_('وقت التوصيل'), {
            'fields': ('estimated_days_min', 'estimated_days_max')
        }),
        (_('الإعدادات'), {
            'fields': ('is_active', 'is_default', 'sort_order', 'restrictions', 'countries')
        }),
        (_('طوابع زمنية'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'start_date', 'end_date', 'uses_count')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code', 'description')
    readonly_fields = ('uses_count', 'created_at', 'updated_at')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('code', 'description')
        }),
        (_('الخصم'), {
            'fields': ('discount_type', 'discount_value', 'min_order_value', 'max_discount_amount')
        }),
        (_('قيود الاستخدام'), {
            'fields': ('is_active', 'start_date', 'end_date', 'max_uses', 'max_uses_per_user')
        }),
        (_('الإحصائيات'), {
            'fields': ('uses_count', 'created_at', 'updated_at')
        }),
    )

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'order', 'used_at')
    list_filter = ('used_at',)
    search_fields = ('coupon__code', 'user__email', 'order__order_number')
    readonly_fields = ('used_at',)

@admin.register(CheckoutSession)
class CheckoutSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'current_step', 'is_completed', 'total_amount', 'created_at')
    list_filter = ('is_completed', 'current_step', 'created_at')
    search_fields = ('user__email', 'email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'expires_at', 'completed_at')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('id', 'user', 'cart', 'order', 'session_key')
        }),
        (_('معلومات العميل'), {
            'fields': ('email', 'phone_number', 'notes')
        }),
        (_('الحالة'), {
            'fields': ('current_step', 'is_completed')
        }),
        (_('طرق الشحن والدفع'), {
            'fields': ('shipping_method', 'payment_method')
        }),
        (_('المبالغ'), {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        (_('طوابع زمنية'), {
            'fields': ('created_at', 'updated_at', 'expires_at', 'completed_at')
        }),
        (_('معلومات الأمان'), {
            'fields': ('ip_address', 'user_agent')
        }),
    )