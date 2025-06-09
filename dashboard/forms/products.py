"""
نماذج إدارة المنتجات - يحتوي على النماذج المرتبطة بإدارة المنتجات والفئات والمتغيرات والصور والخصومات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from mptt.forms import TreeNodeChoiceField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, HTML, Row, Column
from crispy_forms.bootstrap import FormActions, TabHolder, Tab
from django.utils.text import slugify
import json
from django.contrib.auth import get_user_model

from products.models import (
    Product, Category, Brand, Tag, ProductVariant, ProductImage, ProductReview,
    ProductAttribute, ProductDiscount, ProductAttributeValue
)

User = get_user_model()


# dashboard/forms/products.py - تحديث نموذج ProductForm

class ProductForm(forms.ModelForm):
    """نموذج إنشاء وتحديث المنتج"""

    # الحقول الإضافية الموجودة سابقًا
    video_url = forms.URLField(
        label=_("رابط الفيديو"),
        required=False,
        widget=forms.URLInput(attrs={'dir': 'ltr'})
    )

    has_360_view = forms.BooleanField(
        label=_("تفعيل العرض ثلاثي الأبعاد (360 درجة)"),
        required=False
    )

    specifications_json = forms.CharField(
        label=_("المواصفات"),
        widget=forms.Textarea(attrs={'class': 'hidden-field'}),
        required=False
    )

    features_json = forms.CharField(
        label=_("الميزات"),
        widget=forms.Textarea(attrs={'class': 'hidden-field'}),
        required=False
    )

    related_products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True, status='published'),
        label=_("المنتجات ذات الصلة"),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2'})
    )

    # إضافة الحقول المفقودة

    # حقول الخصم
    discount_percentage = forms.DecimalField(
        label=_("نسبة الخصم"),
        required=False,
        min_value=0,
        max_value=100,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100', 'class': 'form-control'})
    )

    discount_amount = forms.DecimalField(
        label=_("مبلغ الخصم"),
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'})
    )

    discount_start = forms.DateTimeField(
        label=_("بداية الخصم"),
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )

    discount_end = forms.DateTimeField(
        label=_("نهاية الخصم"),
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )

    # حقول المخزون المتقدمة
    reserved_quantity = forms.IntegerField(
        label=_("الكمية المحجوزة"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
    )

    max_order_quantity = forms.IntegerField(
        label=_("الحد الأقصى للطلب"),
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )

    track_inventory = forms.BooleanField(
        label=_("تتبع المخزون"),
        required=False,
        initial=True
    )

    # حقول الطلب المسبق
    available_for_preorder = forms.BooleanField(
        label=_("متاح للطلب المسبق"),
        required=False
    )

    preorder_message = forms.CharField(
        label=_("رسالة الطلب المسبق"),
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # حقول الضمان
    warranty_period = forms.CharField(
        label=_("فترة الضمان"),
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    warranty_details = forms.CharField(
        label=_("تفاصيل الضمان"),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    # إعدادات العرض الإضافية
    show_price = forms.BooleanField(
        label=_("عرض السعر"),
        required=False,
        initial=True
    )

    # منتجات متعلقة إضافية
    cross_sell_products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True, status='published'),
        label=_("منتجات البيع المتقاطع"),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2'})
    )

    upsell_products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True, status='published'),
        label=_("منتجات البيع التصاعدي"),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2'})
    )

    # حقول زمنية
    featured_until = forms.DateTimeField(
        label=_("مميز حتى"),
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )

    # حقل مخفي للمستخدم الذي أنشأ المنتج
    created_by = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Product
        fields = [
            'name', 'name_en', 'sku', 'barcode', 'category', 'brand', 'tags',
            'short_description', 'description', 'base_price', 'compare_price',
            'cost', 'tax_rate', 'tax_class', 'stock_quantity', 'stock_status',
            'min_stock_level', 'condition', 'weight', 'length', 'width', 'height',
            'status', 'is_active', 'is_featured', 'is_new', 'is_best_seller',
            'is_digital', 'requires_shipping', 'allow_reviews', 'show_price',
            'meta_title', 'meta_description', 'meta_keywords', 'search_keywords',
            # إضافة الحقول الجديدة لتضمينها في النموذج
            'discount_percentage', 'discount_amount', 'discount_start', 'discount_end',
            'reserved_quantity', 'max_order_quantity', 'track_inventory',
            'available_for_preorder', 'preorder_message',
            'warranty_period', 'warranty_details', 'featured_until'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'required': False}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.Select(attrs={'class': 'form-select select2'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select select2'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control rich-text-editor', 'rows': 10}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'compare_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'tax_class': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'stock_status': forms.Select(attrs={'class': 'form-select'}),
            'min_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0'}),
            'length': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control tagsinput'}),
            'search_keywords': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'show_price': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        error_messages = {
            'name': {
                'required': _("اسم المنتج مطلوب"),
                'min_length': _("اسم المنتج يجب أن يكون على الأقل حرفين"),
            },
            'category': {
                'required': _("يجب اختيار فئة للمنتج"),
            },
            'base_price': {
                'required': _("السعر الأساسي مطلوب"),
                'min_value': _("السعر الأساسي يجب أن يكون أكبر من صفر"),
            },
            'description': {
                'required': _("وصف المنتج مطلوب"),
                'min_length': _("وصف المنتج يجب أن يكون على الأقل 20 حرفًا"),
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sku'].required = True

        # تعبئة القيم الأولية للحقول الجديدة إذا كان المنتج موجودًا
        if self.instance.pk:
            # تعبئة المنتجات المرتبطة
            self.fields['cross_sell_products'].initial = self.instance.cross_sell_products.all()
            self.fields['upsell_products'].initial = self.instance.upsell_products.all()

        # باقي الكود كما هو...

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من منطق الخصم - لا يمكن استخدام نسبة الخصم ومبلغ الخصم معًا
        discount_percentage = cleaned_data.get('discount_percentage')
        discount_amount = cleaned_data.get('discount_amount')

        if discount_percentage and discount_amount and discount_percentage > 0 and discount_amount > 0:
            self.add_error('discount_percentage', _("لا يمكن استخدام نسبة الخصم ومبلغ الخصم معًا"))
            self.add_error('discount_amount', _("لا يمكن استخدام نسبة الخصم ومبلغ الخصم معًا"))

        # التحقق من تواريخ الخصم
        discount_start = cleaned_data.get('discount_start')
        discount_end = cleaned_data.get('discount_end')

        if discount_start and discount_end and discount_start >= discount_end:
            self.add_error('discount_end', _("تاريخ نهاية الخصم يجب أن يكون بعد تاريخ البداية"))

        # باقي التحققات كما هي...

        return cleaned_data

    def save(self, commit=True, user=None):
        import json
        instance = super().save(commit=False)

        # تعيين المستخدم الذي أنشأ المنتج إذا كان منتج جديد
        if not instance.pk and user:
            instance.created_by = user

        # إنشاء سلج للمنتجات الجديدة
        if not instance.pk and not instance.slug:
            slug = slugify(instance.name, allow_unicode=True)
            # التحقق من تفرد السلج
            from uuid import uuid4
            if Product.objects.filter(slug=slug).exists():
                slug = f"{slug}-{uuid4().hex[:6]}"
            instance.slug = slug

        # إنشاء SKU للمنتجات الجديدة
        if not instance.pk and not instance.sku:
            instance.sku = Product().generate_sku()

        # تعيين تاريخ النشر
        if instance.status == 'published' and not instance.published_at:
            instance.published_at = timezone.now()

        # تحميل المواصفات والميزات
        if 'specifications_json' in self.cleaned_data and self.cleaned_data['specifications_json'].strip():
            instance.specifications = json.loads(self.cleaned_data['specifications_json'])

        if 'features_json' in self.cleaned_data and self.cleaned_data['features_json'].strip():
            instance.features = json.loads(self.cleaned_data['features_json'])

        if commit:
            instance.save()

            # حفظ العلاقات
            self.save_m2m()

            # حفظ المنتجات ذات الصلة
            if 'related_products' in self.cleaned_data:
                instance.related_products.set(self.cleaned_data['related_products'])

            # حفظ قيم الصفات
            for attr in self.product_attributes:
                field_name = f'attribute_{attr.id}'
                if field_name in self.cleaned_data and self.cleaned_data[field_name]:
                    value = self.cleaned_data[field_name]
                    ProductAttributeValue.objects.update_or_create(
                        product=instance,
                        attribute=attr,
                        defaults={'value': value}
                    )

        return instance


class CategoryForm(forms.ModelForm):
    """نموذج إنشاء وتعديل فئات المنتجات"""

    class Meta:
        model = Category
        fields = [
            'name', 'name_en', 'slug', 'parent', 'description', 'description_en',
            'image', 'icon', 'color', 'banner_image', 'is_active', 'is_featured',
            'show_in_menu', 'sort_order', 'meta_title', 'meta_description', 'meta_keywords'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'parent': TreeNodeChoiceField(queryset=Category.objects.all(), level_indicator=u'⟹', required=False),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'dir': 'ltr'}),
            'icon': forms.TextInput(attrs={'class': 'form-control icon-picker', 'dir': 'ltr'}),
            'color': forms.TextInput(attrs={'class': 'form-control color-picker', 'dir': 'ltr'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control'}),
        }

    content_blocks = forms.CharField(
        label=_('كتل المحتوى'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل كتل المحتوى بتنسيق JSON (اختياري)')
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تجنب اختيار الفئة نفسها كأب عند التعديل
        if self.instance.pk:
            self.fields['parent'].queryset = Category.objects.exclude(
                pk=self.instance.pk
            ).exclude(
                pk__in=[child.pk for child in self.instance.get_all_children()]
            )

            # تعبئة حقل كتل المحتوى
            if self.instance.content_blocks:
                self.fields['content_blocks'].initial = json.dumps(
                    self.instance.content_blocks,
                    indent=4,
                    ensure_ascii=False
                )

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('المعلومات الأساسية'),
                    Row(
                        Column('name', css_class='col-md-6'),
                        Column('name_en', css_class='col-md-6'),
                    ),
                    Row(
                        Column('slug', css_class='col-md-6'),
                        Column('parent', css_class='col-md-6'),
                    ),
                    'description',
                    'description_en'),

                Tab(_('العرض والمظهر'),
                    Row(
                        Column(
                            HTML('<div class="img-preview mb-3" id="image-preview"></div>'),
                            'image',
                            css_class='col-md-6'
                        ),
                        Column(
                            HTML('<div class="img-preview mb-3" id="banner-preview"></div>'),
                            'banner_image',
                            css_class='col-md-6'
                        ),
                    ),
                    Row(
                        Column('icon', css_class='col-md-6'),
                        Column('color', css_class='col-md-6'),
                    ),
                    Row(
                        Column('sort_order', css_class='col-md-4'),
                        Column('is_active', css_class='col-md-4'),
                        Column('is_featured', css_class='col-md-4'),
                    ),
                    'show_in_menu',
                    'content_blocks'),

                Tab(_('SEO'),
                    'meta_title',
                    'meta_description',
                    'meta_keywords'),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:category_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean_content_blocks(self):
        content = self.cleaned_data.get('content_blocks')
        if not content:
            return {}

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValidationError(_('تنسيق JSON غير صالح لكتل المحتوى'))

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من أن الفئة لا تكون أب لنفسها
        parent = cleaned_data.get('parent')
        if self.instance.pk and parent and parent.pk == self.instance.pk:
            self.add_error('parent', _('لا يمكن أن تكون الفئة أب لنفسها'))

        return cleaned_data

    def save(self, commit=True):
        category = super().save(commit=False)

        # تعيين المستخدم الذي أنشأ الفئة
        if not category.pk and self.user:
            category.created_by = self.user

        if commit:
            category.save()

        return category


class ProductVariantForm(forms.ModelForm):
    """نموذج إنشاء وتعديل متغيرات المنتجات"""

    class Meta:
        model = ProductVariant
        fields = [
            'name', 'sku', 'base_price', 'stock_quantity',
            'weight', 'is_active', 'is_default', 'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'required': False}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    attributes = forms.CharField(
        label=_('خصائص المتغير'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل خصائص المتغير بتنسيق JSON (مثل: {"اللون": "أحمر", "الحجم": "كبير"})')
    )

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        # تعبئة حقل الخصائص
        if self.instance.pk and self.instance.attributes:
            self.fields['attributes'].initial = json.dumps(
                self.instance.attributes,
                indent=4,
                ensure_ascii=False
            )

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('معلومات المتغير'),
                'name',
                'sku',
                'attributes',
            ),
            Fieldset(
                _('التسعير والمخزون'),
                Row(
                    Column('base_price', css_class='col-md-6'),
                    Column('stock_quantity', css_class='col-md-6'),
                ),
                'weight',
            ),
            Fieldset(
                _('الإعدادات'),
                Row(
                    Column('is_active', css_class='col-md-4'),
                    Column('is_default', css_class='col-md-4'),
                    Column('sort_order', css_class='col-md-4'),
                ),
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML(
                    '<a href="{% url "dashboard:product_detail" pk=product.pk %}" class="btn btn-secondary">%s</a>' % _(
                        'إلغاء'))
            )
        )

    def clean_attributes(self):
        attrs = self.cleaned_data.get('attributes')
        if not attrs:
            return {}

        try:
            return json.loads(attrs)
        except json.JSONDecodeError:
            raise ValidationError(_('تنسيق JSON غير صالح للخصائص'))

    def save(self, commit=True):
        variant = super().save(commit=False)

        # تعيين المنتج إذا كان جديدًا
        if not variant.pk and self.product:
            variant.product = self.product

        if commit:
            variant.save()

        return variant


class ProductImageForm(forms.ModelForm):
    """نموذج إضافة وتعديل صور المنتجات"""

    class Meta:
        model = ProductImage
        fields = [
            'image', 'alt_text', 'caption', 'is_primary',
            'is_360', 'sort_order', 'color_code', 'variant'
        ]
        widgets = {
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'color_code': forms.TextInput(attrs={'class': 'form-control color-picker', 'dir': 'ltr'}),
            'variant': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        # تقييد الاختيار للمتغيرات المرتبطة بالمنتج فقط
        if self.product:
            self.fields['variant'].queryset = ProductVariant.objects.filter(product=self.product)

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('الصورة'),
                'image',
                HTML('<div class="img-preview my-3" id="image-preview"></div>'),
                Row(
                    Column('alt_text', css_class='col-md-6'),
                    Column('caption', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('الإعدادات'),
                Row(
                    Column('is_primary', css_class='col-md-6'),
                    Column('is_360', css_class='col-md-6'),
                ),
                Row(
                    Column('sort_order', css_class='col-md-6'),
                    Column('color_code', css_class='col-md-6'),
                ),
                'variant',
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML(
                    '<a href="{% url "dashboard:product_detail" pk=product.pk %}" class="btn btn-secondary">%s</a>' % _(
                        'إلغاء'))
            )
        )

    def save(self, commit=True):
        image = super().save(commit=False)

        # تعيين المنتج إذا كان جديدًا
        if not image.pk and self.product:
            image.product = self.product

        if commit:
            image.save()

        return image


class ProductDiscountForm(forms.ModelForm):
    """نموذج إنشاء وتعديل خصومات المنتجات"""

    class Meta:
        model = ProductDiscount
        fields = [
            'name', 'description', 'code', 'discount_type', 'value',
            'max_discount_amount', 'application_type', 'category', 'products',
            'start_date', 'end_date', 'min_purchase_amount', 'min_quantity',
            'max_uses', 'max_uses_per_user', 'buy_quantity', 'get_quantity',
            'get_discount_percentage', 'is_active', 'is_stackable',
            'requires_coupon_code', 'priority'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'application_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'products': forms.SelectMultiple(attrs={'class': 'form-select select2', 'multiple': 'multiple'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'min_purchase_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_uses_per_user': forms.NumberInput(attrs={'class': 'form-control'}),
            'buy_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'get_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'get_discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تحسين حقول الاختيار
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['products'].queryset = Product.objects.filter(is_active=True, status='published')

        # إخفاء/إظهار الحقول بناءً على نوع الخصم
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'discount-form'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('المعلومات الأساسية'),
                    'name',
                    'description',
                    Row(
                        Column('code', css_class='col-md-6'),
                        Column('requires_coupon_code', css_class='col-md-6'),
                    ),
                    Row(
                        Column('discount_type', css_class='col-md-4'),
                        Column('value', css_class='col-md-4'),
                        Column('max_discount_amount', css_class='col-md-4'),
                    ),
                    Row(
                        Column('start_date', css_class='col-md-6'),
                        Column('end_date', css_class='col-md-6'),
                    ),
                    'is_active',
                    ),

                Tab(_('نطاق التطبيق'),
                    'application_type',
                    Div(
                        'category',
                        css_class='category-fields',
                    ),
                    Div(
                        'products',
                        css_class='products-fields',
                    ),
                    Row(
                        Column('min_purchase_amount', css_class='col-md-6'),
                        Column('min_quantity', css_class='col-md-6'),
                    ),
                    ),

                Tab(_('إعدادات اشتري X واحصل على Y'),
                    Div(
                        Row(
                            Column('buy_quantity', css_class='col-md-4'),
                            Column('get_quantity', css_class='col-md-4'),
                            Column('get_discount_percentage', css_class='col-md-4'),
                        ),
                        css_class='buy-x-get-y-fields',
                    ),
                    ),

                Tab(_('الحدود والإعدادات المتقدمة'),
                    Row(
                        Column('max_uses', css_class='col-md-6'),
                        Column('max_uses_per_user', css_class='col-md-6'),
                    ),
                    Row(
                        Column('priority', css_class='col-md-6'),
                        Column('is_stackable', css_class='col-md-6'),
                    ),
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:discount_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من صحة تواريخ الخصم
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date >= end_date:
            self.add_error('end_date', _('يجب أن يكون تاريخ النهاية بعد تاريخ البداية'))

        # التحقق من حقول اشتري X واحصل على Y
        discount_type = cleaned_data.get('discount_type')
        if discount_type == 'buy_x_get_y':
            buy_quantity = cleaned_data.get('buy_quantity')
            get_quantity = cleaned_data.get('get_quantity')

            if not buy_quantity or buy_quantity < 1:
                self.add_error('buy_quantity', _('يجب تحديد كمية الشراء'))

            if not get_quantity or get_quantity < 1:
                self.add_error('get_quantity', _('يجب تحديد كمية الحصول'))

        # التحقق من نوع التطبيق
        application_type = cleaned_data.get('application_type')
        if application_type == 'category' and not cleaned_data.get('category'):
            self.add_error('category', _('يجب تحديد الفئة عند اختيار نوع التطبيق "فئة محددة"'))

        if application_type == 'specific_products' and not cleaned_data.get('products'):
            self.add_error('products', _('يجب تحديد المنتجات عند اختيار نوع التطبيق "منتجات محددة"'))

        # التحقق من الكود
        requires_code = cleaned_data.get('requires_coupon_code')
        code = cleaned_data.get('code')

        if requires_code and not code:
            self.add_error('code', _('يجب تحديد كود الخصم عند تفعيل "يتطلب كود خصم"'))

        return cleaned_data

    def save(self, commit=True):
        discount = super().save(commit=False)

        # تعيين المستخدم الذي أنشأ الخصم
        if not discount.pk and self.user:
            discount.created_by = self.user

        if commit:
            discount.save()
            self.save_m2m()  # لحفظ العلاقات مثل المنتجات

        return discount