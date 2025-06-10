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
        ('#2c5282', _('ازرق غامق')),  # Brown
    ]

    primary_color = models.CharField(
        _("اللون الرئيسي"),
        max_length=7,
        choices=PRIMARY_COLOR_CHOICES,
        default='#1e88e5'
    )

    # إضافة حقل جديد لتخزين قيمة RGB
    primary_color_rgb = models.CharField(
        _("اللون الرئيسي (RGB)"),
        max_length=15,
        blank=True,
        editable=False  # لا يمكن تعديله يدوياً
    )

    enable_dark_mode = models.BooleanField(_("تفعيل الوضع الداكن"), default=True)
    default_dark_mode = models.BooleanField(_("الوضع الداكن افتراضيًا"), default=False)

    class Meta:
        verbose_name = _("إعدادات الموقع")
        verbose_name_plural = _("إعدادات الموقع")

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # تحويل لون الهيكس إلى RGB قبل الحفظ
        if self.primary_color:
            hex_color = self.primary_color.lstrip('#')
            try:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                self.primary_color_rgb = f"{r}, {g}, {b}"
            except (ValueError, IndexError):
                # في حالة حدوث خطأ، استخدام القيمة الافتراضية
                self.primary_color_rgb = "30, 136, 229"  # أزرق افتراضي

        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """
        الحصول على إعدادات الموقع أو إنشاء إعدادات افتراضية إذا لم تكن موجودة
        Get site settings or create default if not exists
        """
        settings = None

        # محاولة الحصول على الإعدادات المستخدمة حالياً (ID=2)
        try:
            settings = cls.objects.get(pk=2)
        except cls.DoesNotExist:
            # محاولة الحصول على أي إعدادات
            settings = cls.objects.first()
            if not settings:
                # إنشاء إعدادات جديدة إذا لم توجد أي إعدادات
                settings = cls.objects.create(site_name="ESCO")

        return settings