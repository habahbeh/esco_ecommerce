from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _


class ChatbotSettings(models.Model):
    PROVIDER_CHOICES = [
        ('openrouter', 'OpenRouter'),
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google Gemini'),
    ]
    POSITION_CHOICES = [
        ('bottom-right', _('أسفل اليمين')),
        ('bottom-left', _('أسفل اليسار')),
    ]
    BUBBLE_SIZE_CHOICES = [
        ('small', _('صغير')),
        ('medium', _('متوسط')),
        ('large', _('كبير')),
    ]
    PRODUCT_STATUS_CHOICES = [
        ('published_only', _('المنشورة فقط')),
        ('published_and_draft', _('المنشورة والمسودة')),
        ('all', _('الكل')),
    ]
    PRODUCT_SORT_CHOICES = [
        ('newest', _('الأحدث أولاً')),
        ('price_low', _('السعر: من الأقل للأعلى')),
        ('price_high', _('السعر: من الأعلى للأقل')),
        ('name', _('الاسم أبجدياً')),
    ]
    VOICE_PROVIDER_CHOICES = [
        ('browser', _('متصفح (مجاني)')),
        ('openai', 'OpenAI'),
        ('elevenlabs', 'ElevenLabs'),
        ('google', 'Google Cloud'),
        ('azure', 'Azure'),
        ('custom', _('مخصص (أي منصة)')),
    ]
    VOICE_LANGUAGE_CHOICES = [
        ('ar-SA', _('العربية (السعودية)')),
        ('ar-JO', _('العربية (الأردن)')),
        ('ar-EG', _('العربية (مصر)')),
        ('ar-AE', _('العربية (الإمارات)')),
        ('en-US', _('الإنجليزية (أمريكا)')),
        ('en-GB', _('الإنجليزية (بريطانيا)')),
    ]

    is_enabled = models.BooleanField(_("تفعيل الشات بوت"), default=False)

    provider = models.CharField(_("مزود الذكاء الاصطناعي"), max_length=20, choices=PROVIDER_CHOICES, default='openrouter')
    api_key = models.CharField(_("مفتاح API"), max_length=500, blank=True, default='')
    model_name = models.CharField(_("اسم النموذج"), max_length=200, default='openrouter/free')
    temperature = models.DecimalField(_("درجة الإبداع"), max_digits=3, decimal_places=2, default=0.7)
    max_tokens = models.PositiveIntegerField(_("الحد الأقصى للتوكنات"), default=1024)

    primary_color = models.CharField(_("اللون الرئيسي"), max_length=7, default='#1e88e5')
    secondary_color = models.CharField(_("اللون الثانوي"), max_length=7, default='#ffffff')
    position = models.CharField(_("موقع الفقاعة"), max_length=20, choices=POSITION_CHOICES, default='bottom-right')
    bubble_size = models.CharField(_("حجم الفقاعة"), max_length=10, choices=BUBBLE_SIZE_CHOICES, default='medium')
    show_on_mobile = models.BooleanField(_("إظهار على الجوال"), default=True)
    welcome_message_ar = models.TextField(_("رسالة الترحيب (عربي)"), default='مرحباً! كيف يمكنني مساعدتك اليوم؟')
    welcome_message_en = models.TextField(_("رسالة الترحيب (إنجليزي)"), default='Hello! How can I help you today?')
    bot_name_ar = models.CharField(_("اسم البوت (عربي)"), max_length=50, default='مساعد ESCO')
    bot_name_en = models.CharField(_("اسم البوت (إنجليزي)"), max_length=50, default='ESCO Assistant')
    avatar = models.ImageField(_("صورة البوت"), upload_to='chatbot/', null=True, blank=True)
    avatar_icon = models.CharField(_("أيقونة البوت"), max_length=50, blank=True, default='fas fa-robot')
    avatar_icon_color = models.CharField(_("لون أيقونة البوت"), max_length=7, blank=True, default='#ffffff')
    bubble_icon = models.CharField(_("أيقونة الفقاعة"), max_length=50, blank=True, default='fas fa-comments')
    bubble_icon_color = models.CharField(_("لون أيقونة الفقاعة"), max_length=7, blank=True, default='#ffffff')
    bubble_bg_color = models.CharField(_("لون خلفية الفقاعة"), max_length=7, blank=True, default='#1e88e5')

    system_prompt_ar = models.TextField(_("تعليمات النظام (عربي)"), blank=True, default='')
    system_prompt_en = models.TextField(_("تعليمات النظام (إنجليزي)"), blank=True, default='')
    max_history_messages = models.PositiveIntegerField(_("عدد الرسائل في السياق"), default=10)
    enable_product_search = models.BooleanField(_("تفعيل البحث في المنتجات"), default=True)
    enable_blog_search = models.BooleanField(_("تفعيل البحث في المدونة"), default=True)
    enable_comparison = models.BooleanField(_("تفعيل مقارنة المنتجات"), default=True)
    enable_suggestions = models.BooleanField(_("تفعيل الاقتراحات الذكية"), default=True)

    show_categories_in_response = models.BooleanField(_("عرض الأقسام في الرد"), default=True)
    product_status_filter = models.CharField(_("فلتر حالة المنتج"), max_length=20, choices=PRODUCT_STATUS_CHOICES, default='published_only')
    hide_products_without_price = models.BooleanField(_("إخفاء المنتجات بدون سعر"), default=True)
    hide_out_of_stock = models.BooleanField(_("إخفاء المنتجات غير المتوفرة"), default=False)
    show_price_in_response = models.BooleanField(_("عرض السعر في الرد"), default=True)
    product_sort_order = models.CharField(_("ترتيب المنتجات"), max_length=20, choices=PRODUCT_SORT_CHOICES, default='newest')

    enable_voice_input = models.BooleanField(_("تفعيل الإدخال الصوتي"), default=False)
    enable_voice_output = models.BooleanField(_("تفعيل الرد الصوتي"), default=False)
    voice_provider = models.CharField(_("مزود الصوت"), max_length=20, choices=VOICE_PROVIDER_CHOICES, default='browser')
    voice_api_key = models.CharField(_("مفتاح API للصوت"), max_length=500, blank=True, default='')
    voice_language = models.CharField(_("لغة الصوت"), max_length=10, choices=VOICE_LANGUAGE_CHOICES, default='ar-SA')
    voice_id = models.CharField(_("معرّف الصوت"), max_length=200, blank=True, default='',
                                help_text=_('معرّف الصوت لدى المزود (مثل: alloy لـ OpenAI أو معرّف ElevenLabs)'))
    auto_play_voice = models.BooleanField(_("تشغيل الصوت تلقائياً"), default=False)

    custom_voice_tts_url = models.URLField(_("رابط API للنطق (TTS)"), max_length=500, blank=True, default='',
                                           help_text=_('مثال: https://api.lahajati.ai/v1/tts'))
    custom_voice_stt_url = models.URLField(_("رابط API للتعرف على الصوت (STT)"), max_length=500, blank=True, default='',
                                           help_text=_('مثال: https://api.lahajati.ai/v1/stt'))
    custom_voice_auth_header = models.CharField(_("اسم هيدر المصادقة"), max_length=100, blank=True, default='Authorization',
                                                help_text=_('مثال: Authorization أو x-api-key أو xi-api-key'))
    custom_voice_auth_prefix = models.CharField(_("بادئة المصادقة"), max_length=50, blank=True, default='Bearer',
                                                help_text=_('مثال: Bearer أو Token أو اتركه فارغاً'))
    custom_voice_tts_body = models.TextField(_("قالب Body للنطق (JSON)"), blank=True, default='',
                                             help_text=_('JSON template — استخدم {text} و {voice_id} و {language} كمتغيرات'))
    custom_voice_stt_field = models.CharField(_("اسم حقل الملف الصوتي"), max_length=50, blank=True, default='file',
                                              help_text=_('اسم الحقل في multipart/form-data (مثال: file أو audio)'))
    custom_voice_response_path = models.CharField(_("مسار النص في الرد"), max_length=200, blank=True, default='text',
                                                   help_text=_('مسار JSON للنص المُحوَّل (مثال: text أو result.transcript أو data.text)'))

    max_messages_per_session = models.PositiveIntegerField(_("الحد الأقصى لرسائل الجلسة"), default=50)
    rate_limit_per_minute = models.PositiveIntegerField(_("الحد الأقصى للرسائل بالدقيقة"), default=10)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('إعدادات الشات بوت')
        verbose_name_plural = _('إعدادات الشات بوت')

    def __str__(self):
        return "Chatbot Settings"

    @classmethod
    def get_settings(cls):
        obj = cache.get('chatbot_settings')
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set('chatbot_settings', obj, 3600)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete('chatbot_settings')


