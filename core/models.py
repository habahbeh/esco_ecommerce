from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
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
    catalog_ar = models.FileField(_("الكتالوج (عربي)"), upload_to='catalogs/', null=True, blank=True)
    catalog_en = models.FileField(_("Catalog (English)"), upload_to='catalogs/', null=True, blank=True)
    company_profile_ar = models.FileField(_("بروفايل الشركة (عربي)"), upload_to='profiles/', null=True, blank=True)
    company_profile_en = models.FileField(_("Company Profile (English)"), upload_to='profiles/', null=True, blank=True)
    email = models.EmailField(_("البريد الإلكتروني"), blank=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True)
    phone_whatsapp = models.CharField(_("رقم الهاتف واتساب"), max_length=20, blank=True)
    address = models.TextField(_("العنوان"), blank=True)
    facebook = models.URLField(_("فيسبوك"), blank=True)
    twitter = models.URLField(_("تويتر"), blank=True)
    instagram = models.URLField(_("انستغرام"), blank=True)
    linkedin = models.URLField(_("لينكد إن"), blank=True)
    whatsapp = models.URLField(_("واتساب"), blank=True)


    # إعدادات التسويق - Marketing Settings
    gemini_api_key = models.CharField(_("مفتاح OpenRouter API"), max_length=255, blank=True, default='')
    marketing_model = models.CharField(_("نموذج الذكاء الاصطناعي"), max_length=100, blank=True, default='openrouter/free')

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

    # إعدادات الشحن - Shipping Settings
    shipping_fee_amman = models.DecimalField(
        _("أجور النقل - عمان"),
        max_digits=10,
        decimal_places=2,
        default=2.00,
        help_text=_("أجور التوصيل داخل عمان")
    )
    shipping_fee_other = models.DecimalField(
        _("أجور النقل - باقي المحافظات"),
        max_digits=10,
        decimal_places=2,
        default=3.00,
        help_text=_("أجور التوصيل لباقي محافظات الأردن")
    )
    free_shipping_threshold = models.DecimalField(
        _("حد الشحن المجاني"),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_("الحد الأدنى للطلب للحصول على شحن مجاني (0 = لا يوجد شحن مجاني)")
    )
    shipping_enabled = models.BooleanField(
        _("تفعيل أجور الشحن"),
        default=True,
        help_text=_("تفعيل أو إلغاء تفعيل أجور الشحن")
    )
    pickup_enabled = models.BooleanField(
        _("تفعيل الاستلام من الفرع"),
        default=False,
        help_text=_("تفعيل خيار الاستلام من الفرع للعملاء")
    )

    # =================== Default Shipping & Returns Text ===================
    default_shipping_info = models.TextField(
        _("معلومات الشحن الافتراضية"),
        blank=True,
        default='شحن سريع خلال 2-3 أيام عمل داخل عمّان\nشحن خلال 4-5 أيام للمحافظات الأخرى\nإمكانية الشحن الدولي (حسب الوجهة)\nتتبع الشحنة أونلاين\nتغليف آمن ومحكم',
        help_text=_("سطر واحد لكل نقطة")
    )
    default_return_info = models.TextField(
        _("سياسة الإرجاع الافتراضية"),
        blank=True,
        default='إرجاع مجاني خلال 30 يوم\nالمنتج يجب أن يكون في حالته الأصلية\nمع جميع الملحقات والفاتورة الأصلية\nاسترداد المبلغ خلال 7-10 أيام عمل\nإمكانية الاستبدال بمنتج آخر',
        help_text=_("سطر واحد لكل نقطة")
    )

    # =================== Announcement Banner ===================
    show_announcement_banner = models.BooleanField(
        _("إظهار شريط الإعلانات"),
        default=True,
        help_text=_("إظهار أو إخفاء شريط الإعلانات أعلى الموقع")
    )
    announcement_bg_color = models.CharField(
        _("لون خلفية الشريط"),
        max_length=7,
        default='#1b5e20',
        blank=True,
        help_text=_("لون الخلفية بصيغة HEX مثل #1b5e20")
    )
    announcement_icon_1 = models.CharField(
        _("أيقونة 1"),
        max_length=50,
        default='fas fa-truck-fast',
        blank=True,
        help_text=_("كلاس أيقونة Font Awesome مثل fas fa-truck-fast")
    )
    announcement_text_1_ar = models.CharField(
        _("نص 1 (عربي)"),
        max_length=100,
        default='شحن مجاني للطلبات فوق 200 د.أ',
        blank=True,
    )
    announcement_text_1_en = models.CharField(
        _("نص 1 (إنجليزي)"),
        max_length=100,
        default='Free shipping on orders over 200 JOD',
        blank=True,
    )
    announcement_icon_2 = models.CharField(
        _("أيقونة 2"),
        max_length=50,
        default='fas fa-shield-check',
        blank=True,
        help_text=_("كلاس أيقونة Font Awesome")
    )
    announcement_text_2_ar = models.CharField(
        _("نص 2 (عربي)"),
        max_length=100,
        default='منتجات أصلية 100% مع ضمان',
        blank=True,
    )
    announcement_text_2_en = models.CharField(
        _("نص 2 (إنجليزي)"),
        max_length=100,
        default='100% Original products with warranty',
        blank=True,
    )
    announcement_icon_3 = models.CharField(
        _("أيقونة 3"),
        max_length=50,
        default='fas fa-rotate-left',
        blank=True,
        help_text=_("كلاس أيقونة Font Awesome")
    )
    announcement_text_3_ar = models.CharField(
        _("نص 3 (عربي)"),
        max_length=100,
        default='إرجاع سهل',
        blank=True,
    )
    announcement_text_3_en = models.CharField(
        _("نص 3 (إنجليزي)"),
        max_length=100,
        default='Easy returns',
        blank=True,
    )

    # =================== SEO Settings ===================
    seo_title = models.CharField(
        _("عنوان SEO للموقع"),
        max_length=200,
        blank=True,
        help_text=_("العنوان الذي يظهر في نتائج محركات البحث")
    )
    seo_description = models.TextField(
        _("وصف SEO للموقع"),
        max_length=160,
        blank=True,
        help_text=_("الوصف الذي يظهر تحت العنوان في نتائج البحث (150-160 حرف)")
    )
    seo_keywords = models.TextField(
        _("الكلمات المفتاحية العامة"),
        blank=True,
        help_text=_("كلمات مفتاحية مفصولة بفواصل تصف نشاط الموقع")
    )
    google_analytics_id = models.CharField(
        _("معرف Google Analytics"),
        max_length=30,
        blank=True,
        help_text=_("مثال: G-XXXXXXXXXX أو UA-XXXXXXXX-X")
    )
    google_search_console_code = models.CharField(
        _("رمز تحقق Google Search Console"),
        max_length=100,
        blank=True,
        help_text=_("رمز التحقق من ملكية الموقع في Google Search Console")
    )
    og_image = models.ImageField(
        _("صورة المشاركة الافتراضية"),
        upload_to='seo/',
        null=True,
        blank=True,
        help_text=_("الصورة التي تظهر عند مشاركة الموقع على وسائل التواصل (1200x630 بيكسل)")
    )
    enable_structured_data = models.BooleanField(
        _("تفعيل البيانات المنظمة"),
        default=True,
        help_text=_("إضافة بيانات JSON-LD لمحركات البحث (Schema.org)")
    )
    enable_sitemap = models.BooleanField(
        _("تفعيل خريطة الموقع"),
        default=True,
        help_text=_("إنشاء ملف sitemap.xml تلقائياً")
    )
    canonical_domain = models.URLField(
        _("النطاق الأساسي"),
        blank=True,
        help_text=_("النطاق الرئيسي للموقع مثل https://www.example.com")
    )

    class Meta:
        app_label = 'core'
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

    @property
    def default_shipping_info_lines(self):
        if not self.default_shipping_info:
            return []
        return [line.strip() for line in self.default_shipping_info.splitlines() if line.strip()]

    @property
    def default_return_info_lines(self):
        if not self.default_return_info:
            return []
        return [line.strip() for line in self.default_return_info.splitlines() if line.strip()]

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
    """نموذج لتخزين معلومات المشتركين في النشرة البريدية مع التحقق من البريد"""
    email = models.EmailField(_("البريد الإلكتروني"), unique=True)
    name = models.CharField(_("الاسم"), max_length=100, blank=True)
    is_active = models.BooleanField(_("نشط"), default=True)
    is_verified = models.BooleanField(_("تم التحقق"), default=False)
    verification_token = models.CharField(_("رمز التحقق"), max_length=64, blank=True, null=True)
    verification_sent_at = models.DateTimeField(_("تاريخ إرسال التحقق"), blank=True, null=True)
    verified_at = models.DateTimeField(_("تاريخ التحقق"), blank=True, null=True)
    created_at = models.DateTimeField(_("تاريخ الاشتراك"), auto_now_add=True)
    unsubscribe_token = models.CharField(_("رمز إلغاء الاشتراك"), max_length=64, blank=True, null=True)

    # إحصائيات
    emails_received = models.PositiveIntegerField(_("عدد الرسائل المستلمة"), default=0)
    last_email_sent = models.DateTimeField(_("آخر رسالة مرسلة"), blank=True, null=True)

    class Meta:
        app_label = 'core'
        verbose_name = _("اشتراك في النشرة البريدية")
        verbose_name_plural = _("اشتراكات النشرة البريدية")

    def __str__(self):
        return self.email

    def generate_verification_token(self):
        """إنشاء رمز تحقق فريد"""
        import secrets
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token

    def generate_unsubscribe_token(self):
        """إنشاء رمز إلغاء اشتراك فريد"""
        import secrets
        self.unsubscribe_token = secrets.token_urlsafe(32)
        return self.unsubscribe_token


