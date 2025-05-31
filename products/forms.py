# File: products/forms.py
"""
نماذج تطبيق المنتجات - النسخة النهائية المصححة
تتوافق مع نموذج ProductReview الصحيح
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
    نموذج إضافة تقييم للمنتج - مُصحح مع الحقول الصحيحة
    """

    class Meta:
        model = ProductReview
        # استخدام الحقول الصحيحة من النموذج
        fields = ['rating', 'title', 'content', 'image', 'recommend']
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
                'minlength': '10'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'recommend': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'rating': _('التقييم'),
            'title': _('عنوان التقييم'),
            'content': _('تعليقك'),
            'image': _('صورة (اختياري)'),
            'recommend': _('أوصي بهذا المنتج'),
        }
        help_texts = {
            'rating': _('قيّم المنتج من 1 إلى 5 نجوم'),
            'title': _('عنوان مختصر يلخص رأيك'),
            'content': _('اكتب تفاصيل تجربتك مع المنتج (10 أحرف على الأقل)'),
            'image': _('يمكنك رفع صورة للمنتج (حجم أقصى 5MB)'),
            'recommend': _('هل توصي بهذا المنتج للآخرين؟'),
        }

    def clean_content(self):
        """التحقق من محتوى التعليق"""
        content = self.cleaned_data.get('content')
        if content and len(content.strip()) < 10:
            raise ValidationError(_('التعليق يجب أن يكون 10 أحرف على الأقل'))
        return content.strip() if content else content

    def clean_title(self):
        """التحقق من عنوان التقييم"""
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 3:
            raise ValidationError(_('العنوان يجب أن يكون 3 أحرف على الأقل'))
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


class DetailedProductReviewForm(ProductReviewForm):
    """
    نموذج تقييم مفصل للمنتج مع تقييمات فرعية
    """

    class Meta(ProductReviewForm.Meta):
        fields = ProductReviewForm.Meta.fields + [
            'quality_rating', 'value_rating', 'delivery_rating'
        ]
        widgets = ProductReviewForm.Meta.widgets.copy()
        widgets.update({
            'quality_rating': forms.Select(
                choices=[(i, f'{i} ⭐') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'value_rating': forms.Select(
                choices=[(i, f'{i} ⭐') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'delivery_rating': forms.Select(
                choices=[(i, f'{i} ⭐') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
        })
        labels = ProductReviewForm.Meta.labels.copy()
        labels.update({
            'quality_rating': _('تقييم الجودة'),
            'value_rating': _('تقييم القيمة مقابل السعر'),
            'delivery_rating': _('تقييم التوصيل'),
        })


class ProductFilterForm(forms.Form):
    """
    نموذج فلترة المنتجات
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

    def clean_quantity(self):
        """التحقق من الكمية"""
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError(_('الكمية يجب أن تكون أكبر من صفر'))
        return quantity


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
    review_fields = ['rating', 'title', 'content', 'image', 'recommend']
    validate_form_fields(ProductReview, review_fields)
    print("✅ نماذج المراجعات متوافقة مع النموذج")
except Exception as e:
    print(f"⚠️ تحذير: مشكلة في توافق النماذج - {e}")