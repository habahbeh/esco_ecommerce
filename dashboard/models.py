from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class DashboardNotification(models.Model):
    """
    نموذج إشعارات لوحة التحكم - يخزن الإشعارات للمستخدمين في لوحة التحكم
    Dashboard notification model - stores notifications for users in the dashboard
    """
    NOTIFICATION_TYPES = [
        ('info', _('معلومات')),
        ('success', _('نجاح')),
        ('warning', _('تحذير')),
        ('error', _('خطأ')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='dashboard_notifications', verbose_name=_("المستخدم"))
    title = models.CharField(_("العنوان"), max_length=100)
    message = models.TextField(_("الرسالة"))
    notification_type = models.CharField(_("نوع الإشعار"), max_length=10, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(_("مقروء"), default=False)
    related_object_type = models.CharField(_("نوع الكائن المرتبط"), max_length=50, blank=True)
    related_object_id = models.CharField(_("معرف الكائن المرتبط"), max_length=100, blank=True)
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)

    class Meta:
        verbose_name = _("إشعار لوحة التحكم")
        verbose_name_plural = _("إشعارات لوحة التحكم")
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ProductReviewAssignment(models.Model):
    """
    نموذج تعيين مراجعة المنتج - يتتبع تعيينات المراجعين للمنتجات
    Product review assignment model - tracks reviewer assignments for products
    """
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE,
                                related_name='review_assignments', verbose_name=_("المنتج"))
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='product_review_assignments', verbose_name=_("المراجع"))
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, related_name='assigned_product_reviews',
                                    verbose_name=_("تم التعيين بواسطة"))
    assigned_at = models.DateTimeField(_("تاريخ التعيين"), auto_now_add=True)
    is_completed = models.BooleanField(_("مكتمل"), default=False)
    completed_at = models.DateTimeField(_("تاريخ الإكمال"), null=True, blank=True)
    notes = models.TextField(_("ملاحظات"), blank=True)

    class Meta:
        verbose_name = _("تعيين مراجعة المنتج")
        verbose_name_plural = _("تعيينات مراجعة المنتج")
        unique_together = ('product', 'reviewer')

    def __str__(self):
        return f"{self.product.name} - {self.reviewer.get_full_name() or self.reviewer.username}"

    def mark_as_completed(self, notes=None):
        """
        تعليم المراجعة كمكتملة
        Mark the review as completed
        """
        from django.utils import timezone

        self.is_completed = True
        self.completed_at = timezone.now()

        if notes:
            self.notes = notes

        self.save()