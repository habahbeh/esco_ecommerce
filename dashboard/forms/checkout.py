"""
نماذج إدارة عمليات الدفع - يحتوي على نماذج متعلقة بعمليات الدفع والشحن والكوبونات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Div, HTML, Row, Column
from crispy_forms.bootstrap import FormActions, TabHolder, Tab

import json

from checkout.models import (
    CheckoutSession, PaymentMethod, ShippingMethod, PaymentTransaction, Coupon
)
from accounts.models import UserAddress


class PaymentMethodForm(forms.ModelForm):
    """نموذج إنشاء وتعديل طرق الدفع"""

    class Meta:
        model = PaymentMethod
        fields = [
            'name', 'code', 'payment_type', 'description', 'icon',
            'instructions', 'fee_fixed', 'fee_percentage',
            'is_active', 'is_default', 'min_amount', 'max_amount',
            'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fee_fixed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fee_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    api_credentials = forms.CharField(
        label=_('بيانات اعتماد API'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل بيانات اعتماد API بتنسيق JSON')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعبئة حقل API credentials
        if self.instance.pk and self.instance.api_credentials:
            self.fields['api_credentials'].initial = json.dumps(
                self.instance.api_credentials,
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
                        Column('code', css_class='col-md-6'),
                    ),
                    'payment_type',
                    'description',
                    'instructions',
                    ),

                Tab(_('الرسوم والتكاليف'),
                    Row(
                        Column('fee_fixed', css_class='col-md-6'),
                        Column('fee_percentage', css_class='col-md-6'),
                    ),
                    Row(
                        Column('min_amount', css_class='col-md-6'),
                        Column('max_amount', css_class='col-md-6'),
                    ),
                    ),

                Tab(_('الإعدادات'),
                    Row(
                        Column('is_active', css_class='col-md-6'),
                        Column('is_default', css_class='col-md-6'),
                    ),
                    'sort_order',
                    'icon',
                    ),

                Tab(_('إعدادات API'),
                    'api_credentials',
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML(
                    '<a href="{% url "dashboard:payment_method_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean_api_credentials(self):
        creds = self.cleaned_data.get('api_credentials')
        if not creds:
            return {}

        try:
            return json.loads(creds)
        except json.JSONDecodeError:
            raise ValidationError(_('تنسيق JSON غير صالح لبيانات الاعتماد'))

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من المبالغ
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')

        if min_amount is not None and max_amount is not None and max_amount > 0:
            if min_amount > max_amount:
                self.add_error('max_amount', _('يجب أن يكون الحد الأقصى أكبر من الحد الأدنى'))

        return cleaned_data


class ShippingMethodForm(forms.ModelForm):
    """نموذج إنشاء وتعديل طرق الشحن"""

    class Meta:
        model = ShippingMethod
        fields = [
            'name', 'code', 'description', 'icon',
            'base_cost', 'free_shipping_threshold',
            'estimated_days_min', 'estimated_days_max',
            'is_active', 'is_default', 'sort_order',
            'restrictions'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'base_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'free_shipping_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_days_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'estimated_days_max': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'restrictions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    countries = forms.CharField(
        label=_('الدول المتاحة'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل قائمة الدول المتاحة بتنسيق JSON أو مفصولة بسطور جديدة')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعبئة حقل الدول
        if self.instance.pk and self.instance.countries:
            if isinstance(self.instance.countries, list):
                self.fields['countries'].initial = '\n'.join(self.instance.countries)
            else:
                self.fields['countries'].initial = json.dumps(
                    self.instance.countries,
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
                        Column('code', css_class='col-md-6'),
                    ),
                    'description',
                    ),

                Tab(_('التكاليف والوقت'),
                    Row(
                        Column('base_cost', css_class='col-md-6'),
                        Column('free_shipping_threshold', css_class='col-md-6'),
                    ),
                    Row(
                        Column('estimated_days_min', css_class='col-md-6'),
                        Column('estimated_days_max', css_class='col-md-6'),
                    ),
                    ),

                Tab(_('الإعدادات'),
                    Row(
                        Column('is_active', css_class='col-md-6'),
                        Column('is_default', css_class='col-md-6'),
                    ),
                    'sort_order',
                    'icon',
                    ),

                Tab(_('القيود والدول'),
                    'restrictions',
                    'countries',
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:shipping_method_list" %}" class="btn btn-secondary">%s</a>' % _(
                    'إلغاء'))
            )
        )

    def clean_countries(self):
        countries = self.cleaned_data.get('countries')
        if not countries:
            return []

        try:
            # محاولة معالجة كـ JSON
            return json.loads(countries)
        except json.JSONDecodeError:
            # معالجة كقائمة مفصولة بسطور
            return [line.strip() for line in countries.split('\n') if line.strip()]

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من أيام التوصيل
        min_days = cleaned_data.get('estimated_days_min')
        max_days = cleaned_data.get('estimated_days_max')

        if min_days is not None and max_days is not None:
            if min_days > max_days:
                self.add_error('estimated_days_max', _('يجب أن يكون الحد الأقصى للأيام أكبر من أو يساوي الحد الأدنى'))

        return cleaned_data


class CheckoutAddressForm(forms.ModelForm):
    """نموذج عنوان الشحن في صفحة الدفع"""

    use_existing_address = forms.BooleanField(
        label=_('استخدام عنوان موجود'),
        required=False
    )

    existing_address = forms.ModelChoiceField(
        label=_('اختر عنوانًا'),
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = UserAddress
        fields = [
            'first_name', 'last_name', 'address_line_1', 'address_line_2',
            'city', 'state', 'postal_code', 'country', 'phone_number'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # إذا كان المستخدم مسجلًا، نعرض عناوينه المحفوظة
        if self.user and self.user.is_authenticated:
            self.fields['existing_address'].queryset = UserAddress.objects.filter(user=self.user)
        else:
            # إذا لم يكن المستخدم مسجلًا، نخفي حقول العناوين المحفوظة
            self.fields['use_existing_address'].widget = forms.HiddenInput()
            self.fields['existing_address'].widget = forms.HiddenInput()

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        # تنظيم الحقول
        self.helper.layout = Layout(
            Div(
                'use_existing_address',
                'existing_address',
                css_class='mb-3 existing-address-section',
                # إخفاء هذا القسم إذا لم يكن المستخدم مسجلًا
                style='display: none;' if not (self.user and self.user.is_authenticated) else ''
            ),
            Div(
                Fieldset(
                    _('عنوان الشحن'),
                    Row(
                        Column('first_name', css_class='col-md-6'),
                        Column('last_name', css_class='col-md-6'),
                    ),
                    'address_line_1',
                    'address_line_2',
                    Row(
                        Column('city', css_class='col-md-6'),
                        Column('state', css_class='col-md-6'),
                    ),
                    Row(
                        Column('postal_code', css_class='col-md-6'),
                        Column('country', css_class='col-md-6'),
                    ),
                    'phone_number',
                ),
                css_class='new-address-section'
            ),
            FormActions(
                Submit('save', _('حفظ وتابع'), css_class='btn btn-primary'),
                HTML('<a href="{% url "cart:view" %}" class="btn btn-secondary">%s</a>' % _('العودة للسلة'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        use_existing = cleaned_data.get('use_existing_address')
        existing_address = cleaned_data.get('existing_address')

        # إذا اختار المستخدم استخدام عنوان موجود، يجب تحديده
        if use_existing and not existing_address:
            self.add_error('existing_address', _('يرجى اختيار عنوان'))

        # إذا لم يختر استخدام عنوان موجود، يجب ملء حقول العنوان الجديد
        if not use_existing:
            required_fields = ['first_name', 'last_name', 'address_line_1', 'city', 'country', 'phone_number']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('هذا الحقل مطلوب'))

        return cleaned_data


class CouponForm(forms.ModelForm):
    """نموذج إنشاء وتعديل كوبونات الخصم"""

    class Meta:
        model = Coupon
        fields = [
            'code', 'description', 'discount_type', 'discount_value',
            'max_discount_amount', 'min_purchase_amount', 'valid_from',
            'valid_to', 'is_active', 'usage_limit', 'used_count',
            'is_one_time_use', 'categories', 'products', 'excluded_products'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_purchase_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'used_count': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-select select2', 'multiple': 'multiple'}),
            'products': forms.SelectMultiple(attrs={'class': 'form-select select2', 'multiple': 'multiple'}),
            'excluded_products': forms.SelectMultiple(attrs={'class': 'form-select select2', 'multiple': 'multiple'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('معلومات الكوبون'),
                    'code',
                    'description',
                    Row(
                        Column('discount_type', css_class='col-md-4'),
                        Column('discount_value', css_class='col-md-4'),
                        Column('max_discount_amount', css_class='col-md-4'),
                    ),
                    'min_purchase_amount',
                    ),

                Tab(_('الصلاحية والاستخدام'),
                    Row(
                        Column('valid_from', css_class='col-md-6'),
                        Column('valid_to', css_class='col-md-6'),
                    ),
                    Row(
                        Column('usage_limit', css_class='col-md-4'),
                        Column('used_count', css_class='col-md-4'),
                        Column('is_one_time_use', css_class='col-md-4'),
                    ),
                    'is_active',
                    ),

                Tab(_('القيود'),
                    'categories',
                    'products',
                    'excluded_products',
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:coupon_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من تواريخ الصلاحية
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')

        if valid_from and valid_to and valid_from >= valid_to:
            self.add_error('valid_to', _('يجب أن يكون تاريخ انتهاء الصلاحية بعد تاريخ بداية الصلاحية'))

        # التحقق من نوع الخصم وقيمته
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')

        if discount_type == 'percentage' and discount_value:
            if discount_value <= 0 or discount_value > 100:
                self.add_error('discount_value', _('يجب أن تكون نسبة الخصم بين 1 و 100'))

        return cleaned_data


class CheckoutPaymentForm(forms.Form):
    """نموذج اختيار طريقة الدفع في صفحة الدفع"""
    payment_method = forms.ModelChoiceField(
        label=_('اختر طريقة الدفع'),
        queryset=None,
        widget=forms.RadioSelect(),
        empty_label=None
    )

    save_payment_info = forms.BooleanField(
        label=_('حفظ معلومات الدفع للمستقبل'),
        required=False,
        initial=True
    )

    def __init__(self, *args, **kwargs):
        self.total_amount = kwargs.pop('total_amount', 0)
        super().__init__(*args, **kwargs)

        # تقييد الاختيار لطرق الدفع النشطة والمتوافقة مع مبلغ الطلب
        self.fields['payment_method'].queryset = PaymentMethod.objects.filter(
            is_active=True,
            min_amount__lte=self.total_amount
        ).filter(
            # تضمين الطرق التي ليس لها حد أقصى أو الحد الأقصى أكبر من المبلغ
            # نستخدم Q للتعبير عن الشرط المنطقي OR
            models.Q(max_amount__isnull=True) | models.Q(max_amount__gte=self.total_amount)
        ).order_by('sort_order')

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('اختر طريقة الدفع'),
                'payment_method',
                Div(
                    HTML('<div id="payment-method-details" class="mb-3 p-3 border rounded"></div>'),
                    css_class='payment-method-details-container'
                ),
                'save_payment_info',
            ),
            FormActions(
                Submit('continue', _('متابعة'), css_class='btn btn-primary'),
                HTML('<a href="{% url "checkout:shipping" %}" class="btn btn-secondary">%s</a>' % _('الرجوع'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')

        if not payment_method:
            self.add_error('payment_method', _('يرجى اختيار طريقة دفع'))

        return cleaned_data