# File: products/forms.py
"""
نماذج تطبيق المنتجات - مُصححة ومحسنة
تتوافق مع بنية النماذج الصحيحة في models.py
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import re

from .models import ProductReview, Product, Category, Brand, Tag


class ProductReviewForm(forms.ModelForm):
    """
    نموذج إضافة تقييم للمنتج - مُصحح
    """

    class Meta:
        model = ProductReview
        # استخدام الحقول الصحيحة من models.py
        fields = ['rating', 'title', 'content', 'image']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, f'{i} ⭐') for i in range(1, 6)],
                attrs={'class': 'rating-input d-flex gap-2'}
            ),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('عنوان مختصر لتقييمك'),
                'maxlength': '200'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('شاركنا تجربتك مع هذا المنتج...'),
                'rows': 5,
                'minlength': '20'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'rating': _('التقييم'),
            'title': _('عنوان التقييم'),
            'content': _('تعليقك'),
            'image': _('صورة (اختياري)'),
        }
        help_texts = {
            'rating': _('قيّم المنتج من 1 إلى 5 نجوم'),
            'title': _('عنوان مختصر يلخص رأيك'),
            'content': _('اكتب تفاصيل تجربتك مع المنتج (20 حرف على الأقل)'),
            'image': _('يمكنك رفع صورة للمنتج (حجم أقصى 5MB)')
        }

    def clean_content(self):
        """التحقق من محتوى التعليق"""
        content = self.cleaned_data.get('content')
        if content and len(content.strip()) < 20:
            raise ValidationError(_('التعليق يجب أن يكون 20 حرف على الأقل'))
        return content.strip() if content else content

    def clean_title(self):
        """التحقق من عنوان التقييم"""
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 5:
            raise ValidationError(_('العنوان يجب أن يكون 5 أحرف على الأقل'))
        return title.strip() if title else title

    def clean_image(self):
        """التحقق من الصورة المرفوعة"""
        image = self.cleaned_data.get('image')
        if image:
            # التحقق من حجم الصورة (5MB كحد أقصى)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError(_('حجم الصورة يجب أن يكون أقل من 5MB'))

            # التحقق من نوع الملف
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError(_('نوع الصورة غير مدعوم. يرجى استخدام JPG, PNG, GIF, أو WEBP'))

        return image

    def clean_rating(self):
        """التحقق من التقييم"""
        rating = self.cleaned_data.get('rating')
        if rating is not None and (rating < 1 or rating > 5):
            raise ValidationError(_('التقييم يجب أن يكون بين 1 و 5'))
        return rating

    def clean(self):
        """التحقق العام من النموذج"""
        cleaned_data = super().clean()

        # التأكد من وجود محتوى أو عنوان على الأقل
        title = cleaned_data.get('title')
        content = cleaned_data.get('content')

        if not title and not content:
            raise ValidationError(_('يجب كتابة عنوان أو تعليق على الأقل'))

        return cleaned_data


class ProductFilterForm(forms.Form):
    """
    نموذج فلترة المنتجات المحسن
    """
    # البحث
    q = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': _('ابحث عن منتجات...'),
            'autocomplete': 'off'
        }),
        label=_('البحث')
    )

    # نطاق السعر
    min_price = forms.DecimalField(
        required=False,
        min_value=Decimal('0'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control price-input',
            'placeholder': _('من'),
            'step': '0.01',
            'min': '0'
        }),
        label=_('الحد الأدنى للسعر')
    )

    max_price = forms.DecimalField(
        required=False,
        min_value=Decimal('0'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control price-input',
            'placeholder': _('إلى'),
            'step': '0.01',
            'min': '0'
        }),
        label=_('الحد الأقصى للسعر')
    )

    # الترتيب
    SORT_CHOICES = [
        ('newest', _('الأحدث')),
        ('oldest', _('الأقدم')),
        ('price_low', _('السعر: منخفض إلى مرتفع')),
        ('price_high', _('السعر: مرتفع إلى منخفض')),
        ('name_az', _('الاسم: أ-ي')),
        ('name_za', _('الاسم: ي-أ')),
        ('best_selling', _('الأكثر مبيعاً')),
        ('most_viewed', _('الأكثر مشاهدة')),
        ('top_rated', _('الأعلى تقييماً')),
        ('relevance', _('الأكثر صلة')),
    ]

    sort = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='newest',
        widget=forms.Select(attrs={
            'class': 'form-select sort-select'
        }),
        label=_('ترتيب النتائج')
    )

    # الفئة
    category = forms.ModelChoiceField(
        queryset=None,  # سيتم تعيينها في __init__
        required=False,
        empty_label=_('جميع الفئات'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الفئة')
    )

    # العلامة التجارية
    brand = forms.ModelMultipleChoiceField(
        queryset=None,  # سيتم تعيينها في __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label=_('العلامة التجارية')
    )

    # الميزات
    is_new = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('منتجات جديدة')
    )

    is_featured = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('منتجات مميزة')
    )

    on_sale = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('عروض وخصومات')
    )

    in_stock = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('متوفر في المخزون')
    )

    # التقييم
    min_rating = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '5',
            'placeholder': _('أقل تقييم')
        }),
        label=_('أقل تقييم')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعيين querysets للفئات والعلامات التجارية
        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        ).order_by('level', 'name')

        self.fields['brand'].queryset = Brand.objects.filter(
            is_active=True
        ).order_by('name')

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')

        # التحقق من نطاق السعر
        if min_price and max_price and min_price > max_price:
            raise ValidationError(_('الحد الأدنى للسعر يجب أن يكون أقل من الحد الأقصى'))

        # التحقق من صحة البحث
        q = cleaned_data.get('q')
        if q and len(q.strip()) < 2:
            cleaned_data['q'] = ''  # مسح البحث إذا كان قصيراً جداً

        return cleaned_data


class QuickAddToCartForm(forms.Form):
    """
    نموذج إضافة سريعة للسلة
    """
    product_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        min_value=1
    )

    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control quantity-input',
            'min': '1',
            'value': '1'
        }),
        label=_('الكمية')
    )

    variant_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        if product:
            # تعيين الحد الأقصى للكمية
            max_qty = getattr(product, 'max_order_quantity', 10)
            self.fields['quantity'].widget.attrs['max'] = max_qty

            # إضافة حقل اختيار المتغيرات إذا وجدت
            if hasattr(product, 'variants') and product.variants.filter(is_active=True).exists():
                variants = product.variants.filter(is_active=True).order_by('name')
                choices = [('', _('اختر النوع'))] + [(v.id, str(v)) for v in variants]

                self.fields['variant_id'] = forms.ChoiceField(
                    choices=choices,
                    required=False,
                    widget=forms.Select(attrs={
                        'class': 'form-select variant-select'
                    }),
                    label=_('اختر النوع')
                )

    def clean_quantity(self):
        """التحقق من الكمية"""
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError(_('الكمية يجب أن تكون أكبر من صفر'))
        return quantity


class CompareProductsForm(forms.Form):
    """
    نموذج مقارنة المنتجات
    """
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True, status='published'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input compare-checkbox'
        }),
        required=True,
        label=_('اختر المنتجات للمقارنة'),
        help_text=_('اختر من 2 إلى 4 منتجات للمقارنة'),
        error_messages={
            'required': _('يرجى اختيار منتجات للمقارنة'),
        }
    )

    def clean_products(self):
        """التحقق من المنتجات المختارة للمقارنة"""
        products = self.cleaned_data.get('products')

        if not products:
            raise ValidationError(_('يرجى اختيار منتجات للمقارنة'))

        if len(products) < 2:
            raise ValidationError(_('يجب اختيار منتجين على الأقل للمقارنة'))

        if len(products) > 4:
            raise ValidationError(_('لا يمكن مقارنة أكثر من 4 منتجات في نفس الوقت'))

        return products


class AdvancedSearchForm(forms.Form):
    """
    نموذج البحث المتقدم
    """
    # البحث النصي
    q = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': _('ابحث عن منتجات، فئات، علامات تجارية...'),
            'autocomplete': 'off'
        }),
        label=_('كلمات البحث')
    )

    # البحث في الحقول المحددة
    search_in = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('name', _('اسم المنتج')),
            ('description', _('الوصف')),
            ('sku', _('رمز المنتج')),
            ('brand', _('العلامة التجارية')),
            ('category', _('الفئة')),
            ('tags', _('الوسوم')),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label=_('البحث في'),
        initial=['name', 'description']
    )

    # الفئة
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label=_('جميع الفئات'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الفئة')
    )

    # العلامات التجارية
    brands = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label=_('العلامات التجارية')
    )

    # نطاقات السعر المحددة مسبقاً
    price_range = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('جميع الأسعار')),
            ('0-25', _('أقل من 25 ر.س')),
            ('25-50', _('25 - 50 ر.س')),
            ('50-100', _('50 - 100 ر.س')),
            ('100-200', _('100 - 200 ر.س')),
            ('200-500', _('200 - 500 ر.س')),
            ('500-1000', _('500 - 1000 ر.س')),
            ('1000+', _('أكثر من 1000 ر.س')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('نطاق السعر')
    )

    # السعر المخصص
    custom_min_price = forms.DecimalField(
        required=False,
        min_value=Decimal('0'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('السعر الأدنى'),
            'step': '0.01'
        }),
        label=_('السعر الأدنى (مخصص)')
    )

    custom_max_price = forms.DecimalField(
        required=False,
        min_value=Decimal('0'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('السعر الأعلى'),
            'step': '0.01'
        }),
        label=_('السعر الأعلى (مخصص)')
    )

    # التقييم
    min_rating = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('جميع التقييمات')),
            ('4', _('4 نجوم فأكثر')),
            ('3', _('3 نجوم فأكثر')),
            ('2', _('نجمتان فأكثر')),
            ('1', _('نجمة واحدة فأكثر')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('التقييم الأدنى')
    )

    # الميزات
    features = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('is_new', _('منتجات جديدة')),
            ('is_featured', _('منتجات مميزة')),
            ('on_sale', _('عروض وخصومات')),
            ('free_shipping', _('شحن مجاني')),
            ('in_stock', _('متوفر في المخزون')),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label=_('الميزات')
    )

    # الوسوم
    tags = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label=_('الوسوم')
    )

    # تاريخ الإضافة
    date_added = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('أي وقت')),
            ('today', _('اليوم')),
            ('week', _('آخر أسبوع')),
            ('month', _('آخر شهر')),
            ('3months', _('آخر 3 أشهر')),
            ('year', _('آخر سنة')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('تاريخ الإضافة')
    )

    # الترتيب
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('relevance', _('الأكثر صلة')),
            ('newest', _('الأحدث')),
            ('oldest', _('الأقدم')),
            ('price_low', _('السعر: منخفض إلى مرتفع')),
            ('price_high', _('السعر: مرتفع إلى منخفض')),
            ('name_az', _('الاسم: أ-ي')),
            ('name_za', _('الاسم: ي-أ')),
            ('best_selling', _('الأكثر مبيعاً')),
            ('most_viewed', _('الأكثر مشاهدة')),
            ('top_rated', _('الأعلى تقييماً')),
        ],
        initial='relevance',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('ترتيب النتائج')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعيين querysets
        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        ).order_by('level', 'name')

        self.fields['brands'].queryset = Brand.objects.filter(
            is_active=True
        ).order_by('name')

        self.fields['tags'].queryset = Tag.objects.all().order_by('name')

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        # التحقق من السعر المخصص
        custom_min = cleaned_data.get('custom_min_price')
        custom_max = cleaned_data.get('custom_max_price')

        if custom_min and custom_max and custom_min > custom_max:
            raise ValidationError(_('السعر الأدنى يجب أن يكون أقل من السعر الأعلى'))

        return cleaned_data


class NewsletterSubscriptionForm(forms.Form):
    """
    نموذج الاشتراك في النشرة الإخبارية
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('بريدك الإلكتروني'),
            'required': True
        }),
        label=_('البريد الإلكتروني'),
        error_messages={
            'required': _('البريد الإلكتروني مطلوب'),
            'invalid': _('يرجى إدخال بريد إلكتروني صحيح'),
        }
    )

    name = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('اسمك (اختياري)')
        }),
        label=_('الاسم')
    )

    interests = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('new_products', _('منتجات جديدة')),
            ('offers', _('عروض وخصومات')),
            ('industry_news', _('أخبار الصناعة')),
            ('technical_tips', _('نصائح تقنية')),
            ('reviews', _('مراجعات المنتجات')),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label=_('الاهتمامات')
    )

    def clean_email(self):
        """التحقق من صحة البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if email:
            # تطبيق regex للتحقق من صحة البريد الإلكتروني
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise ValidationError(_('يرجى إدخال بريد إلكتروني صحيح'))
        return email


class ContactSellerForm(forms.Form):
    """
    نموذج التواصل مع البائع
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('اسمك الكامل')
        }),
        label=_('الاسم'),
        validators=[MinLengthValidator(2)]
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('بريدك الإلكتروني')
        }),
        label=_('البريد الإلكتروني')
    )

    phone = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('رقم الهاتف (اختياري)')
        }),
        label=_('رقم الهاتف')
    )

    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('موضوع الاستفسار')
        }),
        label=_('الموضوع'),
        validators=[MinLengthValidator(5)]
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': _('اكتب استفسارك هنا...'),
            'rows': 5
        }),
        label=_('الرسالة'),
        validators=[MinLengthValidator(20)]
    )

    product_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False
    )

    def clean_phone(self):
        """التحقق من رقم الهاتف"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # إزالة جميع الأحرف غير الرقمية
            phone_digits = re.sub(r'\D', '', phone)
            if len(phone_digits) < 8:
                raise ValidationError(_('رقم الهاتف قصير جداً'))
            if len(phone_digits) > 15:
                raise ValidationError(_('رقم الهاتف طويل جداً'))
        return phone


class BulkActionForm(forms.Form):
    """
    نموذج العمليات المجمعة للمنتجات
    """
    ACTION_CHOICES = [
        ('', _('اختر عملية')),
        ('activate', _('تفعيل')),
        ('deactivate', _('إلغاء تفعيل')),
        ('delete', _('حذف')),
        ('export', _('تصدير')),
        ('set_featured', _('جعل مميز')),
        ('unset_featured', _('إلغاء مميز')),
        ('apply_discount', _('تطبيق خصم')),
        ('remove_discount', _('إزالة خصم')),
        ('change_category', _('تغيير الفئة')),
        ('change_brand', _('تغيير العلامة التجارية')),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'bulk-action-select'
        }),
        label=_('العملية')
    )

    product_ids = forms.CharField(
        widget=forms.HiddenInput()
    )

    # حقول إضافية للعمليات المحددة
    discount_percentage = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('نسبة الخصم (%)'),
            'step': '0.01'
        }),
        label=_('نسبة الخصم')
    )

    new_category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label=_('اختر فئة جديدة'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الفئة الجديدة')
    )

    new_brand = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label=_('اختر علامة تجارية جديدة'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('العلامة التجارية الجديدة')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعيين querysets
        self.fields['new_category'].queryset = Category.objects.filter(is_active=True)
        self.fields['new_brand'].queryset = Brand.objects.filter(is_active=True)

    def clean_product_ids(self):
        """التحقق من معرفات المنتجات"""
        product_ids = self.cleaned_data.get('product_ids')
        if not product_ids:
            raise ValidationError(_('يجب اختيار منتجات على الأقل'))

        try:
            ids = [int(id.strip()) for id in product_ids.split(',') if id.strip()]
            if not ids:
                raise ValidationError(_('لا توجد منتجات محددة'))
            return ids
        except ValueError:
            raise ValidationError(_('معرفات المنتجات غير صحيحة'))

    def clean(self):
        """التحقق الشامل من النموذج"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')

        # التحقق من الحقول المطلوبة لكل عملية
        if action == 'apply_discount':
            discount_percentage = cleaned_data.get('discount_percentage')
            if not discount_percentage:
                raise ValidationError({
                    'discount_percentage': _('يجب تحديد نسبة الخصم')
                })

        elif action == 'change_category':
            new_category = cleaned_data.get('new_category')
            if not new_category:
                raise ValidationError({
                    'new_category': _('يجب اختيار فئة جديدة')
                })

        elif action == 'change_brand':
            new_brand = cleaned_data.get('new_brand')
            if not new_brand:
                raise ValidationError({
                    'new_brand': _('يجب اختيار علامة تجارية جديدة')
                })

        return cleaned_data


