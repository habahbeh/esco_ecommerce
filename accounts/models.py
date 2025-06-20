# accounts/models.py
"""
نماذج المستخدمين والملفات الشخصية
User and Profile models
"""

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils import timezone
import uuid
import secrets


class Role(models.Model):
    """
    نموذج الأدوار المخصصة في النظام
    Custom roles model
    """
    name = models.CharField(_("اسم الدور"), max_length=100)
    description = models.TextField(_("وصف الدور"), blank=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("الصلاحيات"),
        blank=True,
    )

    class Meta:
        verbose_name = _("دور")
        verbose_name_plural = _("الأدوار")

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    نموذج المستخدم المخصص
    Custom User model
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(
        _("البريد الإلكتروني"),
        unique=True,
        help_text=_("البريد الإلكتروني للمستخدم")
    )

    phone_number = models.CharField(
        _("رقم الهاتف"),
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_("رقم الهاتف يجب أن يكون في الصيغة: '+999999999'. حتى 15 رقم مسموح.")
            )
        ]
    )

    # Avatar
    avatar = models.ImageField(
        _("الصورة الشخصية"),
        upload_to='avatars/',
        blank=True,
        null=True
    )

    # Additional Info
    birth_date = models.DateField(
        _("تاريخ الميلاد"),
        blank=True,
        null=True
    )

    gender_choices = [
        ('M', _('ذكر')),
        ('F', _('أنثى')),
        ('O', _('آخر')),
    ]

    gender = models.CharField(
        _("الجنس"),
        max_length=1,
        choices=gender_choices,
        blank=True
    )

    # Address Information
    address = models.TextField(_("العنوان"), blank=True)
    city = models.CharField(_("المدينة"), max_length=100, blank=True)
    country = models.CharField(_("الدولة"), max_length=100, blank=True)
    postal_code = models.CharField(_("الرمز البريدي"), max_length=20, blank=True)

    # Email verification
    is_verified = models.BooleanField(
        _("موثق"),
        default=False,
        help_text=_("هل تم تأكيد البريد الإلكتروني؟")
    )

    verification_token = models.CharField(
        _("رمز التحقق"),
        max_length=100,
        blank=True,
        null=True
    )

    verification_token_expires = models.DateTimeField(
        _("تاريخ انتهاء رمز التحقق"),
        blank=True,
        null=True
    )

    # Password reset
    password_reset_token = models.CharField(
        _("رمز إعادة تعيين كلمة المرور"),
        max_length=100,
        blank=True,
        null=True
    )

    password_reset_expires = models.DateTimeField(
        _("تاريخ انتهاء رمز إعادة تعيين كلمة المرور"),
        blank=True,
        null=True
    )

    # Role-based permissions
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("الدور"),
        related_name="users"
    )

    is_product_reviewer = models.BooleanField(
        _("مراجع منتجات"),
        default=False,
        help_text=_("يمكن للمستخدم مراجعة المنتجات في لوحة التحكم")
    )

    # Marketing preferences
    accept_marketing = models.BooleanField(
        _("أوافق على التسويق"),
        default=False,
        help_text=_("هل يوافق على تلقي رسائل تسويقية؟")
    )

    # Language and preferences
    language = models.CharField(
        _("اللغة المفضلة"),
        max_length=10,
        default='ar',
        choices=[
            ('ar', _('العربية')),
            ('en', _('الإنجليزية')),
        ]
    )

    timezone = models.CharField(
        _("المنطقة الزمنية"),
        max_length=50,
        default='Asia/Riyadh',
        blank=True
    )

    # Statistics
    last_activity = models.DateTimeField(
        _("آخر نشاط"),
        auto_now=True
    )

    total_orders = models.PositiveIntegerField(
        _("إجمالي الطلبات"),
        default=0,
        editable=False
    )

    total_spent = models.DecimalField(
        _("إجمالي المبلغ المنفق"),
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False
    )

    class Meta:
        verbose_name = _("مستخدم")
        verbose_name_plural = _("المستخدمون")
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Get full name of the user"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.username

    def get_short_name(self):
        """Get short name of the user"""
        return self.first_name or self.username

    @property
    def full_address(self):
        """Get formatted full address"""
        parts = [self.address, self.city, self.country, self.postal_code]
        return ", ".join([part for part in parts if part])

    def update_order_stats(self):
        """Update user order statistics"""
        from orders.models import Order

        orders = Order.objects.filter(user=self, status='completed')
        self.total_orders = orders.count()
        self.total_spent = orders.aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0
        self.save(update_fields=['total_orders', 'total_spent'])

    def can_review_products(self):
        """Check if user can review products"""
        return self.is_product_reviewer or self.is_staff or self.is_superuser

    def can_access_dashboard(self):
        """Check if user can access dashboard"""
        return self.is_staff or self.is_superuser

    def generate_verification_token(self):
        """إنشاء رمز تحقق جديد للبريد الإلكتروني"""
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expires = timezone.now() + timezone.timedelta(days=1)
        self.save(update_fields=['verification_token', 'verification_token_expires'])
        return self.verification_token

    def verify_email(self, token):
        """التحقق من صحة رمز التحقق وتفعيل البريد الإلكتروني"""
        if (self.verification_token == token and
                self.verification_token_expires and
                self.verification_token_expires > timezone.now()):
            self.is_verified = True
            self.verification_token = None
            self.verification_token_expires = None
            self.save(update_fields=['is_verified', 'verification_token', 'verification_token_expires'])
            return True
        return False

    def generate_password_reset_token(self):
        """إنشاء رمز إعادة تعيين كلمة المرور"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = timezone.now() + timezone.timedelta(hours=24)
        self.save(update_fields=['password_reset_token', 'password_reset_expires'])
        return self.password_reset_token

    def verify_password_reset_token(self, token):
        """التحقق من صحة رمز إعادة تعيين كلمة المرور"""
        if (self.password_reset_token == token and
                self.password_reset_expires and
                self.password_reset_expires > timezone.now()):
            return True
        return False

    def reset_password(self, token, new_password):
        """إعادة تعيين كلمة المرور باستخدام الرمز"""
        if self.verify_password_reset_token(token):
            self.set_password(new_password)
            self.password_reset_token = None
            self.password_reset_expires = None
            self.save(update_fields=['password', 'password_reset_token', 'password_reset_expires'])
            return True
        return False


class UserProfile(models.Model):
    """
    نموذج الملف الشخصي للمستخدم (إضافي)
    Extended User Profile model
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_("المستخدم")
    )

    # Social Media Links
    website = models.URLField(_("الموقع الشخصي"), blank=True)
    twitter = models.CharField(_("تويتر"), max_length=100, blank=True)
    facebook = models.CharField(_("فيسبوك"), max_length=100, blank=True)
    instagram = models.CharField(_("انستغرام"), max_length=100, blank=True)
    linkedin = models.CharField(_("لينكد إن"), max_length=100, blank=True)

    # Bio and interests
    bio = models.TextField(
        _("نبذة شخصية"),
        max_length=500,
        blank=True,
        help_text=_("نبذة مختصرة عن المستخدم")
    )

    interests = models.TextField(
        _("الاهتمامات"),
        blank=True,
        help_text=_("اهتمامات المستخدم مفصولة بفواصل")
    )

    # Professional info
    profession = models.CharField(
        _("المهنة"),
        max_length=100,
        blank=True
    )

    company = models.CharField(
        _("الشركة"),
        max_length=100,
        blank=True
    )

    # Preferences
    notification_preferences = models.JSONField(
        _("تفضيلات الإشعارات"),
        default=dict,
        blank=True
    )

    privacy_settings = models.JSONField(
        _("إعدادات الخصوصية"),
        default=dict,
        blank=True
    )

    # Verification
    identity_verified = models.BooleanField(
        _("موثق الهوية"),
        default=False
    )

    phone_verified = models.BooleanField(
        _("موثق الهاتف"),
        default=False
    )

    # Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("ملف شخصي")
        verbose_name_plural = _("الملفات الشخصية")

    def __str__(self):
        return f"ملف {self.user.username}"

    def get_notification_preference(self, key, default=True):
        """Get specific notification preference"""
        return self.notification_preferences.get(key, default)

    def set_notification_preference(self, key, value):
        """Set specific notification preference"""
        self.notification_preferences[key] = value
        self.save(update_fields=['notification_preferences'])


