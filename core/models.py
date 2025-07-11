from django.db import models
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField


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
        # ('#2c5282', _('ازرق غامق')),  # Brown
        ('#0357b5', _('ازرق غامق')),  # Brown
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


class Newsletter(models.Model):
    """نموذج لتخزين معلومات المشتركين في النشرة البريدية"""
    email = models.EmailField(_("البريد الإلكتروني"), unique=True)
    is_active = models.BooleanField(_("نشط"), default=True)
    created_at = models.DateTimeField(_("تاريخ الاشتراك"), auto_now_add=True)

    class Meta:
        verbose_name = _("اشتراك في النشرة البريدية")
        verbose_name_plural = _("اشتراكات النشرة البريدية")

    def __str__(self):
        return self.email


class SliderItem(models.Model):
    """
    نموذج عناصر السلايدر - يخزن العناصر المعروضة في السلايدر الرئيسي
    Slider items model - stores items displayed in the main slider
    """
    title = models.CharField(_("العنوان"), max_length=100)
    subtitle = models.CharField(_("العنوان الفرعي"), max_length=150)
    description = models.TextField(_("الوصف"), blank=True)
    image = models.ImageField(_("الصورة"), upload_to='sliders/')

    # زر أساسي
    primary_button_text = models.CharField(_("نص الزر الرئيسي"), max_length=50)
    primary_button_url = models.CharField(_("رابط الزر الرئيسي"), max_length=200)

    # زر ثانوي (اختياري)
    secondary_button_text = models.CharField(_("نص الزر الثانوي"), max_length=50, blank=True)
    secondary_button_url = models.CharField(_("رابط الزر الثانوي"), max_length=200, blank=True)

    # الترتيب والحالة
    order = models.PositiveIntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("عنصر السلايدر")
        verbose_name_plural = _("عناصر السلايدر")
        ordering = ['order']  # ترتيب العناصر حسب الحقل order

    def __str__(self):
        return self.title


class StaticContent(models.Model):
    """
    نموذج للمحتوى الثابت - يتيح تخزين المحتوى باللغات المختلفة
    Static content model - allows storing content in different languages
    """
    key = models.CharField(_("المفتاح"), max_length=100, unique=True)
    content_ar = RichTextField(_("المحتوى بالعربية"))
    content_en = RichTextField(_("المحتوى بالإنجليزية"))
    last_updated = models.DateTimeField(_("آخر تحديث"), auto_now=True)

    class Meta:
        verbose_name = _("محتوى ثابت")
        verbose_name_plural = _("محتويات ثابتة")

    def __str__(self):
        return self.key

    def get_content(self, lang_code=None):
        """
        الحصول على المحتوى حسب رمز اللغة
        Get content based on language code
        """
        if not lang_code:
            from django.utils.translation import get_language
            lang_code = get_language()

        if lang_code == 'en':
            return self.content_en
        return self.content_ar