class ProductReportForm(forms.Form):
    """
    نموذج الإبلاغ عن منتج
    """
    REPORT_CHOICES = [
        ('inappropriate', _('محتوى غير مناسب')),
        ('fake', _('منتج مزيف')),
        ('wrong_info', _('معلومات خاطئة')),
        ('spam', _('بريد مزعج')),
        ('copyright', _('انتهاك حقوق الطبع')),
        ('price_manipulation', _('تلاعب في الأسعار')),
        ('misleading', _('إعلان مضلل')),
        ('other', _('أخرى')),
    ]

    reason = forms.ChoiceField(
        choices=REPORT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('سبب الإبلاغ')
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': _('اكتب تفاصيل إضافية (اختياري)'),
            'rows': 3
        }),
        required=False,
        label=_('تفاصيل إضافية'),
        max_length=500
    )

    product_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean_description(self):
        """التحقق من الوصف"""
        description = self.cleaned_data.get('description', '')
        reason = self.cleaned_data.get('reason')

        if reason == 'other' and not description.strip():
            raise ValidationError(_('يرجى كتابة تفاصيل عند اختيار "أخرى"'))

        return description.strip()


class QuickContactForm(forms.Form):
    """
    نموذج تواصل سريع
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('اسمك')
        }),
        label=_('الاسم')
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('بريدك الإلكتروني')
        }),
        label=_('البريد الإلكتروني')
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': _('رسالتك'),
            'rows': 3
        }),
        label=_('الرسالة'),
        validators=[MinLengthValidator(10)]
    )


# Helper function للتحقق من النماذج
def validate_form_fields(model_class, form_fields):
    """
    دالة مساعدة للتحقق من توافق حقول النموذج مع النموذج
    """
    model_fields = [field.name for field in model_class._meta.fields]
    invalid_fields = [field for field in form_fields if field not in model_fields]

    if invalid_fields:
        raise ValidationError(
            f"الحقول التالية غير موجودة في النموذج {model_class.__name__}: {invalid_fields}"
        )

    return True


# تحقق من توافق النماذج عند استيراد الملف
try:
    # التحقق من نموذج ProductReviewForm
    review_fields = ['rating', 'title', 'content', 'image']
    validate_form_fields(ProductReview, review_fields)
except Exception as e:
    print(f"تحذير: مشكلة في توافق النماذج - {e}")