# products/models.py
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Avg, Count, Sum, F, Max, Min
from django.core.cache import cache
from django.utils.html import strip_tags
from decimal import Decimal
import os
import uuid
from PIL import Image
import csv
import json
import re

User = get_user_model()


def upload_category_image(instance, filename):
    """Generate upload path for category images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('categories', filename)


def upload_brand_logo(instance, filename):
    """Generate upload path for brand logos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('brands', filename)


def upload_product_image(instance, filename):
    """Generate upload path for product images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    year = timezone.now().year
    month = timezone.now().month
    return os.path.join('products', str(year), str(month), filename)


def upload_review_image(instance, filename):
    """Generate upload path for review images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('reviews', filename)


class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        abstract = True


class SEOModel(models.Model):
    """Abstract base model for SEO fields"""
    meta_title = models.CharField(
        _("عنوان SEO"),
        max_length=200,
        blank=True,
        validators=[MinLengthValidator(5)],
        help_text=_("عنوان الصفحة لمحركات البحث")
    )
    meta_description = models.TextField(
        _("وصف SEO"),
        max_length=160,
        blank=True,
        validators=[MinLengthValidator(20)],
        help_text=_("وصف الصفحة لمحركات البحث")
    )
    meta_keywords = models.CharField(
        _("كلمات مفتاحية SEO"),
        max_length=500,
        blank=True,
        validators=[MinLengthValidator(5)],
        help_text=_("كلمات مفتاحية مفصولة بفواصل")
    )

    class Meta:
        abstract = True


class Category(TimeStampedModel, SEOModel):
    """
    نموذج فئات المنتجات مع دعم التصنيفات الهرمية المحسن
    Enhanced Product categories model with hierarchical support
    """
    # Basic Information
    name = models.CharField(
        _("اسم الفئة"),
        max_length=200,
        validators=[MinLengthValidator(2)],
        help_text=_("اسم الفئة - على الأقل حرفين")
    )
    name_en = models.CharField(
        _("Category Name (English)"),
        max_length=200,
        validators=[MinLengthValidator(2)],
        blank=True,
        help_text=_("English category name (optional)")
    )
    slug = models.SlugField(
        _("معرف URL"),
        max_length=200,
        unique=True,
        allow_unicode=True,
        help_text=_("معرف فريد للرابط")
    )
    description = models.TextField(
        _("الوصف"),
        blank=True,
        validators=[MinLengthValidator(10)],
        help_text=_("وصف الفئة")
    )
    description_en = models.TextField(
        _("Description (English)"),
        blank=True,
        validators=[MinLengthValidator(10)],
        help_text=_("English description (optional)")
    )

    # Hierarchical Structure
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("الفئة الأب")
    )
    level = models.PositiveIntegerField(
        _("المستوى"),
        default=0,
        editable=False,
        help_text=_("مستوى الفئة في الهيكل الشجري")
    )
    sort_order = models.PositiveIntegerField(
        _("ترتيب العرض"),
        default=0,
        help_text=_("ترتيب الفئة في العرض")
    )

    # Visual Content
    image = models.ImageField(
        _("صورة الفئة"),
        upload_to=upload_category_image,
        blank=True,
        null=True,
        help_text=_("صورة تمثيلية للفئة")
    )
    icon = models.CharField(
        _("أيقونة الفئة"),
        max_length=100,
        blank=True,
        help_text=_("CSS class للأيقونة (مثل: fas fa-laptop)")
    )
    color = models.CharField(
        _("لون الفئة"),
        max_length=7,
        blank=True,
        help_text=_("لون سداسي عشري للفئة (مثل: #FF5733)")
    )
    banner_image = models.ImageField(
        _("صورة البانر"),
        upload_to=upload_category_image,
        blank=True,
        null=True,
        help_text=_("صورة بانر للفئة")
    )

    # Display Settings
    is_active = models.BooleanField(_("نشط"), default=True)
    is_featured = models.BooleanField(
        _("فئة مميزة"),
        default=False,
        help_text=_("عرض في الصفحة الرئيسية")
    )
    show_in_menu = models.BooleanField(
        _("عرض في القائمة"),
        default=True,
        help_text=_("عرض في قائمة التنقل الرئيسية")
    )
    show_prices = models.BooleanField(
        _("عرض الأسعار"),
        default=True,
        help_text=_("عرض أسعار المنتجات في هذه الفئة")
    )

    # Statistics
    products_count = models.PositiveIntegerField(
        _("عدد المنتجات"),
        default=0,
        editable=False
    )
    views_count = models.PositiveIntegerField(
        _("عدد المشاهدات"),
        default=0,
        editable=False
    )

    # Business Settings
    commission_rate = models.DecimalField(
        _("نسبة العمولة"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("نسبة العمولة على مبيعات هذه الفئة")
    )

    # Content Management
    content_blocks = models.JSONField(
        _("كتل المحتوى"),
        default=dict,
        blank=True,
        help_text=_("محتوى إضافي للفئة")
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_categories',
        verbose_name=_("أنشئ بواسطة")
    )

    class Meta:
        verbose_name = _("فئة")
        verbose_name_plural = _("الفئات")
        ordering = ['sort_order', 'name']
        unique_together = [['parent', 'name']]
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent', 'is_active']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['level']),
            models.Index(fields=['sort_order']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def clean(self):
        """Custom validation"""
        # Prevent self-parenting
        if self.parent == self:
            raise ValidationError({
                'parent': _("الفئة لا يمكن أن تكون أب لنفسها")
            })

        # Prevent circular references
        if self.parent and self.pk:
            current = self.parent
            while current:
                if current.pk == self.pk:
                    raise ValidationError({
                        'parent': _("لا يمكن إنشاء مرجع دائري في الفئات")
                    })
                current = current.parent

        # Validate color format
        if self.color and not re.match(r'^#[0-9A-Fa-f]{6}$', self.color):
            raise ValidationError({
                'color': _("اللون يجب أن يكون بصيغة سداسية عشرية صحيحة")
            })

        # Validate icon format
        if self.icon and not re.match(r'^[a-zA-Z\s\-]+$', self.icon):
            raise ValidationError({
                'icon': _("أيقونة غير صحيحة")
            })

    def save(self, *args, **kwargs):
        self.full_clean()

        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
            counter = 1
            original_slug = self.slug
            while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        # Calculate level automatically
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0

        # Validate maximum nesting level
        if self.level > 5:
            raise ValidationError(_("لا يمكن تجاوز 5 مستويات في التصنيف"))

        super().save(*args, **kwargs)
        self.update_products_count()
        self.clear_cache()

    def delete(self, *args, **kwargs):
        # Move children to parent or make them root categories
        if self.children.exists():
            self.children.update(parent=self.parent)

        self.clear_cache()
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category_products', kwargs={'category_slug': self.slug})

    def update_products_count(self):
        """Update products count for this category"""
        count = self.products.filter(is_active=True, status='published').count()
        Category.objects.filter(pk=self.pk).update(products_count=count)

        # Update parent counts
        if self.parent:
            self.parent.update_products_count()

    def get_all_children(self, include_self=False):
        """Get all descendant categories recursively"""
        children = []
        if include_self:
            children.append(self)

        for child in self.children.filter(is_active=True):
            children.extend(child.get_all_children(include_self=True))

        return children

    def get_all_parents(self, include_self=False):
        """Get all ancestor categories"""
        parents = []
        if include_self:
            parents.append(self)

        current = self.parent
        while current:
            parents.append(current)
            current = current.parent

        return parents

    def get_breadcrumb(self):
        """Get breadcrumb list"""
        breadcrumb = self.get_all_parents()
        breadcrumb.reverse()
        breadcrumb.append(self)
        return breadcrumb

    @property
    def full_name(self):
        """Get full hierarchical name"""
        names = [cat.name for cat in self.get_breadcrumb()]
        return " > ".join(names)

    @property
    def is_root(self):
        return self.parent is None

    @property
    def is_leaf(self):
        return not self.children.exists()

    @property
    def total_products_count(self):
        """Get total products count including subcategories"""
        cache_key = f"category_total_products_{self.pk}"
        total = cache.get(cache_key)

        if total is None:
            total = self.products_count
            for child in self.get_all_children():
                total += child.products_count
            cache.set(cache_key, total, 3600)  # Cache for 1 hour

        return total

    def get_products(self, include_subcategories=False):
        """Get products in this category"""
        if include_subcategories:
            categories = [self] + self.get_all_children()
            return Product.objects.filter(
                category__in=categories,
                is_active=True,
                status='published'
            )
        else:
            return self.products.filter(is_active=True, status='published')

    def increment_views(self):
        """Increment view count atomically"""
        Category.objects.filter(pk=self.pk).update(
            views_count=F('views_count') + 1
        )
        self.refresh_from_db(fields=['views_count'])

    def clear_cache(self):
        """Clear related cache"""
        cache_keys = [
            f"category_total_products_{self.pk}",
            f"category_tree_{self.pk}",
            "categories_menu",
            "featured_categories",
        ]
        cache.delete_many(cache_keys)

    @classmethod
    def get_tree(cls):
        """Get category tree with caching"""
        cache_key = "category_tree"
        tree = cache.get(cache_key)

        if tree is None:
            tree = cls.objects.filter(is_active=True).select_related('parent')
            cache.set(cache_key, tree, 3600)

        return tree

    @classmethod
    def get_featured_categories(cls):
        """Get featured categories with caching"""
        cache_key = "featured_categories"
        categories = cache.get(cache_key)

        if categories is None:
            categories = list(cls.objects.filter(
                is_featured=True,
                is_active=True
            ).order_by('sort_order'))
            cache.set(cache_key, categories, 3600)

        return categories

    def get_top_products(self, limit=10):
        """Get top products in this category"""
        return self.get_products(include_subcategories=True).order_by(
            '-sales_count', '-views_count'
        )[:limit]

    def get_price_range(self):
        """Get price range for products in this category"""
        products = self.get_products(include_subcategories=True)
        price_range = products.aggregate(
            min_price=Min('base_price'),
            max_price=Max('base_price')
        )
        return price_range

    def __repr__(self):
        return f"<Category: {self.full_name}>"


class Brand(TimeStampedModel, SEOModel):
    """
    نموذج العلامات التجارية المحسن
    Enhanced Brand model
    """
    name = models.CharField(_("اسم العلامة التجارية"), max_length=200)
    name_en = models.CharField(_("Brand Name"), max_length=200, blank=True)
    slug = models.SlugField(_("معرف URL"), max_length=200, unique=True, allow_unicode=True)

    logo = models.ImageField(
        _("الشعار"),
        upload_to=upload_brand_logo,
        blank=True,
        null=True
    )
    banner_image = models.ImageField(
        _("صورة البانر"),
        upload_to=upload_brand_logo,
        blank=True,
        null=True
    )

    website = models.URLField(_("الموقع الإلكتروني"), blank=True)
    email = models.EmailField(_("البريد الإلكتروني"), blank=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True)

    description = models.TextField(_("الوصف"), blank=True)
    history = models.TextField(_("تاريخ العلامة"), blank=True)

    # Location info
    country = models.CharField(_("بلد المنشأ"), max_length=100, blank=True)
    city = models.CharField(_("المدينة"), max_length=100, blank=True)

    # Display settings
    is_featured = models.BooleanField(_("مميز"), default=False)
    is_active = models.BooleanField(_("نشط"), default=True)
    is_verified = models.BooleanField(_("موثق"), default=False)
    sort_order = models.IntegerField(_("الترتيب"), default=0)

    # Social media
    social_links = models.JSONField(_("روابط التواصل"), default=dict, blank=True)

    # Statistics
    products_count = models.PositiveIntegerField(_("عدد المنتجات"), default=0, editable=False)
    views_count = models.PositiveIntegerField(_("عدد المشاهدات"), default=0, editable=False)

    # Rating
    rating = models.DecimalField(
        _("التقييم"),
        max_digits=3,
        decimal_places=2,
        default=0,
        editable=False
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_brands',
        verbose_name=_("أنشئ بواسطة")
    )

    class Meta:
        verbose_name = _("علامة تجارية")
        verbose_name_plural = _("العلامات التجارية")
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['country']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
            counter = 1
            original_slug = self.slug
            while Brand.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)
        self.update_statistics()

    def get_absolute_url(self):
        return reverse('products:brand_detail', kwargs={'slug': self.slug})

    def update_statistics(self):
        """Update brand statistics"""
        products = self.products.filter(is_active=True, status='published')

        # Update products count
        count = products.count()

        # Update rating
        avg_rating = products.aggregate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
        )['avg_rating'] or 0

        Brand.objects.filter(pk=self.pk).update(
            products_count=count,
            rating=avg_rating
        )

    def increment_views(self):
        """Increment view count"""
        Brand.objects.filter(pk=self.pk).update(views_count=F('views_count') + 1)

    def get_top_products(self, limit=10):
        """Get top products for this brand"""
        return self.products.filter(
            is_active=True,
            status='published'
        ).order_by('-sales_count', '-views_count')[:limit]

    def resize_logo(self):
        """Resize logo for optimal performance"""
        if self.logo:
            try:
                img = Image.open(self.logo.path)
                if img.width > 300 or img.height > 300:
                    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    img.save(self.logo.path, optimize=True, quality=85)
            except Exception as e:
                pass  # Log error in production