class UserAddress(models.Model):
    """
    نموذج عناوين المستخدم
    User Address model
    """
    ADDRESS_TYPES = [
        ('home', _('المنزل')),
        ('work', _('العمل')),
        ('other', _('آخر')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_("المستخدم")
    )

    # Address details
    label = models.CharField(
        _("تسمية العنوان"),
        max_length=100,
        help_text=_("مثل: المنزل، العمل، إلخ")
    )

    type = models.CharField(
        _("نوع العنوان"),
        max_length=10,
        choices=ADDRESS_TYPES,
        default='home'
    )

    first_name = models.CharField(_("الاسم الأول"), max_length=50)
    last_name = models.CharField(_("اسم العائلة"), max_length=50)

    address_line_1 = models.CharField(
        _("سطر العنوان الأول"),
        max_length=200
    )

    address_line_2 = models.CharField(
        _("سطر العنوان الثاني"),
        max_length=200,
        blank=True
    )

    city = models.CharField(_("المدينة"), max_length=100)
    state = models.CharField(_("الولاية/المنطقة"), max_length=100, blank=True)
    postal_code = models.CharField(_("الرمز البريدي"), max_length=20)
    country = models.CharField(_("الدولة"), max_length=100)

    phone_number = models.CharField(
        _("رقم الهاتف"),
        max_length=20,
        blank=True
    )

    # Settings
    is_default = models.BooleanField(
        _("العنوان الافتراضي"),
        default=False
    )

    is_billing_default = models.BooleanField(
        _("عنوان الفوترة الافتراضي"),
        default=False
    )

    is_shipping_default = models.BooleanField(
        _("عنوان الشحن الافتراضي"),
        default=False
    )

    # Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("عنوان مستخدم")
        verbose_name_plural = _("عناوين المستخدمين")
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.label}"

    def save(self, *args, **kwargs):
        # Ensure only one default address per type
        if self.is_default:
            UserAddress.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)

        if self.is_billing_default:
            UserAddress.objects.filter(
                user=self.user,
                is_billing_default=True
            ).exclude(pk=self.pk).update(is_billing_default=False)

        if self.is_shipping_default:
            UserAddress.objects.filter(
                user=self.user,
                is_shipping_default=True
            ).exclude(pk=self.pk).update(is_shipping_default=False)

        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Get full name for this address"""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def formatted_address(self):
        """Get formatted address string"""
        parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ", ".join([part for part in parts if part])


class UserActivity(models.Model):
    """
    نموذج نشاط المستخدم - يتتبع نشاطات المستخدم على الموقع
    User activity model - tracks user activities on the site
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', verbose_name=_("المستخدم"))
    activity_type = models.CharField(_("نوع النشاط"), max_length=50)
    description = models.TextField(_("الوصف"))
    object_id = models.CharField(_("معرف الكائن"), max_length=100, null=True, blank=True)  # تم تغييره من PositiveIntegerField إلى CharField
    content_type = models.CharField(_("نوع المحتوى"), max_length=100, blank=True)
    timestamp = models.DateTimeField(_("التوقيت"), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_("عنوان IP"), null=True, blank=True)

    class Meta:
        verbose_name = _("نشاط المستخدم")
        verbose_name_plural = _("أنشطة المستخدمين")
        ordering = ['-timestamp']