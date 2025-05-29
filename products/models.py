from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import os
from PIL import Image
from django.core.validators import MinLengthValidator

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from decimal import Decimal


User = get_user_model()


class Category(models.Model):
    """
    نموذج فئات المنتجات مع دعم التصنيفات الهرمية
    Product categories model with hierarchical support
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
        upload_to='categories/',
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

    # SEO & Marketing
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

    # Commission & Business
    commission_rate = models.DecimalField(
        _("نسبة العمولة"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("نسبة العمولة على مبيعات هذه الفئة")
    )

    # Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
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
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def clean(self):
        """Custom validation"""
        from django.core.exceptions import ValidationError

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
        if self.color and not self.color.startswith('#'):
            raise ValidationError({
                'color': _("اللون يجب أن يبدأ بـ #")
            })

    def save(self, *args, **kwargs):
        self.full_clean()

        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)

            # Ensure slug uniqueness
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

        # Validate maximum nesting level (prevent too deep nesting)
        if self.level > 5:  # Maximum 5 levels
            raise ValidationError(_("لا يمكن تجاوز 5 مستويات في التصنيف"))

        super().save(*args, **kwargs)

        # Update products count
        self.update_products_count()

    def delete(self, *args, **kwargs):
        # Move children to parent or make them root categories
        if self.children.exists():
            self.children.update(parent=self.parent)

        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'slug': self.slug})

    def update_products_count(self):
        """Update products count for this category"""
        from django.db import models
        count = self.products.filter(is_active=True, status='published').count()
        Category.objects.filter(pk=self.pk).update(products_count=count)

    def get_all_children(self, include_self=False):
        """Get all descendant categories"""
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
        """Check if this is a root category"""
        return self.parent is None

    @property
    def is_leaf(self):
        """Check if this is a leaf category (no children)"""
        return not self.children.exists()

    @property
    def total_products_count(self):
        """Get total products count including subcategories"""
        total = self.products_count
        for child in self.get_all_children():
            total += child.products_count
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
        """Increment view count"""
        Category.objects.filter(pk=self.pk).update(
            views_count=models.F('views_count') + 1
        )
        self.refresh_from_db(fields=['views_count'])

    @classmethod
    def get_root_categories(cls):
        """Get all root categories"""
        return cls.objects.filter(parent__isnull=True, is_active=True)

    @classmethod
    def get_featured_categories(cls):
        """Get featured categories"""
        return cls.objects.filter(is_featured=True, is_active=True)

    @classmethod
    def get_menu_categories(cls):
        """Get categories for menu display"""
        return cls.objects.filter(
            show_in_menu=True,
            is_active=True
        ).select_related('parent').prefetch_related('children')

    def get_image_url(self):
        """Get category image URL"""
        if self.image:
            return self.image.url
        return None

    def __repr__(self):
        return f"<Category: {self.full_name}>"


class Brand(models.Model):
    """
    نموذج العلامات التجارية
    """
    name = models.CharField(_("اسم العلامة التجارية"), max_length=200)
    name_en = models.CharField(_("Brand Name"), max_length=200, blank=True)
    slug = models.SlugField(_("معرف URL"), max_length=200, unique=True, allow_unicode=True)
    logo = models.ImageField(_("الشعار"), upload_to='brands/', blank=True, null=True)
    website = models.URLField(_("الموقع الإلكتروني"), blank=True)
    description = models.TextField(_("الوصف"), blank=True)

    # Additional info
    country = models.CharField(_("بلد المنشأ"), max_length=100, blank=True)
    is_featured = models.BooleanField(_("مميز"), default=False)
    is_active = models.BooleanField(_("نشط"), default=True)
    order = models.IntegerField(_("الترتيب"), default=0)

    # Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("علامة تجارية")
        verbose_name_plural = _("العلامات التجارية")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def resize_logo(self):
        """تغيير حجم الشعار للحفاظ على الأداء"""
        if self.logo:
            img = Image.open(self.logo.path)
            if img.width > 300 or img.height > 300:
                img.thumbnail((300, 300))
                img.save(self.logo.path)



class Product(models.Model):
    """
    نموذج المنتجات المحسّن
    """
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('published', _('منشور')),
        ('archived', _('مؤرشف')),
    ]

    STOCK_STATUS_CHOICES = [
        ('in_stock', _('متوفر')),
        ('out_of_stock', _('غير متوفر')),
        ('pre_order', _('طلب مسبق')),
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
        'Category',  # Using string reference to avoid import issues
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_("الفئة")
    )
    brand = models.ForeignKey(
        'Brand',  # Using string reference to avoid import issues
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_("العلامة التجارية")
    )
    tags = models.ManyToManyField(
        'Tag',
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
    short_description_en = models.TextField(
        _("Short Description"),
        max_length=500,
        validators=[MinLengthValidator(10)],
        blank=True,
        help_text=_("Short English description (optional)")
    )
    description = models.TextField(
        _("الوصف الكامل"),
        validators=[MinLengthValidator(20)],
        help_text=_("وصف مفصل للمنتج - على الأقل 20 حرف")
    )
    description_en = models.TextField(
        _("Full Description"),
        validators=[MinLengthValidator(20)],
        blank=True,
        help_text=_("Full English description (optional)")
    )
    specifications = models.JSONField(
        _("المواصفات"),
        default=dict,
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
    tax_rate = models.DecimalField(
        _("نسبة الضريبة"),
        max_digits=5,
        decimal_places=2,
        default=16,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("نسبة الضريبة المضافة")
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

    # Inventory
    stock_quantity = models.PositiveIntegerField(
        _("الكمية المتوفرة"),
        default=0,
        help_text=_("الكمية الحالية في المخزون")
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

    # Features & Flags
    is_featured = models.BooleanField(_("منتج مميز"), default=False)
    is_new = models.BooleanField(_("منتج جديد"), default=True)
    is_best_seller = models.BooleanField(_("الأكثر مبيعاً"), default=False)
    is_digital = models.BooleanField(_("منتج رقمي"), default=False)
    requires_shipping = models.BooleanField(_("يتطلب شحن"), default=True)

    # Display settings
    status = models.CharField(
        _("الحالة"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_active = models.BooleanField(_("نشط"), default=True)
    show_price = models.BooleanField(_("عرض السعر"), default=True)

    # SEO
    meta_title = models.CharField(
        _("عنوان SEO"),
        max_length=200,
        validators=[MinLengthValidator(5)],
        blank=True,
        help_text=_("عنوان الصفحة لمحركات البحث")
    )
    meta_description = models.TextField(
        _("وصف SEO"),
        max_length=160,
        validators=[MinLengthValidator(20)],
        blank=True,
        help_text=_("وصف الصفحة لمحركات البحث")
    )
    meta_keywords = models.CharField(
        _("كلمات مفتاحية SEO"),
        max_length=500,
        validators=[MinLengthValidator(5)],
        blank=True,
        help_text=_("كلمات مفتاحية مفصولة بفواصل")
    )

    # Related products
    related_products = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        verbose_name=_("منتجات ذات صلة")
    )

    # Statistics
    views_count = models.PositiveIntegerField(_("عدد المشاهدات"), default=0)
    sales_count = models.PositiveIntegerField(_("عدد المبيعات"), default=0)

    # Dates
    published_at = models.DateTimeField(_("تاريخ النشر"), null=True, blank=True)
    discount_start = models.DateTimeField(_("بداية الخصم"), null=True, blank=True)
    discount_end = models.DateTimeField(_("نهاية الخصم"), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
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
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(base_price__gt=0),
                name='positive_base_price'
            ),
            models.CheckConstraint(
                check=models.Q(stock_quantity__gte=0),
                name='non_negative_stock'
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Custom validation"""
        from django.core.exceptions import ValidationError

        # Validate discount logic
        if self.discount_percentage > 0 and self.discount_amount > 0:
            raise ValidationError(_("لا يمكن تطبيق نسبة خصم ومبلغ خصم معاً"))

        # Validate discount amount doesn't exceed base price
        if self.discount_amount >= self.base_price:
            raise ValidationError(_("مبلغ الخصم لا يمكن أن يكون أكبر من أو يساوي السعر الأساسي"))

        # Validate discount period
        if self.discount_start and self.discount_end:
            if self.discount_start >= self.discount_end:
                raise ValidationError(_("تاريخ بداية الخصم يجب أن يكون قبل تاريخ النهاية"))

    def save(self, *args, **kwargs):
        # Full clean before save
        self.full_clean()

        # Generate slug if not exists
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
            # Ensure slug uniqueness
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
            if self.stock_quantity <= 0:
                self.stock_status = 'out_of_stock'
            elif self.stock_quantity > 0:
                self.stock_status = 'in_stock'

        super().save(*args, **kwargs)

    def generate_sku(self):
        """Generate unique SKU"""
        import random
        import string

        # Get category prefix safely
        prefix = "PRD"  # Default prefix
        if hasattr(self.category, 'name') and self.category.name:
            prefix = self.category.name[:3].upper()

        # Generate unique suffix
        while True:
            suffix = ''.join(random.choices(string.digits, k=6))
            sku = f"{prefix}-{suffix}"
            if not Product.objects.filter(sku=sku).exists():
                return sku

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    @property
    def current_price(self):
        """Calculate current price with discount"""
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
    def in_stock(self):
        """Check if product is in stock"""
        if not self.track_inventory:
            return self.stock_status == 'in_stock'
        return self.stock_quantity > 0

    @property
    def low_stock(self):
        """Check if stock is low"""
        if self.track_inventory:
            return 0 < self.stock_quantity <= self.min_stock_level
        return False

    @property
    def default_image(self):
        """Get default product image"""
        first_image = self.images.filter(is_primary=True).first()
        if not first_image:
            first_image = self.images.first()
        return first_image

    @property
    def rating(self):
        """Get average rating"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0

    @property
    def review_count(self):
        """Get review count"""
        return self.reviews.filter(is_approved=True).count()

    def increment_views(self):
        """Increment view count"""
        self.views_count = models.F('views_count') + 1
        self.save(update_fields=['views_count'])
        self.refresh_from_db(fields=['views_count'])

    def can_review(self, user):
        """Check if user can review this product"""
        if not user.is_authenticated:
            return False
        # Check if user purchased this product
        try:
            from orders.models import OrderItem
            return OrderItem.objects.filter(
                order__user=user,
                order__status='delivered',
                product=self
            ).exists()
        except ImportError:
            return False


class ProductImage(models.Model):
    """
    نموذج صور المنتجات
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("المنتج")
    )
    image = models.ImageField(_("الصورة"), upload_to='products/%Y/%m/')
    alt_text = models.CharField(_("النص البديل"), max_length=200, blank=True)
    caption = models.CharField(_("التسمية التوضيحية"), max_length=200, blank=True)
    is_primary = models.BooleanField(_("صورة رئيسية"), default=False)
    order = models.IntegerField(_("الترتيب"), default=0)
    created_at = models.DateTimeField(_("تاريخ الإضافة"), auto_now_add=True)

    class Meta:
        verbose_name = _("صورة منتج")
        verbose_name_plural = _("صور المنتجات")
        ordering = ['order', '-is_primary']

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

        # Resize image if needed
        self.resize_image()

    def resize_image(self):
        """Resize image to optimize loading"""
        if self.image:
            img = Image.open(self.image.path)
            if img.width > 1200 or img.height > 1200:
                img.thumbnail((1200, 1200))
                img.save(self.image.path)