class SliderItem(models.Model):
    """
    نموذج عناصر السلايدر - يخزن العناصر المعروضة في السلايدر الرئيسي
    Slider items model - stores items displayed in the main slider
    """
    title = models.CharField(_("العنوان"), max_length=100)
    title_en = models.CharField(_("Title (EN)"), max_length=100, blank=True)
    subtitle = models.CharField(_("العنوان الفرعي"), max_length=150)
    subtitle_en = models.CharField(_("Subtitle (EN)"), max_length=150, blank=True)
    description = models.TextField(_("الوصف"), blank=True)
    description_en = models.TextField(_("Description (EN)"), blank=True)
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
        app_label = 'core'
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
        app_label = 'core'
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


class Branch(models.Model):
    name = models.CharField(_("اسم الفرع"), max_length=150)
    name_en = models.CharField(_("Branch Name"), max_length=150, blank=True)
    address = models.TextField(_("العنوان"))
    address_en = models.TextField(_("Address"), blank=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True)
    working_hours = models.CharField(_("ساعات العمل"), max_length=200, blank=True)
    working_hours_en = models.CharField(_("Working Hours"), max_length=200, blank=True)
    is_active = models.BooleanField(_("نشط"), default=True)
    sort_order = models.PositiveIntegerField(_("الترتيب"), default=0)

    class Meta:
        app_label = 'core'
        verbose_name = _("فرع")
        verbose_name_plural = _("الفروع")
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class SEOKeyword(models.Model):
    LEVEL_CHOICES = [
        ('site', _('مستوى الموقع')),
        ('category', _('مستوى الفئة')),
        ('product', _('مستوى المنتج')),
        ('competitor', _('منافس')),
    ]
    keyword = models.CharField(_("الكلمة المفتاحية"), max_length=200)
    keyword_en = models.CharField(_("Keyword (English)"), max_length=200, blank=True)
    level = models.CharField(_("المستوى"), max_length=20, choices=LEVEL_CHOICES, default='site')
    category = models.ForeignKey(
        'products.Category', on_delete=models.CASCADE,
        null=True, blank=True, related_name='seo_keywords',
        verbose_name=_("الفئة")
    )
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE,
        null=True, blank=True, related_name='seo_keywords',
        verbose_name=_("المنتج")
    )
    search_volume = models.PositiveIntegerField(_("حجم البحث الشهري"), default=0, blank=True)
    competition = models.CharField(
        _("مستوى المنافسة"),
        max_length=10,
        choices=[('low', _('منخفض')), ('medium', _('متوسط')), ('high', _('عالي'))],
        default='medium'
    )
    is_competitor = models.BooleanField(_("كلمة منافس"), default=False)
    competitor_url = models.URLField(_("رابط المنافس"), blank=True)
    notes = models.TextField(_("ملاحظات"), blank=True)
    is_active = models.BooleanField(_("نشط"), default=True)
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        app_label = 'core'
        verbose_name = _("كلمة مفتاحية SEO")
        verbose_name_plural = _("كلمات مفتاحية SEO")
        ordering = ['-search_volume', 'keyword']
        unique_together = [('keyword', 'level', 'category', 'product')]

    def __str__(self):
        return f"{self.keyword} ({self.get_level_display()})"
