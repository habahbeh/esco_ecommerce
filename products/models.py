from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import uuid


class Category(models.Model):
    """
    نموذج التصنيف - يمثل تصنيفات المنتجات (المستوى الأول)
    Category model - represents product categories (level 1)
    """
    name = models.CharField(_("الاسم"), max_length=100)
    name_ar = models.CharField(_("الاسم بالعربية"), max_length=100)
    name_en = models.CharField(_("الاسم بالإنجليزية"), max_length=100)
    slug = models.SlugField(_("الرابط المختصر"), unique=True, allow_unicode=True)
    description = models.TextField(_("الوصف"), blank=True)
    image = models.ImageField(_("الصورة"), upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(_("نشط"), default=True)
    show_prices = models.BooleanField(_("إظهار الأسعار"), default=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='children', verbose_name=_("التصنيف الأب"))
    level = models.PositiveSmallIntegerField(_("المستوى"), default=1, editable=False)
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name='created_categories',
                                   verbose_name=_("أنشئ بواسطة"))
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name='updated_categories',
                                   verbose_name=_("حُدث بواسطة"))

    class Meta:
        verbose_name = _("تصنيف")
        verbose_name_plural = _("التصنيفات")
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # توليد الرابط المختصر تلقائيًا - Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.name_en, allow_unicode=True)

        # تحديد المستوى حسب الأب - Set level based on parent
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'slug': self.slug})

    @property
    def is_subcategory(self):
        """هل هذا تصنيف فرعي؟"""
        return self.parent is not None

    @property
    def is_subsubcategory(self):
        """هل هذا تصنيف فرعي ثالث؟"""
        return self.parent and self.parent.parent is not None


class ProductDiscount(models.Model):
    """
    نموذج خصم المنتج - يمثل الخصومات التي يمكن تطبيقها على المنتجات أو التصنيفات
    Product discount model - represents discounts that can be applied to products or categories
    """
    name = models.CharField(_("الاسم"), max_length=100)
    description = models.TextField(_("الوصف"), blank=True)
    discount_type = models.CharField(_("نوع الخصم"), max_length=10, choices=[
        ('percentage', _('نسبة مئوية')),
        ('fixed', _('قيمة ثابتة')),
    ], default='percentage')
    value = models.DecimalField(_("القيمة"), max_digits=10, decimal_places=2)
    start_date = models.DateTimeField(_("تاريخ البدء"), default=timezone.now)
    end_date = models.DateTimeField(_("تاريخ الانتهاء"), null=True, blank=True)
    is_active = models.BooleanField(_("نشط"), default=True)

    # يمكن تطبيق الخصم على فئة أو منتج محدد - Can be applied to a specific category or product
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name='discounts', verbose_name=_("التصنيف"))

    class Meta:
        verbose_name = _("خصم")
        verbose_name_plural = _("الخصومات")

    def __str__(self):
        return self.name

    @property
    def is_valid(self):
        """
        التحقق مما إذا كان الخصم ساري المفعول في الوقت الحالي
        Check if the discount is valid at the current time
        """
        now = timezone.now()
        return (
                self.is_active and
                self.start_date <= now and
                (self.end_date is None or self.end_date >= now)
        )

    def calculate_discounted_price(self, original_price):
        """
        حساب السعر بعد الخصم
        Calculate the discounted price
        """
        if not self.is_valid:
            return original_price

        if self.discount_type == 'percentage':
            discount_amount = original_price * (self.value / 100)
        else:  # fixed
            discount_amount = self.value

        return max(original_price - discount_amount, 0)  # لا يمكن أن يكون السعر سالبًا


