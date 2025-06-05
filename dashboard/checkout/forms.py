# checkout/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, HTML, Row, Column
from crispy_forms.bootstrap import FormActions, TabHolder, Tab

import json

from checkout.models import (
    CheckoutSession, PaymentMethod, ShippingMethod, PaymentTransaction, Coupon
)

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