class Conversation(models.Model):
    session_key = models.CharField(_("مفتاح الجلسة"), max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("المستخدم"),
        null=True, blank=True, on_delete=models.SET_NULL, related_name='chatbot_conversations'
    )
    language = models.CharField(_("اللغة"), max_length=5, default='ar')
    started_at = models.DateTimeField(_("بدأت في"), auto_now_add=True)
    updated_at = models.DateTimeField(_("آخر تحديث"), auto_now=True)
    is_active = models.BooleanField(_("نشطة"), default=True)
    page_url = models.URLField(_("صفحة المحادثة"), max_length=500, blank=True, default='')

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('محادثة')
        verbose_name_plural = _('المحادثات')
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        return f"Conversation #{self.pk} ({self.session_key[:8]}...)"


class Message(models.Model):
    ROLE_CHOICES = [
        ('user', _('المستخدم')),
        ('assistant', _('المساعد')),
    ]

    conversation = models.ForeignKey(Conversation, verbose_name=_("المحادثة"), related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(_("الدور"), max_length=10, choices=ROLE_CHOICES)
    content = models.TextField(_("المحتوى"))
    rich_content = models.JSONField(_("محتوى غني"), default=dict, blank=True)
    tokens_used = models.PositiveIntegerField(_("التوكنات المستخدمة"), default=0)
    response_time_ms = models.PositiveIntegerField(_("وقت الاستجابة (مللي ثانية)"), default=0)
    provider_used = models.CharField(_("المزود"), max_length=50, blank=True, default='')
    model_used = models.CharField(_("النموذج"), max_length=200, blank=True, default='')
    created_at = models.DateTimeField(_("أنشئت في"), auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('رسالة')
        verbose_name_plural = _('الرسائل')
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class CustomQA(models.Model):
    question_ar = models.CharField(_("السؤال (عربي)"), max_length=500)
    question_en = models.CharField(_("السؤال (إنجليزي)"), max_length=500, blank=True, default='')
    answer_ar = models.TextField(_("الإجابة (عربي)"))
    answer_en = models.TextField(_("الإجابة (إنجليزي)"), blank=True, default='')
    keywords = models.CharField(_("كلمات مفتاحية"), max_length=500, blank=True, default='',
                                help_text=_('كلمات مفتاحية مفصولة بفواصل للمطابقة'))
    is_active = models.BooleanField(_("نشط"), default=True)
    priority = models.PositiveIntegerField(_("الأولوية"), default=0, help_text=_('رقم أعلى = أولوية أعلى'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-updated_at']
        verbose_name = _('سؤال وجواب مخصص')
        verbose_name_plural = _('أسئلة وأجوبة مخصصة')

    def __str__(self):
        return self.question_ar[:80]


class SuggestedQuestion(models.Model):
    text_ar = models.CharField(_("النص (عربي)"), max_length=200)
    text_en = models.CharField(_("النص (إنجليزي)"), max_length=200, blank=True, default='')
    icon = models.CharField(_("أيقونة"), max_length=50, blank=True, default='fas fa-question-circle')
    order = models.PositiveIntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        ordering = ['order']
        verbose_name = _('سؤال مقترح')
        verbose_name_plural = _('الأسئلة المقترحة')

    def __str__(self):
        return self.text_ar[:80]


class LeadRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', _('قيد المراجعة')),
        ('contacted', _('تم التواصل')),
        ('in_progress', _('قيد المتابعة')),
        ('completed', _('مكتمل')),
        ('cancelled', _('ملغي')),
    ]

    conversation = models.ForeignKey(
        Conversation, verbose_name=_("المحادثة"),
        null=True, blank=True, on_delete=models.SET_NULL, related_name='lead_requests'
    )
    customer_name = models.CharField(_("اسم العميل"), max_length=200)
    customer_phone = models.CharField(_("رقم الهاتف"), max_length=30)
    customer_address = models.TextField(_("العنوان"), blank=True, default='')
    expected_date = models.CharField(_("التاريخ المتوقع للاستلام"), max_length=100, blank=True, default='')
    product_interest = models.TextField(_("المنتج / الاهتمام"), blank=True, default='')
    notes = models.TextField(_("ملاحظات العميل"), blank=True, default='')

    status = models.CharField(_("الحالة"), max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("مسؤول المتابعة"),
        null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_leads'
    )
    language = models.CharField(_("اللغة"), max_length=5, default='ar')
    session_key = models.CharField(_("مفتاح الجلسة"), max_length=64, blank=True, default='')
    page_url = models.URLField(_("صفحة المحادثة"), max_length=500, blank=True, default='')

    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("آخر تحديث"), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('طلب عميل')
        verbose_name_plural = _('طلبات العملاء')
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.get_status_display()}"


class LeadComment(models.Model):
    lead = models.ForeignKey(LeadRequest, verbose_name=_("الطلب"), related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("الموظف"),
        on_delete=models.CASCADE, related_name='lead_comments'
    )
    content = models.TextField(_("التعليق"))
    old_status = models.CharField(_("الحالة السابقة"), max_length=20, blank=True, default='')
    new_status = models.CharField(_("الحالة الجديدة"), max_length=20, blank=True, default='')
    created_at = models.DateTimeField(_("تاريخ التعليق"), auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('تعليق')
        verbose_name_plural = _('التعليقات')

    def __str__(self):
        return f"{self.user} - {self.content[:50]}"
