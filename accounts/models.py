from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    نموذج المستخدم المخصص - يمتد من نموذج المستخدم الأساسي في Django
    Custom user model - extends Django's built-in user model
    """
    email = models.EmailField(_("البريد الإلكتروني"), unique=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True)
    avatar = models.ImageField(_("الصورة الشخصية"), upload_to='avatars/', null=True, blank=True)
    address = models.TextField(_("العنوان"), blank=True)

    # إضافة حقول إضافية للمستخدم - Additional user fields
    is_product_manager = models.BooleanField(_("مدير منتجات"), default=False)
    is_product_reviewer = models.BooleanField(_("مراجع منتجات"), default=False)

    class Meta:
        verbose_name = _("مستخدم")
        verbose_name_plural = _("المستخدمون")

    def __str__(self):
        return self.get_full_name() or self.username


class UserActivity(models.Model):
    """
    نموذج نشاط المستخدم - يتتبع نشاطات المستخدم على الموقع
    User activity model - tracks user activities on the site
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', verbose_name=_("المستخدم"))
    activity_type = models.CharField(_("نوع النشاط"), max_length=50)
    description = models.TextField(_("الوصف"))
    object_id = models.PositiveIntegerField(_("معرف الكائن"), null=True, blank=True)
    content_type = models.CharField(_("نوع المحتوى"), max_length=100, blank=True)
    timestamp = models.DateTimeField(_("التوقيت"), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_("عنوان IP"), null=True, blank=True)

    class Meta:
        verbose_name = _("نشاط المستخدم")
        verbose_name_plural = _("أنشطة المستخدمين")
        ordering = ['-timestamp']