class ProductVariant(models.Model):
    """
    نموذج متغيرات المنتج (الألوان، الأحجام، إلخ)
    Product variants model for colors, sizes, etc.
    """

    SIZE_CHOICES = [
        ('xs', _('XS - صغير جداً')),
        ('s', _('S - صغير')),
        ('m', _('M - متوسط')),
        ('l', _('L - كبير')),
        ('xl', _('XL - كبير جداً')),
        ('xxl', _('XXL - كبير جداً جداً')),
        ('xxxl', _('XXXL - كبير جداً جداً جداً')),
    ]

    COLOR_CHOICES = [
        ('red', _('أحمر')),
        ('blue', _('أزرق')),
        ('green', _('أخضر')),
        ('yellow', _('أصفر')),
        ('black', _('أسود')),
        ('white', _('أبيض')),
        ('gray', _('رمادي')),
        ('brown', _('بني')),
        ('pink', _('وردي')),
        ('purple', _('بنفسجي')),
        ('orange', _('برتقالي')),
        ('navy', _('كحلي')),
    ]

    # Basic Information
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_("المنتج")
    )
    name = models.CharField(
        _("اسم المتغير"),
        max_length=200,
        validators=[MinLengthValidator(2)],
        help_text=_("اسم واضح للمتغير")
    )
    sku = models.CharField(
        _("رقم المتغير"),
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(3)],
        help_text=_("رقم فريد للمتغير")
    )

    # Variant Attributes
    color = models.CharField(
        _("اللون"),
        max_length=50,
        choices=COLOR_CHOICES,
        blank=True,
        help_text=_("لون المتغير")
    )
    color_code = models.CharField(
        _("كود اللون"),
        max_length=7,
        blank=True,
        help_text=_("كود اللون السداسي عشري (مثل: #FF5733)")
    )
    size = models.CharField(
        _("الحجم"),
        max_length=20,
        choices=SIZE_CHOICES,
        blank=True,
        help_text=_("حجم المتغير")
    )
    material = models.CharField(
        _("المادة"),
        max_length=100,
        blank=True,
        validators=[MinLengthValidator(2)],
        help_text=_("مادة صنع المتغير")
    )
    pattern = models.CharField(
        _("النقشة/التصميم"),
        max_length=100,
        blank=True,
        help_text=_("نقشة أو تصميم المتغير")
    )

    # Custom Attributes (JSON field for flexibility)
    custom_attributes = models.JSONField(
        _("خصائص مخصصة"),
        default=dict,
        blank=True,
        help_text=_("خصائص إضافية مخصصة للمتغير")
    )

    # Pricing
    price_adjustment = models.DecimalField(
        _("تعديل السعر"),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('-999999.99'))],
        help_text=_("تعديل السعر بالإضافة أو الطرح من السعر الأساسي")
    )
    cost_adjustment = models.DecimalField(
        _("تعديل التكلفة"),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('-999999.99'))],
        help_text=_("تعديل التكلفة بالإضافة أو الطرح من التكلفة الأساسية")
    )

    # Inventory
    stock_quantity = models.PositiveIntegerField(
        _("الكمية المتوفرة"),
        default=0,
        help_text=_("الكمية المتوفرة من هذا المتغير")
    )
    reserved_quantity = models.PositiveIntegerField(
        _("الكمية المحجوزة"),
        default=0,
        help_text=_("الكمية المحجوزة في طلبات معلقة")
    )
    min_stock_level = models.PositiveIntegerField(
        _("الحد الأدنى للمخزون"),
        default=5,
        validators=[MinValueValidator(1)],
        help_text=_("الحد الأدنى للتنبيه عند نفاد المخزون")
    )

    # Physical Attributes
    weight = models.DecimalField(
        _("الوزن (كجم)"),
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text=_("وزن هذا المتغير بالكيلوجرام")
    )
    length = models.DecimalField(
        _("الطول (سم)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("طول هذا المتغير بالسنتيمتر")
    )
    width = models.DecimalField(
        _("العرض (سم)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("عرض هذا المتغير بالسنتيمتر")
    )
    height = models.DecimalField(
        _("الارتفاع (سم)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("ارتفاع هذا المتغير بالسنتيمتر")
    )

    # Status and Availability
    is_active = models.BooleanField(_("نشط"), default=True)
    is_default = models.BooleanField(
        _("المتغير الافتراضي"),
        default=False,
        help_text=_("هل هذا هو المتغير الافتراضي للمنتج؟")
    )

    # Display Order
    sort_order = models.PositiveIntegerField(
        _("ترتيب العرض"),
        default=0,
        help_text=_("ترتيب المتغير في العرض")
    )

    # Tracking and Statistics
    sales_count = models.PositiveIntegerField(
        _("عدد المبيعات"),
        default=0,
        editable=False
    )
    views_count = models.PositiveIntegerField(
        _("عدد المشاهدات"),
        default=0,
        editable=False
    )

    # Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("متغير المنتج")
        verbose_name_plural = _("متغيرات المنتجات")
        ordering = ['sort_order', 'name']
        unique_together = [
            ['product', 'color', 'size'],  # منع التكرار لنفس المنتج بنفس اللون والحجم
            ['sku'],  # SKU فريد
        ]
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['sku']),
            models.Index(fields=['color', 'size']),
            models.Index(fields=['is_default']),
            models.Index(fields=['stock_quantity']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(stock_quantity__gte=0),
                name='non_negative_variant_stock'
            ),
            models.CheckConstraint(
                check=models.Q(reserved_quantity__gte=0),
                name='non_negative_reserved_quantity'
            ),
            models.CheckConstraint(
                check=models.Q(reserved_quantity__lte=models.F('stock_quantity')),
                name='reserved_not_exceed_stock'
            ),
        ]

    def __str__(self):
        parts = [self.product.name]
        if self.color:
            parts.append(self.get_color_display())
        if self.size:
            parts.append(self.get_size_display())
        if self.material:
            parts.append(self.material)
        return " - ".join(parts)

    def clean(self):
        """Custom validation"""
        from django.core.exceptions import ValidationError

        # Validate color code format
        if self.color_code and not self.color_code.startswith('#'):
            raise ValidationError({
                'color_code': _("كود اللون يجب أن يبدأ بـ #")
            })

        # Validate reserved quantity
        if self.reserved_quantity > self.stock_quantity:
            raise ValidationError({
                'reserved_quantity': _("الكمية المحجوزة لا يمكن أن تكون أكبر من الكمية المتوفرة")
            })

        # Ensure only one default variant per product
        if self.is_default:
            existing_default = ProductVariant.objects.filter(
                product=self.product,
                is_default=True
            ).exclude(pk=self.pk)

            if existing_default.exists():
                raise ValidationError({
                    'is_default': _("يوجد متغير افتراضي آخر لهذا المنتج")
                })

    def save(self, *args, **kwargs):
        self.full_clean()

        # Generate SKU if not provided
        if not self.sku:
            self.sku = self.generate_sku()

        # If this is the first variant, make it default
        if not self.pk and not ProductVariant.objects.filter(product=self.product).exists():
            self.is_default = True

        super().save(*args, **kwargs)

    def generate_sku(self):
        """Generate unique SKU for variant"""
        import random
        import string

        # Base SKU from product
        base_sku = self.product.sku if self.product.sku else "VAR"

        # Add variant identifiers
        variant_parts = []
        if self.color:
            variant_parts.append(self.color[:3].upper())
        if self.size:
            variant_parts.append(self.size.upper())

        # Generate unique suffix
        while True:
            suffix = ''.join(random.choices(string.digits, k=4))
            variant_suffix = "-".join(variant_parts) if variant_parts else ""
            sku = f"{base_sku}-{variant_suffix}-{suffix}" if variant_suffix else f"{base_sku}-{suffix}"

            if not ProductVariant.objects.filter(sku=sku).exists():
                return sku

    @property
    def current_price(self):
        """Calculate current price including adjustment"""
        base_price = self.product.current_price
        return base_price + self.price_adjustment

    @property
    def current_cost(self):
        """Calculate current cost including adjustment"""
        base_cost = self.product.cost or Decimal('0.00')
        return base_cost + self.cost_adjustment

    @property
    def available_quantity(self):
        """Get available quantity (stock - reserved)"""
        return self.stock_quantity - self.reserved_quantity

    @property
    def is_in_stock(self):
        """Check if variant is in stock"""
        return self.available_quantity > 0

    @property
    def is_low_stock(self):
        """Check if variant stock is low"""
        return 0 < self.available_quantity <= self.min_stock_level

    @property
    def stock_status(self):
        """Get stock status"""
        if self.available_quantity <= 0:
            return 'out_of_stock'
        elif self.is_low_stock:
            return 'low_stock'
        else:
            return 'in_stock'

    @property
    def full_name(self):
        """Get full descriptive name"""
        return str(self)

    @property
    def display_attributes(self):
        """Get display attributes as dictionary"""
        attrs = {}
        if self.color:
            attrs[_('اللون')] = self.get_color_display()
        if self.size:
            attrs[_('الحجم')] = self.get_size_display()
        if self.material:
            attrs[_('المادة')] = self.material
        if self.pattern:
            attrs[_('النقشة')] = self.pattern

        # Add custom attributes
        for key, value in self.custom_attributes.items():
            attrs[key] = value

        return attrs

    def reserve_quantity(self, quantity):
        """Reserve quantity for an order"""
        if quantity > self.available_quantity:
            raise ValueError(_("الكمية المطلوبة غير متوفرة"))

        self.reserved_quantity += quantity
        self.save(update_fields=['reserved_quantity'])

    def release_quantity(self, quantity):
        """Release reserved quantity"""
        if quantity > self.reserved_quantity:
            raise ValueError(_("الكمية المراد تحريرها أكبر من المحجوزة"))

        self.reserved_quantity -= quantity
        self.save(update_fields=['reserved_quantity'])

    def reduce_stock(self, quantity):
        """Reduce stock after sale"""
        if quantity > self.stock_quantity:
            raise ValueError(_("الكمية المطلوبة أكبر من المتوفرة"))

        self.stock_quantity -= quantity
        self.reserved_quantity = max(0, self.reserved_quantity - quantity)
        self.sales_count += quantity
        self.save(update_fields=['stock_quantity', 'reserved_quantity', 'sales_count'])

    def increment_views(self):
        """Increment view count"""
        ProductVariant.objects.filter(pk=self.pk).update(
            views_count=models.F('views_count') + 1
        )
        self.refresh_from_db(fields=['views_count'])

    def get_images(self):
        """Get variant-specific images"""
        # First try to get variant-specific images
        variant_images = self.images.filter(is_active=True)
        if variant_images.exists():
            return variant_images

        # Fallback to product images
        return self.product.images.filter(is_active=True)

    @classmethod
    def get_variants_for_product(cls, product, **filters):
        """Get variants for a specific product with filters"""
        queryset = cls.objects.filter(product=product, is_active=True)

        if filters:
            queryset = queryset.filter(**filters)

        return queryset.order_by('sort_order', 'name')

    def __repr__(self):
        return f"<ProductVariant: {self.full_name}>"


class Tag(models.Model):
    """
    نموذج الوسوم
    """
    name = models.CharField(_("اسم الوسم"), max_length=50, unique=True)
    slug = models.SlugField(_("معرف URL"), max_length=50, unique=True, allow_unicode=True)
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)

    class Meta:
        verbose_name = _("وسم")
        verbose_name_plural = _("الوسوم")
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class ProductReview(models.Model):
    """
    نموذج تقييمات المنتجات
    """
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
    rating = models.IntegerField(
        _("التقييم"),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(_("عنوان التقييم"), max_length=200)
    comment = models.TextField(_("التعليق"))

    # Images
    image1 = models.ImageField(_("صورة 1"), upload_to='reviews/', blank=True, null=True)
    image2 = models.ImageField(_("صورة 2"), upload_to='reviews/', blank=True, null=True)
    image3 = models.ImageField(_("صورة 3"), upload_to='reviews/', blank=True, null=True)

    # Moderation
    is_approved = models.BooleanField(_("معتمد"), default=False)
    is_featured = models.BooleanField(_("مميز"), default=False)

    # Helpful votes
    helpful_count = models.PositiveIntegerField(_("مفيد"), default=0)
    not_helpful_count = models.PositiveIntegerField(_("غير مفيد"), default=0)

    # Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("تقييم منتج")
        verbose_name_plural = _("تقييمات المنتجات")
        ordering = ['-created_at']
        unique_together = [['product', 'user']]

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating} stars"

    @property
    def helpful_percentage(self):
        """Calculate helpful percentage"""
        total = self.helpful_count + self.not_helpful_count
        if total > 0:
            return int((self.helpful_count / total) * 100)
        return 0


