from django.contrib import admin
from .models import Transaction, Payment, Refund

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'user', 'amount', 'currency', 'transaction_type', 'status', 'created_at')
    list_filter = ('status', 'transaction_type', 'currency', 'payment_gateway')
    search_fields = ('reference_number', 'user__email', 'gateway_transaction_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'completed_at')
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('id', 'reference_number', 'user', 'order')
        }),
        ('معلومات مالية', {
            'fields': ('amount', 'currency', 'fees')
        }),
        ('حالة المعاملة', {
            'fields': ('transaction_type', 'status', 'created_at', 'updated_at', 'completed_at')
        }),
        ('معلومات البوابة', {
            'fields': ('payment_gateway', 'payment_method', 'gateway_transaction_id', 'gateway_response')
        }),
        ('تفاصيل إضافية', {
            'fields': ('description', 'notes', 'metadata', 'ip_address', 'user_agent')
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'currency', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'currency', 'payment_gateway')
    search_fields = ('user__email', 'gateway_payment_id', 'order__order_number')
    readonly_fields = ('id', 'created_at', 'updated_at', 'paid_at')
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('id', 'user', 'order', 'transaction')
        }),
        ('معلومات الدفع', {
            'fields': ('amount', 'currency', 'payment_method', 'status')
        }),
        ('توقيت الدفع', {
            'fields': ('created_at', 'updated_at', 'paid_at')
        }),
        ('معلومات البوابة', {
            'fields': ('payment_gateway', 'gateway_payment_id', 'gateway_response')
        }),
        ('معلومات البطاقة', {
            'fields': ('card_type', 'last_4_digits', 'card_expiry')
        }),
        ('تفاصيل إضافية', {
            'fields': ('billing_address', 'description', 'notes', 'ip_address')
        }),
    )

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'amount', 'currency', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason', 'currency')
    search_fields = ('payment__gateway_payment_id', 'user__email', 'gateway_refund_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'completed_at')
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('id', 'payment', 'order', 'user', 'transaction')
        }),
        ('معلومات الاسترداد', {
            'fields': ('amount', 'currency', 'reason', 'status')
        }),
        ('توقيت الاسترداد', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
        ('معلومات البوابة', {
            'fields': ('refund_gateway', 'gateway_refund_id', 'gateway_response')
        }),
        ('الأشخاص المسؤولون', {
            'fields': ('requested_by', 'processed_by')
        }),
        ('ملاحظات', {
            'fields': ('notes', 'customer_notes', 'admin_notes')
        }),
    )