class Tag(TimeStampedModel):
    """
    نموذج الوسوم المحسن
    Enhanced Tags model
    """
    name = models.CharField(_("اسم الوسم"), max_length=50, unique=True)
    slug = models.SlugField(_("معرف URL"), max_length=50, unique=True, allow_unicode=True)
    description = models.TextField(_("الوصف"), blank=True)
    color = models.CharField(_("اللون"), max_length=7, blank=True)
    icon = models.CharField(_("الأيقونة"), max_length=50, blank=True)

    is_featured = models.BooleanField(_("مميز"), default=False)
    is_active = models.BooleanField(_("نشط"), default=True)

    # Statistics
    products_count = models.PositiveIntegerField(_("عدد المنتجات"), default=0, editable=False)
    usage_count = models.PositiveIntegerField(_("مرات الاستخدام"), default=0, editable=False)

    class Meta:
        verbose_name = _("وسم")
        verbose_name_plural = _("الوسوم")
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['usage_count']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:tag_products', kwargs={'slug': self.slug})

    def update_statistics(self):
        """Update tag statistics"""
        count = self.products.filter(is_active=True, status='published').count()
        Tag.objects.filter(pk=self.pk).update(
            products_count=count,
            usage_count=F('usage_count') + 1
        )


class Product(TimeStampedModel, SEOModel):
    """
    نموذج المنتجات المحسن مع ميزات إضافية
    Enhanced Product model with additional features
    """
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('published', _('منشور')),
        ('archived', _('مؤرشف')),
        ('pending_review', _('قيد المراجعة')),
    ]

    STOCK_STATUS_CHOICES = [
        ('in_stock', _('متوفر')),
        ('out_of_stock', _('غير متوفر')),
        ('pre_order', _('طلب مسبق')),
        ('discontinued', _('متوقف')),
    ]

    CONDITION_CHOICES = [
        ('new', _('جديد')),
        ('refurbished', _('مجدد')),
        ('used', _('مستعمل')),
    ]

    # Basic Information
    name = models.CharField(
        _("اسم المنتج"),
        max_length=500,
        validators=[MinLengthValidator(2)],
        help_text=_("يجب أن يكون اسم المنتج على الأقل حرفين")
    )
    name_en = models.CharField(
        _("Product Name"),
        max_length=500,
        validators=[MinLengthValidator(2)],
        blank=True,
        help_text=_("English product name (optional)")
    )
    slug = models.SlugField(
        _("معرف URL"),
        max_length=500,
        unique=True,
        allow_unicode=True
    )
    sku = models.CharField(
        _("رقم المنتج"),
        max_length=100,
        validators=[MinLengthValidator(3)],
        unique=True,
        help_text=_("رقم المنتج الفريد - على الأقل 3 أحرف")
    )
    barcode = models.CharField(
        _("الباركود"),
        max_length=100,
        validators=[MinLengthValidator(8)],
        blank=True,
        help_text=_("الباركود - على الأقل 8 أرقام")
    )

    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_("الفئة")
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_("العلامة التجارية")
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='products',
        verbose_name=_("الوسوم")
    )

    # Description
    short_description = models.TextField(
        _("وصف مختصر"),
        max_length=500,
        validators=[MinLengthValidator(10)],
        blank=True,
        help_text=_("وصف مختصر للمنتج - على الأقل 10 أحرف")
    )
    description = models.TextField(
        _("الوصف الكامل"),
        validators=[MinLengthValidator(20)],
        help_text=_("وصف مفصل للمنتج - على الأقل 20 حرف")
    )
    specifications = models.JSONField(
        _("المواصفات"),
        default=dict,
        blank=True
    )
    features = models.JSONField(
        _("الميزات"),
        default=list,
        blank=True
    )

    # Pricing
    base_price = models.DecimalField(
        _("السعر الأساسي"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("السعر الأساسي قبل الخصم")
    )
    compare_price = models.DecimalField(
        _("سعر المقارنة"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("السعر للمقارنة (قبل الخصم)")
    )
    cost = models.DecimalField(
        _("التكلفة"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("تكلفة المنتج (اختياري)")
    )

    # Discounts
    discount_percentage = models.DecimalField(
        _("نسبة الخصم"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("نسبة الخصم من 0 إلى 100%")
    )
    discount_amount = models.DecimalField(
        _("مبلغ الخصم"),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("مبلغ الخصم المباشر")
    )
    discount_start = models.DateTimeField(_("بداية الخصم"), null=True, blank=True)
    discount_end = models.DateTimeField(_("نهاية الخصم"), null=True, blank=True)

    # Tax
    tax_rate = models.DecimalField(
        _("نسبة الضريبة"),
        max_digits=5,
        decimal_places=2,
        default=16,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("نسبة الضريبة المضافة")
    )
    tax_class = models.CharField(
        _("فئة الضريبة"),
        max_length=50,
        blank=True,
        help_text=_("فئة الضريبة للمنتج")
    )

    # Inventory
    stock_quantity = models.PositiveIntegerField(
        _("الكمية المتوفرة"),
        default=0,
        help_text=_("الكمية الحالية في المخزون")
    )
    reserved_quantity = models.PositiveIntegerField(
        _("الكمية المحجوزة"),
        default=0,
        help_text=_("الكمية المحجوزة في طلبات معلقة")
    )
    stock_status = models.CharField(
        _("حالة المخزون"),
        max_length=20,
        choices=STOCK_STATUS_CHOICES,
        default='in_stock'
    )
    min_stock_level = models.PositiveIntegerField(
        _("الحد الأدنى للمخزون"),
        default=5,
        validators=[MinValueValidator(1)],
        help_text=_("الحد الأدنى للتنبيه عند نفاد المخزون")
    )
    max_order_quantity = models.PositiveIntegerField(
        _("الحد الأقصى للطلب"),
        default=100,
        validators=[MinValueValidator(1)],
        help_text=_("أقصى كمية يمكن طلبها في مرة واحدة")
    )
    track_inventory = models.BooleanField(
        _("تتبع المخزون"),
        default=True,
        help_text=_("تفعيل/إلغاء تتبع المخزون")
    )

    # Physical attributes
    weight = models.DecimalField(
        _("الوزن (كجم)"),
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text=_("وزن المنتج بالكيلوجرام")
    )
    length = models.DecimalField(
        _("الطول (سم)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("طول المنتج بالسنتيمتر")
    )
    width = models.DecimalField(
        _("العرض (سم)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("عرض المنتج بالسنتيمتر")
    )
    height = models.DecimalField(
        _("الارتفاع (سم)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("ارتفاع المنتج بالسنتيمتر")
    )

    # Product condition and type
    condition = models.CharField(
        _("حالة المنتج"),
        max_length=20,
        choices=CONDITION_CHOICES,
        default='new'
    )

    # Features & Flags
    is_featured = models.BooleanField(_("منتج مميز"), default=False)
    is_new = models.BooleanField(_("منتج جديد"), default=True)
    is_best_seller = models.BooleanField(_("الأكثر مبيعاً"), default=False)
    is_digital = models.BooleanField(_("منتج رقمي"), default=False)
    requires_shipping = models.BooleanField(_("يتطلب شحن"), default=True)
    is_gift_card = models.BooleanField(_("بطاقة هدية"), default=False)

    # Availability
    available_for_preorder = models.BooleanField(_("متاح للطلب المسبق"), default=False)
    preorder_message = models.CharField(
        _("رسالة الطلب المسبق"),
        max_length=200,
        blank=True
    )

    # Warranty
    warranty_period = models.CharField(
        _("فترة الضمان"),
        max_length=50,
        blank=True,
        help_text=_("مثل: سنة واحدة، 6 أشهر")
    )
    warranty_details = models.TextField(_("تفاصيل الضمان"), blank=True)

    # Display settings
    status = models.CharField(
        _("الحالة"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_active = models.BooleanField(_("نشط"), default=True)
    show_price = models.BooleanField(_("عرض السعر"), default=True)
    allow_reviews = models.BooleanField(_("السماح بالتقييمات"), default=True)

    # Related products
    related_products = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        verbose_name=_("منتجات ذات صلة")
    )
    cross_sell_products = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='cross_sold_by',
        verbose_name=_("منتجات البيع المتقاطع")
    )
    upsell_products = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='upsold_by',
        verbose_name=_("منتجات البيع التصاعدي")
    )

    # Statistics
    views_count = models.PositiveIntegerField(_("عدد المشاهدات"), default=0)
    sales_count = models.PositiveIntegerField(_("عدد المبيعات"), default=0)
    wishlist_count = models.PositiveIntegerField(_("عدد قوائم الأمنيات"), default=0)

    # Dates
    published_at = models.DateTimeField(_("تاريخ النشر"), null=True, blank=True)
    featured_until = models.DateTimeField(_("مميز حتى"), null=True, blank=True)

    # Search and SEO
    search_keywords = models.TextField(_("كلمات البحث"), blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products',
        verbose_name=_("أنشئ بواسطة")
    )

    class Meta:
        verbose_name = _("منتج")
        verbose_name_plural = _("المنتجات")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['category', 'brand']),
            models.Index(fields=['-sales_count']),
            models.Index(fields=['-views_count']),
            models.Index(fields=['barcode']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_featured', 'featured_until']),
            models.Index(fields=['stock_status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(base_price__gt=0),
                name='positive_base_price'
            ),
            models.CheckConstraint(
                check=Q(stock_quantity__gte=0),
                name='non_negative_stock'
            ),
            models.CheckConstraint(
                check=Q(reserved_quantity__lte=F('stock_quantity')),
                name='reserved_not_exceed_stock'
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Enhanced validation"""
        # Validate discount logic
        if self.discount_percentage > 0 and self.discount_amount > 0:
            raise ValidationError(_("لا يمكن تطبيق نسبة خصم ومبلغ خصم معاً"))

        if self.discount_amount >= self.base_price:
            raise ValidationError(_("مبلغ الخصم لا يمكن أن يكون أكبر من أو يساوي السعر الأساسي"))

        # Validate discount period
        if self.discount_start and self.discount_end:
            if self.discount_start >= self.discount_end:
                raise ValidationError(_("تاريخ بداية الخصم يجب أن يكون قبل تاريخ النهاية"))

        # Validate dimensions for shipping products
        if self.requires_shipping and not self.is_digital:
            if not all([self.weight, self.length, self.width, self.height]):
                pass  # Warning only, not error

        # Validate stock for digital products
        if self.is_digital and self.track_inventory:
            self.track_inventory = False

    def save(self, *args, **kwargs):
        self.full_clean()

        # Generate slug if not exists
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
            counter = 1
            original_slug = self.slug
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        # Generate SKU if not exists
        if not self.sku:
            self.sku = self.generate_sku()

        # Set published date
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        # Update stock status based on quantity
        if self.track_inventory:
            available_qty = self.stock_quantity - self.reserved_quantity
            if available_qty <= 0:
                self.stock_status = 'out_of_stock'
            elif available_qty <= self.min_stock_level:
                self.stock_status = 'in_stock'  # But will show as low stock
            else:
                self.stock_status = 'in_stock'

        super().save(*args, **kwargs)

        # Update search keywords
        self.update_search_keywords()

        # Clear cache
        self.clear_cache()

    def generate_sku(self):
        """Generate unique SKU"""
        import random
        import string

        prefix = "PRD"
        if self.category and self.category.name:
            prefix = self.category.name[:3].upper()

        while True:
            suffix = ''.join(random.choices(string.digits, k=6))
            sku = f"{prefix}-{suffix}"
            if not Product.objects.filter(sku=sku).exists():
                return sku

    def update_search_keywords(self):
        """Update search keywords automatically"""
        keywords = []

        # Add product name
        keywords.extend(self.name.split())

        # Add category names
        for cat in self.category.get_breadcrumb():
            keywords.extend(cat.name.split())

        # Add brand name
        if self.brand:
            keywords.extend(self.brand.name.split())

        # Add tags
        keywords.extend([tag.name for tag in self.tags.all()])

        # Add specifications
        if self.specifications:
            for key, value in self.specifications.items():
                if isinstance(value, str):
                    keywords.extend(value.split())

        # Clean and deduplicate
        keywords = list(set([
            keyword.lower().strip()
            for keyword in keywords
            if len(keyword) > 2
        ]))

        self.search_keywords = ' '.join(keywords)
        Product.objects.filter(pk=self.pk).update(search_keywords=self.search_keywords)

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    @property
    def current_price(self):
        """Calculate current price with active discount"""
        if self.has_discount:
            if self.discount_percentage > 0:
                discount = self.base_price * (self.discount_percentage / 100)
                return self.base_price - discount
            elif self.discount_amount > 0:
                return self.base_price - self.discount_amount
        return self.base_price

    @property
    def has_discount(self):
        """Check if product has active discount"""
        now = timezone.now()
        has_discount_value = self.discount_percentage > 0 or self.discount_amount > 0

        if not has_discount_value:
            return False

        # Check discount period if set
        if self.discount_start and self.discount_end:
            return self.discount_start <= now <= self.discount_end
        elif self.discount_start:
            return self.discount_start <= now
        elif self.discount_end:
            return now <= self.discount_end

        return True

    @property
    def savings_amount(self):
        """Calculate savings amount"""
        if self.has_discount:
            return self.base_price - self.current_price
        return Decimal('0.00')

    @property
    def savings_percentage(self):
        """Calculate savings percentage"""
        if self.has_discount and self.base_price > 0:
            return int((self.savings_amount / self.base_price) * 100)
        return 0

    @property
    def available_quantity(self):
        """Get available quantity (stock - reserved)"""
        return max(0, self.stock_quantity - self.reserved_quantity)

    @property
    def in_stock(self):
        """Check if product is in stock"""
        if not self.track_inventory:
            return self.stock_status == 'in_stock'
        return self.available_quantity > 0

    @property
    def low_stock(self):
        """Check if stock is low"""
        if self.track_inventory:
            return 0 < self.available_quantity <= self.min_stock_level
        return False

    @property
    def default_image(self):
        """Get default product image"""
        primary_image = self.images.filter(is_primary=True).first()
        if not primary_image:
            primary_image = self.images.first()
        return primary_image

    @property
    def rating(self):
        """Get average rating with caching"""
        cache_key = f"product_rating_{self.pk}"
        rating = cache.get(cache_key)

        if rating is None:
            result = self.reviews.filter(is_approved=True).aggregate(
                avg_rating=Avg('rating')
            )
            rating = result['avg_rating'] or 0
            cache.set(cache_key, rating, 1800)  # Cache for 30 minutes

        return rating

    @property
    def review_count(self):
        """Get review count with caching"""
        cache_key = f"product_review_count_{self.pk}"
        count = cache.get(cache_key)

        if count is None:
            count = self.reviews.filter(is_approved=True).count()
            cache.set(cache_key, count, 1800)

        return count

    # =================== دوال التقييمات الجديدة ===================

    @property
    def average_rating(self):
        """حساب متوسط التقييم - استخدم rating property الموجود"""
        return self.rating

    @property
    def rating_distribution(self):
        """توزيع التقييمات حسب النجوم"""
        distribution = {}
        total = self.review_count

        for i in range(1, 6):
            count = self.reviews.filter(rating=i, is_approved=True).count()
            percentage = (count / total * 100) if total > 0 else 0
            distribution[i] = {
                'count': count,
                'percentage': int(percentage)
            }

        return distribution

    def can_user_review(self, user):
        """التحقق من إمكانية المستخدم إضافة تقييم"""
        if not user.is_authenticated or not self.allow_reviews:
            return False

        # التحقق من عدم وجود تقييم سابق
        return not self.reviews.filter(user=user).exists()

    def get_verified_purchase_status(self, user):
        """التحقق من شراء المستخدم للمنتج"""
        if not user.is_authenticated:
            return False

        # هنا يمكنك إضافة منطق التحقق من الطلبات
        # مثال:
        # from orders.models import Order
        # return Order.objects.filter(
        #     user=user,
        #     items__product=self,
        #     status='completed'
        # ).exists()

        return False  # مؤقتاً

    def get_featured_reviews(self, limit=3):
        """الحصول على التقييمات المميزة"""
        return self.reviews.filter(
            is_approved=True,
            is_featured=True
        ).select_related('user').order_by('-helpful_votes')[:limit]

    def get_recent_reviews(self, limit=5):
        """الحصول على أحدث التقييمات"""
        return self.reviews.filter(
            is_approved=True
        ).select_related('user').order_by('-created_at')[:limit]

    # =================== نهاية دوال التقييمات ===================

    def increment_views(self):
        """Increment view count atomically"""
        Product.objects.filter(pk=self.pk).update(views_count=F('views_count') + 1)
        self.refresh_from_db(fields=['views_count'])

    def increment_sales(self, quantity=1):
        """Increment sales count"""
        Product.objects.filter(pk=self.pk).update(
            sales_count=F('sales_count') + quantity
        )

    def reserve_stock(self, quantity):
        """Reserve stock for an order"""
        if not self.track_inventory:
            return True

        if quantity > self.available_quantity:
            return False

        Product.objects.filter(pk=self.pk).update(
            reserved_quantity=F('reserved_quantity') + quantity
        )
        return True

    def release_stock(self, quantity):
        """Release reserved stock"""
        if not self.track_inventory:
            return

        Product.objects.filter(pk=self.pk).update(
            reserved_quantity=F('reserved_quantity') - quantity
        )

    def reduce_stock(self, quantity):
        """Reduce stock after sale"""
        if not self.track_inventory:
            return

        Product.objects.filter(pk=self.pk).update(
            stock_quantity=F('stock_quantity') - quantity,
            reserved_quantity=F('reserved_quantity') - quantity,
            sales_count=F('sales_count') + quantity
        )

    def can_review(self, user):
        """Check if user can review this product - استخدم can_user_review"""
        return self.can_user_review(user)

    def get_related_products(self, limit=4):
        """Get related products with fallback"""
        related = list(self.related_products.filter(
            is_active=True,
            status='published'
        )[:limit])

        if len(related) < limit:
            # Auto-suggest from same category
            auto_related = Product.objects.filter(
                category=self.category,
                is_active=True,
                status='published'
            ).exclude(
                id__in=[p.id for p in related] + [self.id]
            ).order_by('-sales_count')[:limit - len(related)]

            related.extend(auto_related)

        return related[:limit]

    def get_price_with_tax(self):
        """Get price including tax"""
        price = self.current_price
        tax_amount = price * (self.tax_rate / 100)
        return price + tax_amount

    def clear_cache(self):
        """Clear related cache"""
        cache_keys = [
            f"product_rating_{self.pk}",
            f"product_review_count_{self.pk}",
            f"product_related_{self.pk}",
        ]
        cache.delete_many(cache_keys)

    def get_shipping_weight(self):
        """Get shipping weight (with packaging)"""
        base_weight = self.weight or Decimal('0.5')  # Default 500g
        packaging_weight = Decimal('0.1')  # 100g packaging
        return base_weight + packaging_weight

    @classmethod
    def get_featured_products(cls, limit=10):
        """Get featured products"""
        now = timezone.now()
        return cls.objects.filter(
            is_featured=True,
            is_active=True,
            status='published'
        ).filter(
            Q(featured_until__isnull=True) | Q(featured_until__gte=now)
        ).order_by('-sales_count')[:limit]

    @classmethod
    def get_bestsellers(cls, limit=10):
        """Get bestselling products"""
        return cls.objects.filter(
            is_active=True,
            status='published'
        ).order_by('-sales_count')[:limit]

    @classmethod
    def search(cls, query, filters=None):
        """Advanced search functionality"""
        if not query and not filters:
            return cls.objects.none()

        queryset = cls.objects.filter(is_active=True, status='published')

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(search_keywords__icontains=query) |
                Q(sku__icontains=query) |
                Q(barcode__icontains=query)
            )

        if filters:
            if 'category' in filters:
                queryset = queryset.filter(category__in=filters['category'])
            if 'brand' in filters:
                queryset = queryset.filter(brand__in=filters['brand'])
            if 'price_min' in filters:
                queryset = queryset.filter(base_price__gte=filters['price_min'])
            if 'price_max' in filters:
                queryset = queryset.filter(base_price__lte=filters['price_max'])
            if 'in_stock' in filters and filters['in_stock']:
                queryset = queryset.filter(stock_quantity__gt=0)

        return queryset.distinct()

    def __repr__(self):
        return f"<Product: {self.name} ({self.sku})>"


# Additional models for the enhanced system...

class ProductImage(TimeStampedModel):
    """
    نموذج صور المنتجات المحسن
    Enhanced Product Images model
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("المنتج")
    )
    image = models.ImageField(_("الصورة"), upload_to=upload_product_image)
    alt_text = models.CharField(_("النص البديل"), max_length=200, blank=True)
    caption = models.CharField(_("التسمية التوضيحية"), max_length=200, blank=True)
    is_primary = models.BooleanField(_("صورة رئيسية"), default=False)
    is_360 = models.BooleanField(_("صورة 360 درجة"), default=False)
    sort_order = models.IntegerField(_("الترتيب"), default=0)

    # Image variants for different sizes
    image_thumbnail = models.ImageField(
        _("صورة مصغرة"),
        upload_to=upload_product_image,
        blank=True,
        null=True
    )
    image_medium = models.ImageField(
        _("صورة متوسطة"),
        upload_to=upload_product_image,
        blank=True,
        null=True
    )

    # Color/variant association
    color_code = models.CharField(_("كود اللون"), max_length=7, blank=True)
    variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='images',
        verbose_name=_("المتغير")
    )

    class Meta:
        verbose_name = _("صورة منتج")
        verbose_name_plural = _("صور المنتجات")
        ordering = ['sort_order', '-is_primary']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
            models.Index(fields=['variant']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        return f"{self.product.name} - Image {self.pk}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)

        # Generate image variants
        if self.image and not self.image_thumbnail:
            self.generate_thumbnails()

    def generate_thumbnails(self):
        """Generate thumbnail and medium size images"""
        try:
            from PIL import Image
            import io
            from django.core.files.base import ContentFile

            # Open original image
            img = Image.open(self.image.path)

            # Generate thumbnail (150x150)
            thumb_img = img.copy()
            thumb_img.thumbnail((150, 150), Image.Resampling.LANCZOS)

            thumb_io = io.BytesIO()
            thumb_img.save(thumb_io, format='JPEG', quality=85)

            self.image_thumbnail.save(
                f"thumb_{self.image.name}",
                ContentFile(thumb_io.getvalue()),
                save=False
            )

            # Generate medium size (500x500)
            medium_img = img.copy()
            medium_img.thumbnail((500, 500), Image.Resampling.LANCZOS)

            medium_io = io.BytesIO()
            medium_img.save(medium_io, format='JPEG', quality=90)

            self.image_medium.save(
                f"medium_{self.image.name}",
                ContentFile(medium_io.getvalue()),
                save=False
            )

            # Save without triggering save again
            ProductImage.objects.filter(pk=self.pk).update(
                image_thumbnail=self.image_thumbnail,
                image_medium=self.image_medium
            )

        except Exception as e:
            # Log error in production
            pass

    def get_thumbnail_url(self):
        """Get thumbnail URL with fallback"""
        if self.image_thumbnail:
            return self.image_thumbnail.url
        return self.image.url

    def get_medium_url(self):
        """Get medium size URL with fallback"""
        if self.image_medium:
            return self.image_medium.url
        return self.image.url


# إضافة هذا الكود إلى نهاية ملف products/models.py

class ProductVariant(TimeStampedModel):
    """
    نموذج متغيرات المنتج المحسن
    Enhanced Product Variants model
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_("المنتج")
    )

    # Variant identification
    name = models.CharField(
        _("اسم المتغير"),
        max_length=200,
        help_text=_("مثل: أحمر، كبير، 64 جيجا")
    )
    sku = models.CharField(
        _("رقم المتغير"),
        max_length=100,
        unique=True,
        help_text=_("رقم فريد للمتغير")
    )

    # Variant attributes
    attributes = models.JSONField(
        _("الخصائص"),
        default=dict,
        help_text=_("خصائص المتغير مثل اللون، المقاس، الذاكرة")
    )

    # Pricing (can override product pricing)
    base_price = models.DecimalField(
        _("السعر الأساسي"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("السعر الخاص بهذا المتغير (اختياري)")
    )

    # Inventory
    stock_quantity = models.PositiveIntegerField(
        _("الكمية المتوفرة"),
        default=0
    )
    reserved_quantity = models.PositiveIntegerField(
        _("الكمية المحجوزة"),
        default=0
    )
    track_inventory = models.BooleanField(
        _("تتبع المخزون"),
        default=True
    )

    # Physical attributes
    weight = models.DecimalField(
        _("الوزن (كجم)"),
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.001'))]
    )

    # Settings
    is_active = models.BooleanField(_("نشط"), default=True)
    is_default = models.BooleanField(_("متغير افتراضي"), default=False)
    sort_order = models.IntegerField(_("الترتيب"), default=0)

    class Meta:
        verbose_name = _("متغير منتج")
        verbose_name_plural = _("متغيرات المنتجات")
        ordering = ['sort_order', 'name']
        unique_together = [['product', 'name']]
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def current_price(self):
        """Get current price (variant or product price)"""
        if self.base_price:
            return self.base_price
        return self.product.current_price

    @property
    def available_quantity(self):
        """Get available quantity"""
        return max(0, self.stock_quantity - self.reserved_quantity)

    @property
    def is_in_stock(self):
        """Check if variant is in stock"""
        if not self.track_inventory:
            return True
        return self.available_quantity > 0


class Wishlist(TimeStampedModel):
    """
    نموذج قائمة الأمنيات المحسن
    Enhanced Wishlist model
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlists',
        verbose_name=_("المستخدم")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
        verbose_name=_("المنتج")
    )

    # Optional variant
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("المتغير")
    )

    # Additional info
    notes = models.TextField(
        _("ملاحظات"),
        blank=True,
        help_text=_("ملاحظات شخصية حول المنتج")
    )

    # Notification settings
    notify_on_sale = models.BooleanField(
        _("تنبيه عند الخصم"),
        default=True
    )
    notify_on_restock = models.BooleanField(
        _("تنبيه عند التوفر"),
        default=True
    )

    class Meta:
        verbose_name = _("قائمة أمنيات")
        verbose_name_plural = _("قوائم الأمنيات")
        unique_together = [['user', 'product']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class ProductComparison(TimeStampedModel):
    """
    نموذج مقارنة المنتجات المحسن
    Enhanced Product Comparison model
    """
    session_key = models.CharField(
        _("مفتاح الجلسة"),
        max_length=40,
        help_text=_("مفتاح جلسة المستخدم")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='product_comparisons',
        verbose_name=_("المستخدم")
    )
    products = models.ManyToManyField(
        Product,
        related_name='compared_in',
        verbose_name=_("المنتجات")
    )

    # Settings
    is_public = models.BooleanField(_("مقارنة عامة"), default=False)
    name = models.CharField(
        _("اسم المقارنة"),
        max_length=200,
        blank=True
    )

    class Meta:
        verbose_name = _("مقارنة منتجات")
        verbose_name_plural = _("مقارنات المنتجات")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"مقارنة {self.products.count()} منتجات"


class ProductViewHistory(TimeStampedModel):
    """
    نموذج تاريخ مشاهدة المنتجات
    Product View History model
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='viewed_products',
        verbose_name=_("المستخدم")
    )
    session_key = models.CharField(
        _("مفتاح الجلسة"),
        max_length=40,
        null=True,
        blank=True
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='view_history',
        verbose_name=_("المنتج")
    )
    ip_address = models.GenericIPAddressField(
        _("عنوان IP"),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("تاريخ المشاهدة")
        verbose_name_plural = _("تاريخ المشاهدات")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session_key', 'created_at']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        user_info = self.user.username if self.user else self.session_key
        return f"{user_info} - {self.product.name}"


class ProductAttribute(TimeStampedModel):
    """
    نموذج خصائص المنتجات
    Product Attributes model
    """
    ATTRIBUTE_TYPES = [
        ('text', _('نص')),
        ('number', _('رقم')),
        ('boolean', _('صح/خطأ')),
        ('select', _('اختيار واحد')),
        ('multiselect', _('اختيار متعدد')),
        ('color', _('لون')),
        ('date', _('تاريخ')),
    ]

    name = models.CharField(_("اسم الخاصية"), max_length=100)
    name_en = models.CharField(_("Attribute Name"), max_length=100, blank=True)
    slug = models.SlugField(_("معرف URL"), max_length=100, unique=True)

    attribute_type = models.CharField(
        _("نوع الخاصية"),
        max_length=20,
        choices=ATTRIBUTE_TYPES,
        default='text'
    )

    # For select/multiselect types
    options = models.JSONField(
        _("الخيارات"),
        default=list,
        blank=True,
        help_text=_("خيارات الاختيار للخصائص من نوع select")
    )

    # Display settings
    is_required = models.BooleanField(_("مطلوب"), default=False)
    is_filterable = models.BooleanField(_("قابل للفلترة"), default=True)
    is_searchable = models.BooleanField(_("قابل للبحث"), default=False)

    # Categories that use this attribute
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='attributes',
        verbose_name=_("الفئات")
    )

    sort_order = models.IntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("خاصية منتج")
        verbose_name_plural = _("خصائص المنتجات")
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['attribute_type']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class ProductAttributeValue(TimeStampedModel):
    """
    نموذج قيم خصائص المنتجات
    Product Attribute Values model
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attribute_values',
        verbose_name=_("المنتج")
    )
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name=_("الخاصية")
    )
    value = models.TextField(_("القيمة"))

    class Meta:
        verbose_name = _("قيمة خاصية منتج")
        verbose_name_plural = _("قيم خصائص المنتجات")
        unique_together = [['product', 'attribute']]
        indexes = [
            models.Index(fields=['product', 'attribute']),
            models.Index(fields=['attribute', 'value']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"


class ProductQuestion(TimeStampedModel):
    """
    نموذج أسئلة المنتجات
    Product Questions model
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_("المنتج")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_questions',
        verbose_name=_("المستخدم")
    )

    question = models.TextField(
        _("السؤال"),
        validators=[MinLengthValidator(10)]
    )
    answer = models.TextField(
        _("الإجابة"),
        blank=True
    )

    # Status
    is_answered = models.BooleanField(_("تم الرد"), default=False)
    is_public = models.BooleanField(_("سؤال عام"), default=True)
    is_featured = models.BooleanField(_("سؤال مميز"), default=False)

    # Answer info
    answered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_questions',
        verbose_name=_("أجاب عليه")
    )
    answered_at = models.DateTimeField(_("تاريخ الإجابة"), null=True, blank=True)

    # Voting
    helpful_votes = models.PositiveIntegerField(_("أصوات مفيدة"), default=0)

    class Meta:
        verbose_name = _("سؤال منتج")
        verbose_name_plural = _("أسئلة المنتجات")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'is_public']),
            models.Index(fields=['user']),
            models.Index(fields=['is_answered']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

    def save(self, *args, **kwargs):
        if self.answer and not self.is_answered:
            self.is_answered = True
            self.answered_at = timezone.now()
        super().save(*args, **kwargs)


class ProductSubscription(TimeStampedModel):
    """
    نموذج اشتراكات المنتجات (للتنبيهات)
    Product Subscriptions model
    """
    SUBSCRIPTION_TYPES = [
        ('price_drop', _('انخفاض السعر')),
        ('back_in_stock', _('العودة للمخزون')),
        ('new_review', _('مراجعة جديدة')),
        ('question_answered', _('إجابة سؤال')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_subscriptions',
        verbose_name=_("المستخدم")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_("المنتج")
    )
    subscription_type = models.CharField(
        _("نوع الاشتراك"),
        max_length=20,
        choices=SUBSCRIPTION_TYPES
    )

    # Settings
    is_active = models.BooleanField(_("نشط"), default=True)
    email_notifications = models.BooleanField(_("تنبيهات البريد"), default=True)
    sms_notifications = models.BooleanField(_("تنبيهات الرسائل"), default=False)

    # For price drop subscriptions
    target_price = models.DecimalField(
        _("السعر المستهدف"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("اشتراك منتج")
        verbose_name_plural = _("اشتراكات المنتجات")
        unique_together = [['user', 'product', 'subscription_type']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['product', 'subscription_type']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.get_subscription_type_display()})"


# إضافة هذا الكود لتحديث upload_review_image في أعلى الملف
def upload_review_image(instance, filename):
    """Generate upload path for review images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('reviews', filename)


class ProductReview(TimeStampedModel):
    """
    نموذج تقييمات المنتجات المحسن
    Enhanced Product Reviews model
    """
    # الحقول الأساسية
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_("المنتج")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_reviews',
        verbose_name=_("المستخدم")
    )

    # التقييم والمحتوى
    rating = models.PositiveSmallIntegerField(
        _("التقييم"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("تقييم من 1 إلى 5 نجوم")
    )
    title = models.CharField(
        _("عنوان المراجعة"),
        max_length=200,
        blank=True,
        help_text=_("عنوان مختصر للمراجعة")
    )
    content = models.TextField(
        _("محتوى المراجعة"),
        validators=[MinLengthValidator(10)],
        help_text=_("نص المراجعة - على الأقل 10 أحرف")
    )

    # صورة اختيارية
    image = models.ImageField(
        _("صورة المراجعة"),
        upload_to=upload_review_image,
        blank=True,
        null=True,
        help_text=_("صورة اختيارية مع المراجعة")
    )

    # حالة المراجعة
    is_approved = models.BooleanField(_("معتمد"), default=False)
    is_featured = models.BooleanField(_("مراجعة مميزة"), default=False)

    # التصويت على المراجعة
    helpful_votes = models.PositiveIntegerField(_("أصوات مفيدة"), default=0)
    unhelpful_votes = models.PositiveIntegerField(_("أصوات غير مفيدة"), default=0)

    # الإبلاغ
    report_count = models.PositiveIntegerField(_("عدد البلاغات"), default=0)
    is_spam = models.BooleanField(_("رسالة مزعجة"), default=False)

    # معلومات إضافية
    ip_address = models.GenericIPAddressField(_("عنوان IP"), blank=True, null=True)
    user_agent = models.CharField(_("معرف المتصفح"), max_length=500, blank=True)

    # تقييم فرعي (إضافي)
    quality_rating = models.PositiveSmallIntegerField(
        _("تقييم الجودة"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True
    )
    value_rating = models.PositiveSmallIntegerField(
        _("تقييم القيمة"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True
    )
    delivery_rating = models.PositiveSmallIntegerField(
        _("تقييم التوصيل"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True
    )

    # هل يوصي بالمنتج
    recommend = models.BooleanField(_("يوصي بالمنتج"), default=True)

    # تاريخ الشراء (إذا كان متاحاً)
    purchase_date = models.DateField(_("تاريخ الشراء"), blank=True, null=True)

    # تاريخ التحديث الأخير
    approved_at = models.DateTimeField(_("تاريخ الاعتماد"), blank=True, null=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_reviews',
        verbose_name=_("اعتمد بواسطة")
    )

    class Meta:
        verbose_name = _("مراجعة منتج")
        verbose_name_plural = _("مراجعات المنتجات")
        ordering = ['-created_at']
        unique_together = [['product', 'user']]  # مراجعة واحدة لكل مستخدم لكل منتج
        indexes = [
            models.Index(fields=['product', 'is_approved']),
            models.Index(fields=['user']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_approved', 'created_at']),
            models.Index(fields=['helpful_votes']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"

    def clean(self):
        """التحقق من صحة البيانات"""
        # التحقق من أن المستخدم لم يراجع المنتج من قبل
        if not self.pk:  # فقط للمراجعات الجديدة
            existing_review = ProductReview.objects.filter(
                product=self.product,
                user=self.user
            ).exists()
            if existing_review:
                raise ValidationError(_("لقد قمت بمراجعة هذا المنتج من قبل"))

        # التحقق من أن تاريخ الشراء ليس في المستقبل
        if self.purchase_date and self.purchase_date > timezone.now().date():
            raise ValidationError({
                'purchase_date': _("تاريخ الشراء لا يمكن أن يكون في المستقبل")
            })

    def save(self, *args, **kwargs):
        self.full_clean()

        # تعيين تاريخ الاعتماد إذا تم اعتماد المراجعة
        if self.is_approved and not self.approved_at:
            self.approved_at = timezone.now()

        super().save(*args, **kwargs)

        # تحديث إحصائيات المنتج
        self.update_product_stats()

    def update_product_stats(self):
        """تحديث إحصائيات المنتج"""
        if self.is_approved:
            # إعادة حساب متوسط التقييم
            reviews = ProductReview.objects.filter(
                product=self.product,
                is_approved=True
            )
            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

            # تحديث عدد المراجعات في المنتج إذا كان هناك حقل لذلك
            # Product.objects.filter(pk=self.product.pk).update(avg_rating=avg_rating)

    @property
    def helpful_percentage(self):
        """حساب نسبة الأصوات المفيدة"""
        total_votes = self.helpful_votes + self.unhelpful_votes
        if total_votes == 0:
            return 0
        return int((self.helpful_votes / total_votes) * 100)

    @property
    def total_votes(self):
        """إجمالي الأصوات"""
        return self.helpful_votes + self.unhelpful_votes

    @property
    def is_recent(self):
        """هل المراجعة حديثة (خلال 30 يوم)"""
        from datetime import timedelta
        return self.created_at >= timezone.now() - timedelta(days=30)

    def can_edit(self, user):
        """هل يمكن للمستخدم تعديل المراجعة"""
        if user != self.user:
            return False

        # يمكن التعديل خلال 24 ساعة من الإنشاء
        from datetime import timedelta
        edit_deadline = self.created_at + timedelta(hours=24)
        return timezone.now() <= edit_deadline

    def can_delete(self, user):
        """هل يمكن للمستخدم حذف المراجعة"""
        return user == self.user or user.is_staff

    def get_rating_stars(self):
        """الحصول على النجوم كنص"""
        return "⭐" * self.rating + "☆" * (5 - self.rating)

    @classmethod
    def get_recent_reviews(cls, limit=10):
        """الحصول على أحدث المراجعات المعتمدة"""
        return cls.objects.filter(
            is_approved=True
        ).select_related('user', 'product').order_by('-created_at')[:limit]

    @classmethod
    def get_featured_reviews(cls, limit=5):
        """الحصول على المراجعات المميزة"""
        return cls.objects.filter(
            is_approved=True,
            is_featured=True
        ).select_related('user', 'product').order_by('-helpful_votes')[:limit]


# أضف هذا الكود إلى ملف products/models.py

class ProductDiscount(TimeStampedModel):
    """
    نموذج خصومات المنتجات
    Product Discounts model
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', _('نسبة مئوية')),
        ('fixed_amount', _('مبلغ ثابت')),
        ('buy_x_get_y', _('اشتري X واحصل على Y')),
        ('free_shipping', _('شحن مجاني')),
    ]

    APPLICATION_TYPE_CHOICES = [
        ('all_products', _('جميع المنتجات')),
        ('category', _('فئة محددة')),
        ('specific_products', _('منتجات محددة')),
        ('minimum_purchase', _('حد أدنى للشراء')),
    ]

    # Basic Information
    name = models.CharField(
        _("اسم الخصم"),
        max_length=200,
        help_text=_("اسم وصفي للخصم")
    )
    description = models.TextField(
        _("وصف الخصم"),
        blank=True,
        help_text=_("وصف تفصيلي للخصم")
    )
    code = models.CharField(
        _("كود الخصم"),
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text=_("كود الخصم للعملاء (اختياري)")
    )

    # Discount Configuration
    discount_type = models.CharField(
        _("نوع الخصم"),
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage'
    )
    value = models.DecimalField(
        _("قيمة الخصم"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("نسبة الخصم أو المبلغ الثابت")
    )
    max_discount_amount = models.DecimalField(
        _("الحد الأقصى للخصم"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("الحد الأقصى لمبلغ الخصم (للنسبة المئوية)")
    )

    # Application Settings
    application_type = models.CharField(
        _("نوع التطبيق"),
        max_length=20,
        choices=APPLICATION_TYPE_CHOICES,
        default='all_products'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discounts',
        verbose_name=_("الفئة")
    )
    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name='discounts',
        verbose_name=_("المنتجات")
    )

    # Date Range
    start_date = models.DateTimeField(
        _("تاريخ البداية"),
        help_text=_("تاريخ بداية الخصم")
    )
    end_date = models.DateTimeField(
        _("تاريخ النهاية"),
        null=True,
        blank=True,
        help_text=_("تاريخ نهاية الخصم (اختياري)")
    )

    # Usage Limitations
    min_purchase_amount = models.DecimalField(
        _("الحد الأدنى للشراء"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("الحد الأدنى لمبلغ الشراء لتطبيق الخصم")
    )
    min_quantity = models.PositiveIntegerField(
        _("الحد الأدنى للكمية"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_("الحد الأدنى لكمية المنتجات")
    )
    max_uses = models.PositiveIntegerField(
        _("الحد الأقصى للاستخدام"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_("عدد مرات الاستخدام المسموح (اختياري)")
    )
    max_uses_per_user = models.PositiveIntegerField(
        _("الحد الأقصى للاستخدام لكل مستخدم"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_("عدد مرات الاستخدام لكل مستخدم (اختياري)")
    )

    # Buy X Get Y Configuration
    buy_quantity = models.PositiveIntegerField(
        _("كمية الشراء"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_("كمية المنتجات المطلوب شراؤها")
    )
    get_quantity = models.PositiveIntegerField(
        _("كمية الحصول"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_("كمية المنتجات المجانية")
    )
    get_discount_percentage = models.DecimalField(
        _("نسبة خصم المنتجات المجانية"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100,
        help_text=_("نسبة الخصم على المنتجات المجانية (100% = مجاني)")
    )

    # Status and Settings
    is_active = models.BooleanField(
        _("نشط"),
        default=True,
        help_text=_("تفعيل/إلغاء تفعيل الخصم")
    )
    is_stackable = models.BooleanField(
        _("قابل للتجميع"),
        default=False,
        help_text=_("يمكن تجميعه مع خصومات أخرى")
    )
    requires_coupon_code = models.BooleanField(
        _("يتطلب كود خصم"),
        default=False,
        help_text=_("العميل يجب أن يدخل كود الخصم")
    )
    priority = models.PositiveIntegerField(
        _("الأولوية"),
        default=0,
        help_text=_("أولوية تطبيق الخصم (الأعلى أولاً)")
    )

    # Usage Statistics
    used_count = models.PositiveIntegerField(
        _("عدد مرات الاستخدام"),
        default=0,
        editable=False
    )

    # User Information
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_discounts',
        verbose_name=_("أنشئ بواسطة")
    )

    class Meta:
        verbose_name = _("خصم منتج")
        verbose_name_plural = _("خصومات المنتجات")
        ordering = ['-priority', '-start_date']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_active']),
            models.Index(fields=['application_type']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Validate discount configuration"""
        # Validate date range
        if self.end_date and self.start_date >= self.end_date:
            raise ValidationError({
                'end_date': _("تاريخ النهاية يجب أن يكون بعد تاريخ البداية")
            })

        # Validate discount value based on type
        if self.discount_type == 'percentage' and self.value > 100:
            raise ValidationError({
                'value': _("نسبة الخصم لا يمكن أن تتجاوز 100%")
            })

        # Validate Buy X Get Y configuration
        if self.discount_type == 'buy_x_get_y':
            if not self.buy_quantity or not self.get_quantity:
                raise ValidationError({
                    'buy_quantity': _("يجب تحديد كمية الشراء والحصول لنوع الخصم Buy X Get Y"),
                    'get_quantity': _("يجب تحديد كمية الشراء والحصول لنوع الخصم Buy X Get Y")
                })

        # Validate application type requirements
        if self.application_type == 'category' and not self.category:
            raise ValidationError({
                'category': _("يجب تحديد الفئة عند اختيار نوع التطبيق 'فئة محددة'")
            })

        if self.application_type == 'specific_products' and not self.products.exists():
            raise ValidationError({
                'products': _("يجب تحديد المنتجات عند اختيار نوع التطبيق 'منتجات محددة'")
            })

        # Validate coupon code requirement
        if self.requires_coupon_code and not self.code:
            raise ValidationError({
                'code': _("يجب تحديد كود الخصم عند تفعيل 'يتطلب كود خصم'")
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """Check if discount is currently valid"""
        if not self.is_active:
            return False

        now = timezone.now()
        if self.start_date > now:
            return False

        if self.end_date and self.end_date < now:
            return False

        if self.max_uses and self.used_count >= self.max_uses:
            return False

        return True

    @property
    def is_expired(self):
        """Check if discount is expired"""
        if self.end_date:
            return timezone.now() > self.end_date
        return False

    @property
    def days_remaining(self):
        """Get days remaining until expiry"""
        if not self.end_date:
            return None

        remaining = self.end_date - timezone.now()
        return remaining.days if remaining.days > 0 else 0

    def get_usage_percentage(self):
        """Get usage percentage"""
        if not self.max_uses:
            return 0
        return int((self.used_count / self.max_uses) * 100)

    def can_be_used_by_user(self, user):
        """Check if discount can be used by specific user"""
        if not self.is_valid:
            return False

        if not self.max_uses_per_user:
            return True

        # This would require a DiscountUsage model to track per-user usage
        # For now, return True
        return True

    def applies_to_product(self, product):
        """Check if discount applies to a specific product"""
        if self.application_type == 'all_products':
            return True

        elif self.application_type == 'category':
            if self.category:
                # Check if product is in this category or subcategory
                product_categories = product.category.get_all_parents(include_self=True)
                return self.category in product_categories

        elif self.application_type == 'specific_products':
            return self.products.filter(id=product.id).exists()

        return False

    def calculate_discount_amount(self, original_price, quantity=1):
        """Calculate discount amount for given price and quantity"""
        if not self.is_valid:
            return Decimal('0.00')

        if self.discount_type == 'percentage':
            discount = original_price * (self.value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount

        elif self.discount_type == 'fixed_amount':
            return min(self.value, original_price)

        elif self.discount_type == 'buy_x_get_y':
            if quantity >= self.buy_quantity:
                free_items = (quantity // self.buy_quantity) * self.get_quantity
                free_items = min(free_items, quantity)  # Can't get more free than total
                return original_price * (free_items / quantity) * (self.get_discount_percentage / 100)

        return Decimal('0.00')

    def increment_usage(self):
        """Increment usage count"""
        ProductDiscount.objects.filter(pk=self.pk).update(
            used_count=F('used_count') + 1
        )
        self.refresh_from_db(fields=['used_count'])

    @classmethod
    def get_active_discounts(cls):
        """Get all currently active discounts"""
        now = timezone.now()
        return cls.objects.filter(
            is_active=True,
            start_date__lte=now
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).filter(
            Q(max_uses__isnull=True) | Q(used_count__lt=F('max_uses'))
        ).order_by('-priority')

    @classmethod
    def get_applicable_discounts_for_product(cls, product):
        """Get all discounts applicable to a specific product"""
        active_discounts = cls.get_active_discounts()
        applicable_discounts = []

        for discount in active_discounts:
            if discount.applies_to_product(product):
                applicable_discounts.append(discount)

        return applicable_discounts

    def __repr__(self):
        return f"<ProductDiscount: {self.name} ({self.discount_type})>"


class DiscountUsage(TimeStampedModel):
    """
    نموذج استخدام الخصومات
    Discount Usage tracking model
    """
    discount = models.ForeignKey(
        ProductDiscount,
        on_delete=models.CASCADE,
        related_name='usage_records',
        verbose_name=_("الخصم")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discount_usages',
        verbose_name=_("المستخدم")
    )
    session_key = models.CharField(
        _("مفتاح الجلسة"),
        max_length=40,
        null=True,
        blank=True
    )
    order = models.ForeignKey(
        'orders.Order',  # Assuming you have an Order model
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discount_usages',
        verbose_name=_("الطلب")
    )
    discount_amount = models.DecimalField(
        _("مبلغ الخصم"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    original_amount = models.DecimalField(
        _("المبلغ الأصلي"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    class Meta:
        verbose_name = _("استخدام خصم")
        verbose_name_plural = _("استخدامات الخصومات")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['discount', 'user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        user_info = self.user.username if self.user else self.session_key
        return f"{user_info} - {self.discount.name}"

    @property
    def savings_percentage(self):
        """Calculate savings percentage"""
        if self.original_amount > 0:
            return int((self.discount_amount / self.original_amount) * 100)
        return 0


class ReviewImage(TimeStampedModel):
    """
    نموذج صور التقييمات
    Review Images model
    """
    review = models.ForeignKey(
        ProductReview,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("التقييم")
    )
    image = models.ImageField(
        _("الصورة"),
        upload_to=upload_review_image,
        help_text=_("صورة مرفقة مع التقييم")
    )
    caption = models.CharField(
        _("وصف الصورة"),
        max_length=200,
        blank=True,
        help_text=_("وصف اختياري للصورة")
    )
    sort_order = models.PositiveIntegerField(
        _("الترتيب"),
        default=0
    )

    class Meta:
        verbose_name = _("صورة تقييم")
        verbose_name_plural = _("صور التقييمات")
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['review']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        return f"صورة للتقييم: {self.review.id}"

    def save(self, *args, **kwargs):
        """معالجة الصورة قبل الحفظ"""
        super().save(*args, **kwargs)

        # تحسين حجم الصورة إذا لزم الأمر
        if self.image:
            self.optimize_image()

    def optimize_image(self):
        """تحسين حجم الصورة"""
        try:
            from PIL import Image as PILImage
            import os

            # فتح الصورة
            img = PILImage.open(self.image.path)

            # تحديد الحد الأقصى للأبعاد
            max_size = (1200, 1200)

            # تغيير الحجم إذا كانت أكبر من الحد المسموح
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, PILImage.Resampling.LANCZOS)

                # حفظ الصورة المحسنة
                img.save(self.image.path, optimize=True, quality=85)

        except Exception as e:
            # في حالة الخطأ، تسجيل الخطأ فقط دون إيقاف العملية
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to optimize review image {self.id}: {e}")