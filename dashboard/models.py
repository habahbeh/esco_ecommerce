# dashboard/models.py
"""
نماذج لوحة التحكم
Dashboard models
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        abstract = True


class DashboardNotification(TimeStampedModel):
    """
    نموذج إشعارات لوحة التحكم
    Dashboard notifications model
    """
    NOTIFICATION_TYPES = [
        ('info', _('معلومات')),
        ('success', _('نجاح')),
        ('warning', _('تحذير')),
        ('error', _('خطأ')),
        ('urgent', _('عاجل')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard_notifications',
        verbose_name=_("المستخدم")
    )

    title = models.CharField(
        _("العنوان"),
        max_length=200,
        help_text=_("عنوان الإشعار")
    )

    message = models.TextField(
        _("الرسالة"),
        help_text=_("محتوى الإشعار")
    )

    notification_type = models.CharField(
        _("نوع الإشعار"),
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info'
    )

    # Related object information
    related_object_type = models.CharField(
        _("نوع الكائن المرتبط"),
        max_length=50,
        blank=True,
        help_text=_("نوع الكائن المرتبط بالإشعار")
    )

    related_object_id = models.CharField(
        _("معرف الكائن المرتبط"),
        max_length=100,
        blank=True,
        help_text=_("معرف الكائن المرتبط بالإشعار")
    )

    # Status
    is_read = models.BooleanField(
        _("مقروء"),
        default=False
    )

    read_at = models.DateTimeField(
        _("تاريخ القراءة"),
        null=True,
        blank=True
    )

    # Actions
    action_url = models.URLField(
        _("رابط الإجراء"),
        blank=True,
        help_text=_("رابط للانتقال إليه عند النقر على الإشعار")
    )

    action_text = models.CharField(
        _("نص الإجراء"),
        max_length=100,
        blank=True,
        help_text=_("نص زر الإجراء")
    )

    # Auto-expire
    expires_at = models.DateTimeField(
        _("ينتهي في"),
        null=True,
        blank=True,
        help_text=_("تاريخ انتهاء صلاحية الإشعار")
    )

    class Meta:
        verbose_name = _("إشعار لوحة التحكم")
        verbose_name_plural = _("إشعارات لوحة التحكم")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['related_object_type', 'related_object_id']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    @property
    def is_expired(self):
        """Check if notification is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def time_since_created(self):
        """Get human-readable time since creation"""
        from django.utils.timesince import timesince
        return timesince(self.created_at)

    @classmethod
    def create_notification(cls, user, title, message, notification_type='info', **kwargs):
        """Create a new notification"""
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            **kwargs
        )

    @classmethod
    def get_unread_for_user(cls, user):
        """Get unread notifications for user"""
        return cls.objects.filter(
            user=user,
            is_read=False
        ).filter(
            models.Q(expires_at__isnull=True) |
            models.Q(expires_at__gt=timezone.now())
        ).order_by('-created_at')

    @classmethod
    def mark_all_read_for_user(cls, user):
        """Mark all notifications as read for user"""
        cls.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )


class ProductReviewAssignment(TimeStampedModel):
    """
    نموذج تعيين مراجعة المنتجات
    Product review assignment model
    """
    PRIORITY_CHOICES = [
        ('low', _('منخفضة')),
        ('normal', _('عادية')),
        ('high', _('عالية')),
        ('urgent', _('عاجلة')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='review_assignments',
        verbose_name=_("المنتج")
    )

    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_review_assignments',
        verbose_name=_("المراجع")
    )

    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_product_reviews',
        verbose_name=_("عُين بواسطة")
    )

    # Assignment details
    assigned_at = models.DateTimeField(
        _("تاريخ التعيين"),
        auto_now_add=True
    )

    due_date = models.DateTimeField(
        _("تاريخ الاستحقاق"),
        null=True,
        blank=True,
        help_text=_("التاريخ المطلوب إنجاز المراجعة فيه")
    )

    priority = models.CharField(
        _("الأولوية"),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal'
    )

    instructions = models.TextField(
        _("التعليمات"),
        blank=True,
        help_text=_("تعليمات خاصة للمراجع")
    )

    # Completion details
    is_completed = models.BooleanField(
        _("مكتمل"),
        default=False
    )

    completed_at = models.DateTimeField(
        _("تاريخ الإكمال"),
        null=True,
        blank=True
    )

    review_notes = models.TextField(
        _("ملاحظات المراجعة"),
        blank=True,
        help_text=_("ملاحظات المراجع حول المنتج")
    )

    # Status tracking
    is_accepted = models.BooleanField(
        _("مقبول"),
        default=False
    )

    rejection_reason = models.TextField(
        _("سبب الرفض"),
        blank=True,
        help_text=_("سبب رفض المنتج")
    )

    # Time tracking
    estimated_time = models.PositiveIntegerField(
        _("الوقت المقدر (بالدقائق)"),
        null=True,
        blank=True,
        help_text=_("الوقت المقدر لإكمال المراجعة")
    )

    actual_time = models.PositiveIntegerField(
        _("الوقت الفعلي (بالدقائق)"),
        null=True,
        blank=True,
        help_text=_("الوقت الفعلي لإكمال المراجعة")
    )

    class Meta:
        verbose_name = _("تعيين مراجعة منتج")
        verbose_name_plural = _("تعيينات مراجعة المنتجات")
        ordering = ['-assigned_at']
        unique_together = [['product', 'reviewer']]
        indexes = [
            models.Index(fields=['reviewer', 'is_completed']),
            models.Index(fields=['product', 'is_completed']),
            models.Index(fields=['assigned_at']),
            models.Index(fields=['due_date']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.reviewer.username} - {self.product.name}"

    def clean(self):
        """Validate assignment"""
        from django.core.exceptions import ValidationError

        # Check if reviewer has permission
        if not self.reviewer.is_staff and not hasattr(self.reviewer, 'is_product_reviewer'):
            raise ValidationError({
                'reviewer': _("المراجع يجب أن يكون موظف أو لديه صلاحية مراجعة المنتجات")
            })

        # Check due date
        if self.due_date and self.due_date <= timezone.now():
            raise ValidationError({
                'due_date': _("تاريخ الاستحقاق يجب أن يكون في المستقبل")
            })

    def mark_as_completed(self, notes="", is_accepted=True, rejection_reason=""):
        """Mark assignment as completed"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.review_notes = notes
        self.is_accepted = is_accepted
        if not is_accepted:
            self.rejection_reason = rejection_reason
        self.save()

        # Update product status based on review result
        if is_accepted:
            self.product.status = 'published'
            self.product.approved_by = self.reviewer
            self.product.published_at = timezone.now()
        else:
            self.product.status = 'rejected'

        self.product.save()

    @property
    def is_overdue(self):
        """Check if assignment is overdue"""
        if self.due_date and not self.is_completed:
            return timezone.now() > self.due_date
        return False

    @property
    def time_until_due(self):
        """Get time until due date"""
        if self.due_date and not self.is_completed:
            remaining = self.due_date - timezone.now()
            if remaining.total_seconds() > 0:
                return remaining
        return None

    @property
    def time_spent(self):
        """Calculate time spent on assignment"""
        if self.completed_at:
            return self.completed_at - self.assigned_at
        return timezone.now() - self.assigned_at

    @classmethod
    def get_pending_for_reviewer(cls, reviewer):
        """Get pending assignments for reviewer"""
        return cls.objects.filter(
            reviewer=reviewer,
            is_completed=False
        ).select_related('product').order_by('due_date', 'priority', 'assigned_at')

    @classmethod
    def get_overdue_assignments(cls):
        """Get all overdue assignments"""
        return cls.objects.filter(
            is_completed=False,
            due_date__lt=timezone.now()
        ).select_related('reviewer', 'product')

    def __repr__(self):
        return f"<ProductReviewAssignment: {self.product.name} -> {self.reviewer.username}>"


class DashboardWidget(TimeStampedModel):
    """
    نموذج ودجات لوحة التحكم
    Dashboard widgets model
    """
    WIDGET_TYPES = [
        ('chart', _('مخطط')),
        ('counter', _('عداد')),
        ('list', _('قائمة')),
        ('table', _('جدول')),
        ('text', _('نص')),
        ('progress', _('شريط تقدم')),
    ]

    name = models.CharField(
        _("اسم الودجة"),
        max_length=100
    )

    widget_type = models.CharField(
        _("نوع الودجة"),
        max_length=20,
        choices=WIDGET_TYPES
    )

    title = models.CharField(
        _("العنوان"),
        max_length=200
    )

    description = models.TextField(
        _("الوصف"),
        blank=True
    )

    # Configuration
    config = models.JSONField(
        _("إعدادات الودجة"),
        default=dict,
        help_text=_("إعدادات JSON للودجة")
    )

    # Positioning
    row = models.PositiveIntegerField(
        _("الصف"),
        default=1
    )

    column = models.PositiveIntegerField(
        _("العمود"),
        default=1
    )

    width = models.PositiveIntegerField(
        _("العرض"),
        default=6,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    height = models.PositiveIntegerField(
        _("الارتفاع"),
        default=300
    )

    # Permissions
    required_permissions = models.JSONField(
        _("الصلاحيات المطلوبة"),
        default=list,
        help_text=_("قائمة بالصلاحيات المطلوبة لعرض الودجة")
    )

    # Status
    is_active = models.BooleanField(
        _("نشط"),
        default=True
    )

    sort_order = models.PositiveIntegerField(
        _("الترتيب"),
        default=0
    )

    class Meta:
        verbose_name = _("ودجة لوحة التحكم")
        verbose_name_plural = _("ودجات لوحة التحكم")
        ordering = ['row', 'column', 'sort_order']

    def __str__(self):
        return self.title

    def can_user_view(self, user):
        """Check if user can view this widget"""
        if not self.is_active:
            return False

        if not self.required_permissions:
            return True

        return user.has_perms(self.required_permissions)


class DashboardUserSettings(TimeStampedModel):
    """
    نموذج إعدادات المستخدم للوحة التحكم
    Dashboard user settings model
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard_settings',
        verbose_name=_("المستخدم")
    )

    # Layout preferences
    widgets_layout = models.JSONField(
        _("تخطيط الودجات"),
        default=dict,
        help_text=_("تخطيط ودجات المستخدم المخصص")
    )

    # Notification preferences
    email_notifications = models.BooleanField(
        _("إشعارات البريد الإلكتروني"),
        default=True
    )

    browser_notifications = models.BooleanField(
        _("إشعارات المتصفح"),
        default=True
    )

    notification_sound = models.BooleanField(
        _("صوت الإشعارات"),
        default=False
    )

    # Dashboard preferences
    default_view = models.CharField(
        _("العرض الافتراضي"),
        max_length=50,
        default='overview'
    )

    items_per_page = models.PositiveIntegerField(
        _("عدد العناصر في الصفحة"),
        default=20,
        validators=[MinValueValidator(10), MaxValueValidator(100)]
    )

    # Theme and language
    theme = models.CharField(
        _("السمة"),
        max_length=20,
        default='light',
        choices=[
            ('light', _('فاتح')),
            ('dark', _('داكن')),
            ('auto', _('تلقائي')),
        ]
    )

    language = models.CharField(
        _("اللغة"),
        max_length=10,
        default='ar',
        choices=[
            ('ar', _('العربية')),
            ('en', _('الإنجليزية')),
        ]
    )

    class Meta:
        verbose_name = _("إعدادات المستخدم للوحة التحكم")
        verbose_name_plural = _("إعدادات المستخدمين للوحة التحكم")

    def __str__(self):
        return f"إعدادات {self.user.username}"