from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import DashboardNotification, ProductReviewAssignment


@admin.register(DashboardNotification)
class DashboardNotificationAdmin(admin.ModelAdmin):
    """
    إدارة إشعارات لوحة التحكم - تسمح للمشرفين بإدارة الإشعارات في لوحة التحكم
    Dashboard notification admin - allows administrators to manage dashboard notifications
    """
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    fieldsets = (
        (_('معلومات الإشعار'), {
            'fields': ('user', 'title', 'message', 'notification_type', 'is_read')
        }),
        (_('معلومات الكائن المرتبط'), {
            'fields': ('related_object_type', 'related_object_id')
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at',)
        }),
    )

    def mark_as_read(self, request, queryset):
        """
        إجراء لتعليم الإشعارات المحددة كمقروءة
        Action to mark selected notifications as read
        """
        queryset.update(is_read=True)
        self.message_user(request, _("تم تعليم الإشعارات المحددة كمقروءة"))

    mark_as_read.short_description = _("تعليم كمقروءة")

    def mark_as_unread(self, request, queryset):
        """
        إجراء لتعليم الإشعارات المحددة كغير مقروءة
        Action to mark selected notifications as unread
        """
        queryset.update(is_read=False)
        self.message_user(request, _("تم تعليم الإشعارات المحددة كغير مقروءة"))

    mark_as_unread.short_description = _("تعليم كغير مقروءة")

    actions = [mark_as_read, mark_as_unread]


@admin.register(ProductReviewAssignment)
class ProductReviewAssignmentAdmin(admin.ModelAdmin):
    """
    إدارة تعيينات مراجعة المنتج - تسمح للمشرفين بإدارة تعيينات المراجعين للمنتجات
    Product review assignment admin - allows administrators to manage reviewer assignments for products
    """
    list_display = ('product', 'reviewer', 'assigned_by', 'assigned_at', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'assigned_at', 'completed_at')
    search_fields = ('product__name', 'product__sku', 'reviewer__username', 'reviewer__email')
    readonly_fields = ('assigned_at', 'completed_at')
    date_hierarchy = 'assigned_at'
    fieldsets = (
        (_('معلومات التعيين'), {
            'fields': ('product', 'reviewer', 'assigned_by', 'is_completed', 'notes')
        }),
        (_('معلومات النظام'), {
            'fields': ('assigned_at', 'completed_at')
        }),
    )

    def mark_as_completed(self, request, queryset):
        """
        إجراء لتعليم التعيينات المحددة كمكتملة
        Action to mark selected assignments as completed
        """
        for assignment in queryset.filter(is_completed=False):
            assignment.is_completed = True
            assignment.completed_at = timezone.now()
            assignment.save()
        self.message_user(request, _("تم تعليم التعيينات المحددة كمكتملة"))

    mark_as_completed.short_description = _("تعليم كمكتملة")

    actions = [mark_as_completed]