class Wishlist(models.Model):
    """
    نموذج قائمة الأمنيات
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
    created_at = models.DateTimeField(_("تاريخ الإضافة"), auto_now_add=True)

    class Meta:
        verbose_name = _("قائمة أمنيات")
        verbose_name_plural = _("قوائم الأمنيات")
        unique_together = [['user', 'product']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class ProductComparison(models.Model):
    """
    نموذج مقارنة المنتجات
    """
    session_key = models.CharField(_("معرف الجلسة"), max_length=100)
    products = models.ManyToManyField(Product, related_name='comparisons')
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("مقارنة منتجات")
        verbose_name_plural = _("مقارنات المنتجات")

    def __str__(self):
        return f"Comparison {self.session_key}"


class ProductDiscount(models.Model):
    """
    نموذج خصومات المنتجات
    Product discount model for managing product discounts
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', _('نسبة مئوية')),
        ('fixed_amount', _('مبلغ ثابت')),
        ('buy_x_get_y', _('اشتري X واحصل على Y')),
        ('quantity_based', _('خصم حسب الكمية')),
    ]

    APPLICATION_TYPE_CHOICES = [
        ('all_products', _('جميع المنتجات')),
        ('category', _('فئة محددة')),
        ('specific_products', _('منتجات محددة')),
    ]

    # Basic Information
    name = models.CharField(
        _("اسم الخصم"),
        max_length=200,
        validators=[MinLengthValidator(3)],
        help_text=_("اسم واضح للخصم")
    )
    description = models.TextField(
        _("وصف الخصم"),
        blank=True,
        validators=[MinLengthValidator(10)],
        help_text=_("وصف تفصيلي للخصم")
    )
    code = models.CharField(
        _("كود الخصم"),
        max_length=50,
        unique=True,
        blank=True,
        help_text=_("كود فريد للخصم (اختياري)")
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
        help_text=_("قيمة الخصم (نسبة أو مبلغ)")
    )
    max_discount_amount = models.DecimalField(
        _("الحد الأقصى لمبلغ الخصم"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("الحد الأقصى لمبلغ الخصم (للنسبة المئوية)")
    )

    # Application Rules
    application_type = models.CharField(
        _("نوع التطبيق"),
        max_length=20,
        choices=APPLICATION_TYPE_CHOICES,
        default='all_products'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discounts',
        verbose_name=_("الفئة")
    )
    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name='specific_discounts',
        verbose_name=_("المنتجات المحددة")
    )

    # Validity Period
    start_date = models.DateTimeField(
        _("تاريخ البداية"),
        help_text=_("تاريخ ووقت بداية الخصم")
    )
    end_date = models.DateTimeField(
        _("تاريخ النهاية"),
        null=True,
        blank=True,
        help_text=_("تاريخ ووقت نهاية الخصم (اختياري)")
    )

    # Usage Limitations
    min_purchase_amount = models.DecimalField(
        _("الحد الأدنى للشراء"),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("الحد الأدنى لمبلغ الشراء لتطبيق الخصم")
    )
    min_quantity = models.PositiveIntegerField(
        _("الحد الأدنى للكمية"),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("الحد الأدنى للكمية لتطبيق الخصم")
    )
    max_uses = models.PositiveIntegerField(
        _("الحد الأقصى للاستخدام"),
        null=True,
        blank=True,
        help_text=_("الحد الأقصى لعدد مرات الاستخدام")
    )
    max_uses_per_user = models.PositiveIntegerField(
        _("الحد الأقصى للاستخدام لكل مستخدم"),
        null=True,
        blank=True,
        help_text=_("الحد الأقصى للاستخدام لكل مستخدم")
    )
    used_count = models.PositiveIntegerField(
        _("عدد مرات الاستخدام"),
        default=0
    )

    # Buy X Get Y Configuration (for buy_x_get_y type)
    buy_quantity = models.PositiveIntegerField(
        _("اشتري كمية"),
        null=True,
        blank=True,
        help_text=_("الكمية المطلوب شراؤها")
    )
    get_quantity = models.PositiveIntegerField(
        _("احصل على كمية"),
        null=True,
        blank=True,
        help_text=_("الكمية المجانية")
    )
    get_discount_percentage = models.DecimalField(
        _("نسبة خصم الكمية المجانية"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("نسبة الخصم على الكمية المجانية")
    )

    # Status and Flags
    is_active = models.BooleanField(_("نشط"), default=True)
    is_stackable = models.BooleanField(
        _("قابل للتراكم"),
        default=False,
        help_text=_("هل يمكن تطبيق هذا الخصم مع خصومات أخرى؟")
    )
    requires_coupon_code = models.BooleanField(
        _("يتطلب كود خصم"),
        default=False,
        help_text=_("هل يتطلب إدخال كود للحصول على الخصم؟")
    )

    # Priority (for stacking discounts)
    priority = models.PositiveIntegerField(
        _("الأولوية"),
        default=0,
        help_text=_("أولوية تطبيق الخصم (رقم أعلى = أولوية أكبر)")
    )

    # Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_discounts',
        verbose_name=_("أنشئ بواسطة")
    )

    class Meta:
        verbose_name = _("خصم المنتج")
        verbose_name_plural = _("خصومات المنتجات")
        ordering = ['-priority', '-start_date']
        indexes = [
            models.Index(fields=['is_active', 'start_date', 'end_date']),
            models.Index(fields=['code']),
            models.Index(fields=['category']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_discount_type_display()})"

    def clean(self):
        """Custom validation"""
        from django.core.exceptions import ValidationError

        # Validate dates
        if self.end_date and self.start_date >= self.end_date:
            raise ValidationError({
                'end_date': _("تاريخ النهاية يجب أن يكون بعد تاريخ البداية")
            })

        # Validate discount type specific fields
        if self.discount_type == 'buy_x_get_y':
            if not self.buy_quantity or not self.get_quantity:
                raise ValidationError({
                    'buy_quantity': _("يجب تحديد كمية الشراء والكمية المجانية لنوع الخصم هذا"),
                    'get_quantity': _("يجب تحديد كمية الشراء والكمية المجانية لنوع الخصم هذا")
                })

        # Validate application type
        if self.application_type == 'category' and not self.category:
            raise ValidationError({
                'category': _("يجب اختيار فئة عند اختيار 'فئة محددة'")
            })

        # Validate coupon code
        if self.requires_coupon_code and not self.code:
            raise ValidationError({
                'code': _("يجب إدخال كود الخصم عند تفعيل 'يتطلب كود خصم'")
            })

    def save(self, *args, **kwargs):
        self.full_clean()

        # Generate code if not provided and required
        if self.requires_coupon_code and not self.code:
            self.code = self.generate_code()

        super().save(*args, **kwargs)

    def generate_code(self):
        """Generate unique discount code"""
        import random
        import string

        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not ProductDiscount.objects.filter(code=code).exists():
                return code

    @property
    def is_valid_now(self):
        """Check if discount is currently valid"""
        now = timezone.now()

        # Check if active
        if not self.is_active:
            return False

        # Check start date
        if self.start_date > now:
            return False

        # Check end date
        if self.end_date and self.end_date < now:
            return False

        # Check usage limits
        if self.max_uses and self.used_count >= self.max_uses:
            return False

        return True

    @property
    def is_expired(self):
        """Check if discount is expired"""
        if not self.end_date:
            return False
        return timezone.now() > self.end_date

    @property
    def days_until_expiry(self):
        """Get days until expiry"""
        if not self.end_date:
            return None

        now = timezone.now()
        if self.end_date < now:
            return 0

        return (self.end_date - now).days

    def can_apply_to_product(self, product):
        """Check if discount can be applied to a specific product"""
        if not self.is_valid_now:
            return False

        if self.application_type == 'all_products':
            return True
        elif self.application_type == 'category':
            return product.category == self.category
        elif self.application_type == 'specific_products':
            return self.products.filter(id=product.id).exists()

        return False

    def calculate_discount_amount(self, price, quantity=1):
        """Calculate discount amount for given price and quantity"""
        if not self.is_valid_now:
            return Decimal('0.00')

        # Check minimum quantity
        if quantity < self.min_quantity:
            return Decimal('0.00')

        discount_amount = Decimal('0.00')

        if self.discount_type == 'percentage':
            discount_amount = price * (self.value / 100)
            # Apply maximum discount limit
            if self.max_discount_amount and discount_amount > self.max_discount_amount:
                discount_amount = self.max_discount_amount

        elif self.discount_type == 'fixed_amount':
            discount_amount = self.value
            # Don't exceed the price
            if discount_amount > price:
                discount_amount = price

        elif self.discount_type == 'quantity_based':
            # Apply discount based on quantity tiers
            discount_amount = price * (self.value / 100)

        elif self.discount_type == 'buy_x_get_y':
            # Calculate how many free items customer gets
            if quantity >= self.buy_quantity:
                free_items = (quantity // self.buy_quantity) * self.get_quantity
                if self.get_discount_percentage:
                    discount_amount = (price * free_items) * (self.get_discount_percentage / 100)
                else:
                    discount_amount = price * free_items

        return discount_amount

    def increment_usage(self):
        """Increment usage count"""
        self.used_count = models.F('used_count') + 1
        self.save(update_fields=['used_count'])
        self.refresh_from_db(fields=['used_count'])

    def get_usage_percentage(self):
        """Get usage percentage"""
        if not self.max_uses:
            return 0
        return int((self.used_count / self.max_uses) * 100)