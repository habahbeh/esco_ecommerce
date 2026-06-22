from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from ckeditor.fields import RichTextField

import uuid
import os

User = get_user_model()


def upload_blog_image(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('blog', filename)


class BlogCategory(models.Model):
    name = models.CharField(_("اسم التصنيف"), max_length=100)
    name_en = models.CharField(_("Category Name"), max_length=100, blank=True)
    slug = models.SlugField(_("الرابط"), max_length=120, unique=True, allow_unicode=True)
    description = models.TextField(_("الوصف"), blank=True)
    description_en = models.TextField(_("Description"), blank=True)
    icon = models.CharField(_("الأيقونة"), max_length=50, blank=True, help_text=_("Font Awesome class مثل fa-tools"))
    sort_order = models.PositiveIntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("نشط"), default=True)
    meta_title = models.CharField(_("عنوان SEO"), max_length=200, blank=True)
    meta_description = models.TextField(_("وصف SEO"), max_length=160, blank=True)

    class Meta:
        verbose_name = _("تصنيف المدونة")
        verbose_name_plural = _("تصنيفات المدونة")
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:category', kwargs={'slug': self.slug})

    def get_display_name(self, lang='ar'):
        if lang == 'en' and self.name_en:
            return self.name_en
        return self.name


class BlogTag(models.Model):
    name = models.CharField(_("الوسم"), max_length=50)
    name_en = models.CharField(_("Tag"), max_length=50, blank=True)
    slug = models.SlugField(_("الرابط"), max_length=60, unique=True, allow_unicode=True)

    class Meta:
        verbose_name = _("وسم")
        verbose_name_plural = _("الوسوم")
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:tag', kwargs={'slug': self.slug})


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('published', _('منشور')),
        ('archived', _('مؤرشف')),
    ]

    title = models.CharField(_("العنوان"), max_length=250)
    title_en = models.CharField(_("Title"), max_length=250, blank=True)
    slug = models.SlugField(_("الرابط"), max_length=280, unique=True, allow_unicode=True)
    category = models.ForeignKey(
        BlogCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='posts',
        verbose_name=_("التصنيف")
    )
    tags = models.ManyToManyField(BlogTag, blank=True, related_name='posts', verbose_name=_("الوسوم"))
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='blog_posts',
        verbose_name=_("الكاتب")
    )

    excerpt = models.TextField(_("المقتطف"), max_length=300, blank=True, help_text=_("ملخص قصير يظهر في قائمة المقالات"))
    excerpt_en = models.TextField(_("Excerpt"), max_length=300, blank=True)
    content = RichTextField(_("المحتوى"))
    content_en = RichTextField(_("Content"), blank=True)

    featured_image = models.ImageField(_("الصورة الرئيسية"), upload_to=upload_blog_image, null=True, blank=True)
    featured_image_alt = models.CharField(_("وصف الصورة"), max_length=200, blank=True)
    featured_image_alt_en = models.CharField(_("Image Alt"), max_length=200, blank=True)

    card_icon = models.CharField(_("أيقونة البطاقة"), max_length=50, blank=True, default='fa-newspaper',
                                  help_text=_("Font Awesome icon class"))
    card_icon_color = models.CharField(_("لون الأيقونة"), max_length=20, blank=True, default='#2563eb',
                                        help_text=_("كود اللون بصيغة HEX مثل #2563eb"))

    status = models.CharField(_("الحالة"), max_length=10, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(_("مقال مميز"), default=False)
    allow_comments = models.BooleanField(_("السماح بالتعليقات"), default=True)

    views_count = models.PositiveIntegerField(_("عدد المشاهدات"), default=0)
    reading_time = models.PositiveIntegerField(_("وقت القراءة (دقائق)"), default=5)

    # SEO
    meta_title = models.CharField(_("عنوان SEO"), max_length=200, blank=True)
    meta_description = models.TextField(_("وصف SEO"), max_length=160, blank=True)
    meta_keywords = models.CharField(_("كلمات مفتاحية"), max_length=200, blank=True)
    canonical_url = models.URLField(_("الرابط الأساسي"), blank=True)

    related_products = models.ManyToManyField(
        'products.Product', blank=True, related_name='blog_posts',
        verbose_name=_("منتجات ذات صلة")
    )
    related_categories = models.ManyToManyField(
        'products.Category', blank=True, related_name='blog_posts',
        verbose_name=_("فئات ذات صلة")
    )

    published_at = models.DateTimeField(_("تاريخ النشر"), null=True, blank=True)
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("مقال")
        verbose_name_plural = _("المقالات")
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        if self.content:
            word_count = len(strip_tags(self.content).split())
            self.reading_time = max(1, word_count // 200)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def get_display_title(self, lang='ar'):
        if lang == 'en' and self.title_en:
            return self.title_en
        return self.title

    def get_display_content(self, lang='ar'):
        if lang == 'en' and self.content_en:
            return self.content_en
        return self.content

    def get_display_excerpt(self, lang='ar'):
        if lang == 'en' and self.excerpt_en:
            return self.excerpt_en
        return self.excerpt

    def increment_views(self):
        self.__class__.objects.filter(pk=self.pk).update(views_count=models.F('views_count') + 1)

    @classmethod
    def published(cls):
        return cls.objects.filter(status='published', published_at__lte=timezone.now())


class BlogPostFAQ(models.Model):
    post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE,
        related_name='faqs', verbose_name=_("المقال")
    )
    question = models.CharField(_("السؤال"), max_length=300)
    question_en = models.CharField(_("Question"), max_length=300, blank=True)
    answer = models.TextField(_("الإجابة"))
    answer_en = models.TextField(_("Answer"), blank=True)
    sort_order = models.PositiveIntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("سؤال شائع للمقال")
        verbose_name_plural = _("الأسئلة الشائعة للمقالات")
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.post.title[:30]}: {self.question[:50]}"