class Product(models.Model):
    """
    نموذج المنتج - يمثل المنتجات المعروضة في الموقع
    Product model - represents products displayed on the site
    """
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('pending', _('قيد المراجعة')),
        ('published', _('منشور')),
        ('archived', _('مؤرشف')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("الاسم"), max_length=255)
    name_ar = models.CharField(_("الاسم بالعربية"), max_length=255)
    name_en = models.CharField(_("الاسم بالإنجليزية"), max_length=255)
    slug = models.SlugField(_("الرابط المختصر"), unique=True, allow_unicode=True)
    sku = models.CharField(_("رمز المنتج"), max_length=50, unique=True)
    description = models.TextField(_("الوصف"))
    description_ar = models.TextField(_("الوصف بالعربية"))
    description_en = models.TextField(_("الوصف بالإنجليزية"))
    short_description = models.TextField(_("وصف مختصر"), blank=True)

    # التصنيفات - Categories
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products',
                                 verbose_name=_("التصنيف"))

    # معلومات السعر - Price information
    base_price = models.DecimalField(_("السعر الأساسي"), max_digits=10, decimal_places=2)
    show_price = models.BooleanField(_("إظهار السعر"), default=True)
    discount = models.ForeignKey(ProductDiscount, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='products', verbose_name=_("الخصم"))

    # الصور - Images
    default_image = models.ImageField(_("الصورة الافتراضية"), upload_to='products/')

    # المخزون - Inventory
    stock_quantity = models.PositiveIntegerField(_("الكمية المتوفرة"), default=0)
    stock_status = models.CharField(_("حالة المخزون"), max_length=20, choices=[
        ('in_stock', _('متوفر')),
        ('out_of_stock', _('غير متوفر')),
        ('backorder', _('متوفر للطلب المسبق')),
    ], default='in_stock')

    # حالة المنتج ومعلومات النشر - Product status and publishing info
    status = models.CharField(_("الحالة"), max_length=20, choices=STATUS_CHOICES, default='pending')
    is_featured = models.BooleanField(_("مميز"), default=False)
    is_active = models.BooleanField(_("نشط"), default=True)

    # توقيتات ومعلومات المستخدم - Timestamps and user info
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
    published_at = models.DateTimeField(_("تاريخ النشر"), null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name='created_products',
                                   verbose_name=_("أنشئ بواسطة"))
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name='updated_products',
                                   verbose_name=_("حُدث بواسطة"))
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='approved_products',
                                    verbose_name=_("تمت الموافقة بواسطة"))

    # SEO معلومات - SEO information
    meta_title = models.CharField(_("عنوان ميتا"), max_length=100, blank=True)
    meta_description = models.TextField(_("وصف ميتا"), blank=True)
    meta_keywords = models.CharField(_("كلمات ميتا"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("منتج")
        verbose_name_plural = _("المنتجات")
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # توليد الرابط المختصر تلقائيًا - Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.name_en, allow_unicode=True)

        # تحديث تاريخ النشر عند تغيير الحالة إلى منشور - Update published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    @property
    def current_price(self):
        """
        حساب السعر الحالي بعد تطبيق الخصومات (إن وجدت)
        Calculate the current price after applying discounts (if any)
        """
        price = self.base_price

        # تطبيق خصم المنتج إذا كان موجودًا وساريًا - Apply product discount if exists and valid
        if self.discount and self.discount.is_valid:
            price = self.discount.calculate_discounted_price(price)

        # تطبيق خصم الفئة إذا كان موجودًا وساريًا - Apply category discount if exists and valid
        category_discount = None
        if self.category.discounts.exists():
            for discount in self.category.discounts.filter(is_active=True):
                if discount.is_valid:
                    category_discount = discount
                    break

        if category_discount:
            price = category_discount.calculate_discounted_price(price)

        return price

    @property
    def discount_percentage(self):
        """
        حساب نسبة الخصم (إذا كان هناك خصم)
        Calculate discount percentage (if there is a discount)
        """
        if self.current_price < self.base_price:
            return int(((self.base_price - self.current_price) / self.base_price) * 100)
        return 0

    @property
    def has_discount(self):
        """
        التحقق مما إذا كان المنتج يحتوي على خصم ساري المفعول
        Check if the product has an active discount
        """
        return self.current_price < self.base_price


class ProductVariant(models.Model):
    """
    نموذج متغير المنتج - يمثل متغيرات المنتج (مثل الألوان المختلفة)
    Product variant model - represents product variants (such as different colors)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants',
                                verbose_name=_("المنتج"))
    name = models.CharField(_("الاسم"), max_length=100)
    name_ar = models.CharField(_("الاسم بالعربية"), max_length=100)
    name_en = models.CharField(_("الاسم بالإنجليزية"), max_length=100)
    color_code = models.CharField(_("كود اللون"), max_length=20, blank=True)
    price_adjustment = models.DecimalField(_("تعديل السعر"), max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(_("الكمية المتوفرة"), default=0)
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("متغير المنتج")
        verbose_name_plural = _("متغيرات المنتج")

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def price(self):
        """
        حساب سعر هذا المتغير (السعر الأساسي للمنتج + تعديل السعر)
        Calculate the price of this variant (product base price + price adjustment)
        """
        base_price = self.product.base_price + self.price_adjustment

        # تطبيق الخصومات إذا كانت موجودة - Apply discounts if they exist
        if self.product.discount and self.product.discount.is_valid:
            return self.product.discount.calculate_discounted_price(base_price)

        # تطبيق خصم الفئة إذا كان موجودًا - Apply category discount if exists
        category_discount = None
        if self.product.category.discounts.exists():
            for discount in self.product.category.discounts.filter(is_active=True):
                if discount.is_valid:
                    category_discount = discount
                    break

        if category_discount:
            return category_discount.calculate_discounted_price(base_price)

        return base_price


class ProductImage(models.Model):
    """
    نموذج صورة المنتج - يمثل صور المنتج
    Product image model - represents product images
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images',
                                verbose_name=_("المنتج"))
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='images', verbose_name=_("المتغير"))
    image = models.ImageField(_("الصورة"), upload_to='products/')
    alt_text = models.CharField(_("النص البديل"), max_length=255, blank=True)
    is_primary = models.BooleanField(_("صورة رئيسية"), default=False)
    sort_order = models.PositiveSmallIntegerField(_("ترتيب الظهور"), default=0)

    class Meta:
        verbose_name = _("صورة المنتج")
        verbose_name_plural = _("صور المنتج")
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.name} - {self.id}"