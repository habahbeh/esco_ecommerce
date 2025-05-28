from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSettings(models.Model):
    """
    نموذج إعدادات الموقع - يخزن الإعدادات العامة للموقع
    Site settings model - stores general website settings
    """
    site_name = models.CharField(_("اسم الموقع"), max_length=100)
    site_description = models.TextField(_("وصف الموقع"), blank=True)
    logo = models.ImageField(_("الشعار"), upload_to='site/', null=True, blank=True)
    favicon = models.ImageField(_("أيقونة الموقع"), upload_to='site/', null=True, blank=True)
    email = models.EmailField(_("البريد الإلكتروني"), blank=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True)
    address = models.TextField(_("العنوان"), blank=True)
    facebook = models.URLField(_("فيسبوك"), blank=True)
    twitter = models.URLField(_("تويتر"), blank=True)
    instagram = models.URLField(_("انستغرام"), blank=True)
    linkedin = models.URLField(_("لينكد إن"), blank=True)

    # إعدادات المظهر - Appearance settings
    PRIMARY_COLOR_CHOICES = [
        ('#1e88e5', _('أزرق')),  # Blue
        ('#43a047', _('أخضر')),  # Green
        ('#e53935', _('أحمر')),  # Red
        ('#fb8c00', _('برتقالي')),  # Orange
        ('#6d4c41', _('بني')),  # Brown
    ]

    primary_color = models.CharField(
        _("اللون الرئيسي"),
        max_length=7,
        choices=PRIMARY_COLOR_CHOICES,
        default='#1e88e5'
    )

    enable_dark_mode = models.BooleanField(_("تفعيل الوضع الداكن"), default=True)
    default_dark_mode = models.BooleanField(_("الوضع الداكن افتراضيًا"), default=False)

    class Meta:
        verbose_name = _("إعدادات الموقع")
        verbose_name_plural = _("إعدادات الموقع")

    def __str__(self):
        return self.site_name

    @classmethod
    def get_settings(cls):
        """
        الحصول على إعدادات الموقع أو إنشاء إعدادات افتراضية إذا لم تكن موجودة
        Get site settings or create default if not exists
        """
        settings, created = cls.objects.get_or_create(pk=1)
        return settings