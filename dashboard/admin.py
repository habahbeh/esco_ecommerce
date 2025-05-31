# dashboard/admin.py
"""
Django Admin configuration for dashboard models
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    DashboardNotification,
    ProductReviewAssignment,
    DashboardWidget,
    DashboardUserSettings
)


@admin.register(DashboardNotification)
class DashboardNotificationAdmin(admin.ModelAdmin):
    """
    إدارة إشعارات لوحة التحكم
    Dashboard Notifications Admin
    """
    list_display = [
        'title', 'user', 'notification_type', 'is_read',
        'created_at', 'read_at'
    ]
    list_filter = [
        'notification_type', 'is_read', 'created_at'
    ]
    search_fields = [
        'title', 'message', 'user__username', 'user__email'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'read_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('user', 'title', 'message', 'notification_type')
        }),
        (_('الكائن المرتبط'), {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        (_('الإجراءات'), {
            'fields': ('action_url', 'action_text'),
            'classes': ('collapse',)
        }),
        (_('الحالة'), {
            'fields': ('is_read', 'read_at', 'expires_at')
        }),
        (_('معلومات النظام'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def has_change_permission(self, request, obj=None):
        # Allow marking as read but prevent editing content
        return request.user.is_superuser

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        updated = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(
            request,
            f"تم تعليم {updated} إشعار كمقروء."
        )

    mark_as_read.short_description = _("تعليم كمقروء")

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(
            request,
            f"تم تعليم {updated} إشعار كغير مقروء."
        )

    mark_as_unread.short_description = _("تعليم كغير مقروء")


@admin.register(ProductReviewAssignment)
class ProductReviewAssignmentAdmin(admin.ModelAdmin):
    """
    إدارة تعيينات مراجعة المنتجات
    Product Review Assignments Admin
    """
    list_display = [
        'product_name', 'reviewer', 'assigned_by', 'priority',
        'is_completed', 'assigned_at', 'due_date', 'status_indicator'
    ]
    list_filter = [
        'priority', 'is_completed', 'assigned_at', 'due_date',
        'is_accepted'
    ]
    search_fields = [
        'product__name', 'reviewer__username', 'reviewer__email',
        'assigned_by__username'
    ]
    readonly_fields = [
        'id', 'assigned_at', 'completed_at', 'time_spent_display'
    ]
    date_hierarchy = 'assigned_at'
    ordering = ['-assigned_at']

    fieldsets = (
        (_('معلومات التعيين'), {
            'fields': ('product', 'reviewer', 'assigned_by', 'priority')
        }),
        (_('التوقيتات'), {
            'fields': ('assigned_at', 'due_date', 'estimated_time')
        }),
        (_('التعليمات'), {
            'fields': ('instructions',)
        }),
        (_('حالة الإكمال'), {
            'fields': ('is_completed', 'completed_at', 'review_notes', 'actual_time')
        }),
        (_('نتيجة المراجعة'), {
            'fields': ('is_accepted', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        (_('معلومات النظام'), {
            'fields': ('id', 'time_spent_display'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'product', 'reviewer', 'assigned_by'
        )

    def product_name(self, obj):
        """Display product name with link"""
        if obj.product:
            url = reverse('admin:products_product_change', args=[obj.product.pk])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'

    product_name.short_description = _('المنتج')
    product_name.admin_order_field = 'product__name'

    def status_indicator(self, obj):
        """Visual status indicator"""
        if obj.is_completed:
            if obj.is_accepted:
                return format_html(
                    '<span style="color: green;">✓ مكتمل - مقبول</span>'
                )
            else:
                return format_html(
                    '<span style="color: red;">✗ مكتمل - مرفوض</span>'
                )
        elif obj.is_overdue:
            return format_html(
                '<span style="color: red;">⚠ متأخر</span>'
            )
        else:
            return format_html(
                '<span style="color: orange;">⏳ قيد المراجعة</span>'
            )

    status_indicator.short_description = _('الحالة')

    def time_spent_display(self, obj):
        """Display time spent on assignment"""
        time_spent = obj.time_spent
        if time_spent:
            days = time_spent.days
            hours, remainder = divmod(time_spent.seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            parts = []
            if days:
                parts.append(f"{days} يوم")
            if hours:
                parts.append(f"{hours} ساعة")
            if minutes:
                parts.append(f"{minutes} دقيقة")

            return " و ".join(parts) if parts else "أقل من دقيقة"
        return '-'

    time_spent_display.short_description = _('الوقت المستغرق')

    actions = ['mark_as_completed', 'extend_due_date']

    def mark_as_completed(self, request, queryset):
        """Mark assignments as completed"""
        updated = queryset.filter(is_completed=False).update(
            is_completed=True,
            completed_at=timezone.now()
        )
        self.message_user(
            request,
            f"تم تعليم {updated} تعيين كمكتمل."
        )

    mark_as_completed.short_description = _("تعليم كمكتمل")

    def extend_due_date(self, request, queryset):
        """Extend due date by 3 days"""
        from datetime import timedelta

        updated = 0
        for assignment in queryset.filter(is_completed=False):
            if assignment.due_date:
                assignment.due_date += timedelta(days=3)
                assignment.save()
                updated += 1

        self.message_user(
            request,
            f"تم تمديد موعد {updated} تعيين بـ 3 أيام."
        )

    extend_due_date.short_description = _("تمديد الموعد النهائي")


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    """
    إدارة ودجات لوحة التحكم
    Dashboard Widgets Admin
    """
    list_display = [
        'title', 'widget_type', 'row', 'column', 'width',
        'is_active', 'sort_order'
    ]
    list_filter = ['widget_type', 'is_active', 'row']
    search_fields = ['name', 'title', 'description']
    ordering = ['row', 'column', 'sort_order']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'title', 'description', 'widget_type')
        }),
        (_('التخطيط'), {
            'fields': ('row', 'column', 'width', 'height', 'sort_order')
        }),
        (_('الإعدادات'), {
            'fields': ('config',)
        }),
        (_('الصلاحيات'), {
            'fields': ('required_permissions',)
        }),
        (_('الحالة'), {
            'fields': ('is_active',)
        }),
    )


@admin.register(DashboardUserSettings)
class DashboardUserSettingsAdmin(admin.ModelAdmin):
    """
    إدارة إعدادات المستخدمين للوحة التحكم
    Dashboard User Settings Admin
    """
    list_display = [
        'user', 'theme', 'language', 'default_view',
        'items_per_page', 'email_notifications'
    ]
    list_filter = [
        'theme', 'language', 'default_view', 'email_notifications'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (_('المستخدم'), {
            'fields': ('user',)
        }),
        (_('تفضيلات العرض'), {
            'fields': ('theme', 'language', 'default_view', 'items_per_page')
        }),
        (_('تخطيط الودجات'), {
            'fields': ('widgets_layout',),
            'classes': ('collapse',)
        }),
        (_('إعدادات الإشعارات'), {
            'fields': (
                'email_notifications', 'browser_notifications',
                'notification_sound'
            )
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Register inline admins if needed
class DashboardNotificationInline(admin.TabularInline):
    """
    Inline admin for notifications
    """
    model = DashboardNotification
    extra = 0
    readonly_fields = ['created_at', 'read_at']
    fields = ['title', 'notification_type', 'is_read', 'created_at']


class ProductReviewAssignmentInline(admin.TabularInline):
    """
    Inline admin for review assignments
    """
    model = ProductReviewAssignment
    extra = 0
    readonly_fields = ['assigned_at', 'completed_at']
    fields = ['reviewer', 'priority', 'is_completed', 'assigned_at']