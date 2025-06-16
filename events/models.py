from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
import uuid
import os


def upload_event_image(instance, filename):
    """مسار تحميل صور الفعاليات"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    if hasattr(instance, 'event'):
        return os.path.join('events', str(instance.event.id), filename)
    return os.path.join('events', str(instance.id), filename)


class Event(models.Model):
    """
    نموذج الفعاليات - يخزن بيانات الفعاليات والمعارض
    """
    DISPLAY_CHOICES = [
        ('banner', _('شريط علوي')),
        ('slider', _('معرض شرائح')),
        ('both', _('كلاهما')),
    ]

    title = models.CharField(_("عنوان الفعالية"), max_length=200)
    slug = models.SlugField(_("معرف URL"), max_length=250, unique=True, allow_unicode=True)
    description = models.TextField(_("وصف الفعالية"))
    short_description = models.CharField(_("وصف مختصر"), max_length=255, blank=True,
                                         help_text=_("وصف مختصر للعرض في الشريط العلوي"))

    # التواريخ
    start_date = models.DateTimeField(_("تاريخ البدء"))
    end_date = models.DateTimeField(_("تاريخ الانتهاء"))

    # الموقع
    location = models.CharField(_("الموقع"), max_length=200, blank=True)

    # الصور
    banner_image = models.ImageField(_("صورة الشريط العلوي"), upload_to=upload_event_image,
                                     help_text=_("صورة مصغرة للعرض في الشريط العلوي (مقاس موصى به: 1200×200)"))
    cover_image = models.ImageField(_("صورة الغلاف"), upload_to=upload_event_image,
                                    help_text=_("صورة كبيرة للعرض في معرض الشرائح (مقاس موصى به: 1920×600)"))

    # التحكم بالعرض
    is_active = models.BooleanField(_("نشط"), default=True)
    display_in = models.CharField(_("مكان العرض"), max_length=10, choices=DISPLAY_CHOICES, default='both')
    order = models.PositiveIntegerField(_("الترتيب"), default=0)

    # معلومات إضافية
    registration_url = models.URLField(_("رابط التسجيل"), blank=True)
    button_text = models.CharField(_("نص الزر"), max_length=50, default=_("اعرف المزيد"))

    # التوقيتات
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("فعالية")
        verbose_name_plural = _("الفعاليات")
        ordering = ['order', '-start_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)

        # إذا لم يتم تعيين الوصف المختصر، استخدم جزء من الوصف الكامل
        if not self.short_description and self.description:
            self.short_description = self.description[:200]

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """الحصول على رابط الفعالية"""
        return reverse('events:event_detail', kwargs={'slug': self.slug})

    @property
    def is_upcoming(self):
        """التحقق إذا كانت الفعالية قادمة"""
        from django.utils import timezone
        return self.start_date > timezone.now()

    @property
    def is_ongoing(self):
        """التحقق إذا كانت الفعالية جارية حاليًا"""
        from django.utils import timezone
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    @property
    def status_text(self):
        """نص حالة الفعالية"""
        if self.is_upcoming:
            return _("قادمة")
        elif self.is_ongoing:
            return _("جارية")
        else:
            return _("منتهية")

    @property
    def should_display_banner(self):
        """هل يجب عرض الشريط العلوي؟"""
        return self.is_active and (self.display_in == 'banner' or self.display_in == 'both')

    @property
    def should_display_slider(self):
        """هل يجب العرض في معرض الشرائح؟"""
        return self.is_active and (self.display_in == 'slider' or self.display_in == 'both')


class EventImage(models.Model):
    """
    نموذج صور الفعالية - لتخزين معرض صور متعدد للفعالية
    """
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("الفعالية")
    )

    image = models.ImageField(_("الصورة"), upload_to=upload_event_image)
    caption = models.CharField(_("وصف الصورة"), max_length=200, blank=True)
    order = models.PositiveIntegerField(_("الترتيب"), default=0)

    class Meta:
        verbose_name = _("صورة الفعالية")
        verbose_name_plural = _("صور الفعاليات")
        ordering = ['order']

    def __str__(self):
        return f"{self.event.title} - صورة {self.order}"