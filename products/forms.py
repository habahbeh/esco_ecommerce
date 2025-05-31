# products/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import re

from .models import ProductReview, Product, Category, Brand, Tag


class ProductReviewForm(forms.ModelForm):
    """
    نموذج إضافة تقييم للمنتج
    """

    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'comment', 'image1', 'image2', 'image3']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, i) for i in range(1, 6)],
                attrs={'class': 'rating-input'}
            ),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('عنوان مختصر لتقييمك'),
                'maxlength': '200'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('شاركنا تجربتك مع هذا المنتج...'),
                'rows': 5
            }),
            'image1': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'image2': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'image3': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'rating': _('التقييم'),
            'title': _('عنوان التقييم'),
            'comment': _('تعليقك'),
            'image1': _('صورة 1 (اختياري)'),
            'image2': _('صورة 2 (اختياري)'),
            'image3': _('صورة 3 (اختياري)'),
        }
        help_texts = {
            'rating': _('قيّم المنتج من 1 إلى 5 نجوم'),
            'title': _('عنوان مختصر يلخص رأيك'),
            'comment': _('اكتب تفاصيل تجربتك مع المنتج'),
            'image1': _('يمكنك رفع صور للمنتج (حجم أقصى 5MB)')
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if len(comment) < 20:
            raise forms.ValidationError(_('التعليق يجب أن يكون 20 حرف على الأقل'))
        return comment

    def clean(self):
        cleaned_data = super().clean()
        # Validate image sizes
        for field in ['image1', 'image2', 'image3']:
            image = cleaned_data.get(field)
            if image:
                if image.size > 5 * 1024 * 1024:  # 5MB
                    self.add_error(field, _('حجم الصورة يجب أن يكون أقل من 5MB'))
        return cleaned_data


class ProductFilterForm(forms.Form):
    """
    نموذج فلترة المنتجات
    """
    # Search
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('ابحث عن منتجات...')
        })
    )

    # Price range
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control price-input',
            'placeholder': _('من')
        })
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control price-input',
            'placeholder': _('إلى')
        })
    )

    # Sorting
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
    ]

    sort = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='newest',
        widget=forms.Select(attrs={
            'class': 'form-select sort-select'
        })
    )

    # Features
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
        label=_('متوفر في المخزن')
    )

    # Rating
    min_rating = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '5'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')

        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError(_('الحد الأدنى للسعر يجب أن يكون أقل من الحد الأقصى'))

        return cleaned_data


class QuickAddToCartForm(forms.Form):
    """
    نموذج إضافة سريعة للسلة
    """
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control quantity-input',
            'min': '1'
        })
    )
    variant_id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        if product:
            self.fields['quantity'].widget.attrs['max'] = product.max_order_quantity
            if product.variants.filter(is_active=True).exists():
                self.fields['variant_id'] = forms.ChoiceField(
                    choices=[(v.id, str(v)) for v in product.variants.filter(is_active=True)],
                    widget=forms.Select(attrs={
                        'class': 'form-select'
                    }),
                    label=_('اختر النوع')
                )


class CompareProductsForm(forms.Form):
    """
    نموذج مقارنة المنتجات
    """
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True, status='published'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=True,
        label='اختر المنتجات للمقارنة',
        help_text='اختر من 2 إلى 4 منتجات للمقارنة'
    )

    def clean_products(self):
        products = self.cleaned_data.get('products')

        if not products:
            raise ValidationError('يرجى اختيار منتجات للمقارنة')

        if len(products) < 2:
            raise ValidationError('يجب اختيار منتجين على الأقل للمقارنة')

        if len(products) > 4:
            raise ValidationError('لا يمكن مقارنة أكثر من 4 منتجات في نفس الوقت')

        return products


class ProductSearchForm(forms.Form):
    """
    نموذج البحث المتقدم
    """
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': _('ابحث عن منتجات، فئات، علامات تجارية...'),
            'autocomplete': 'off'
        })
    )

    category = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label=_('جميع الفئات'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    brand = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )

    price_range = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('جميع الأسعار')),
            ('0-50', _('أقل من 50 د.أ')),
            ('50-100', _('50 - 100 د.أ')),
            ('100-200', _('100 - 200 د.أ')),
            ('200-500', _('200 - 500 د.أ')),
            ('500+', _('أكثر من 500 د.أ')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    def __init__(self, *args, **kwargs):
        from .models import Category, Brand
        super().__init__(*args, **kwargs)

        # Set querysets
        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        ).order_by('level', 'name')

        self.fields['brand'].queryset = Brand.objects.filter(
            is_active=True
        ).order_by('name')


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
        label=_('البريد الإلكتروني')
    )

    name = forms.CharField(
        required=False,
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
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label=_('الاهتمامات')
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check for valid email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
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
        label=_('الاسم')
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
        label=_('الموضوع')
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
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove all non-digit characters
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
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('العملية')
    )

    product_ids = forms.CharField(
        widget=forms.HiddenInput()
    )

    # Additional fields for specific actions
    discount_percentage = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('نسبة الخصم (%)')
        }),
        label=_('نسبة الخصم')
    )

    def clean_product_ids(self):
        product_ids = self.cleaned_data.get('product_ids')
        if not product_ids:
            raise ValidationError(_('يجب اختيار منتجات على الأقل'))

        try:
            ids = [int(id) for id in product_ids.split(',') if id.strip()]
            if not ids:
                raise ValidationError(_('لا توجد منتجات محددة'))
            return ids
        except ValueError:
            raise ValidationError(_('معرفات المنتجات غير صحيحة'))

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')

        if action == 'apply_discount':
            discount_percentage = cleaned_data.get('discount_percentage')
            if not discount_percentage:
                raise ValidationError({
                    'discount_percentage': _('يجب تحديد نسبة الخصم')
                })

        return cleaned_data


class ProductVariantForm(forms.Form):
    """
    نموذج اختيار متغيرات المنتج
    """

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        if product and product.variants.filter(is_active=True).exists():
            variants = product.variants.filter(is_active=True).order_by('sort_order')

            # Group variants by type (color, size, etc.)
            variant_groups = {}
            for variant in variants:
                if variant.color:
                    if 'color' not in variant_groups:
                        variant_groups['color'] = []
                    variant_groups['color'].append((variant.id, variant.get_color_display()))

                if variant.size:
                    if 'size' not in variant_groups:
                        variant_groups['size'] = []
                    variant_groups['size'].append((variant.id, variant.get_size_display()))

            # Create fields for each variant group
            for group_name, choices in variant_groups.items():
                field_name = f'{group_name}_variant'
                self.fields[field_name] = forms.ChoiceField(
                    choices=[('', f'اختر {group_name}')] + choices,
                    required=False,
                    widget=forms.Select(attrs={
                        'class': 'form-select variant-select',
                        'data-variant-type': group_name
                    }),
                    label=_(group_name.title())
                )


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
        label=_('تفاصيل إضافية')
    )

    product_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        reason = self.cleaned_data.get('reason')

        if reason == 'other' and not description:
            raise ValidationError(_('يرجى كتابة تفاصيل عند اختيار "أخرى"'))

        return description