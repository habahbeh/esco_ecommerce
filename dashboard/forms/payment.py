"""
نماذج إدارة المدفوعات - يحتوي على نماذج متعلقة بالمدفوعات والمعاملات المالية واسترداد المبالغ
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Div, HTML, Row, Column
from crispy_forms.bootstrap import FormActions

from payment.models import Transaction, Payment, Refund


class PaymentRefundForm(forms.ModelForm):
    """نموذج استرداد المدفوعات"""

    class Meta:
        model = Refund
        fields = [
            'amount', 'reason', 'customer_notes', 'admin_notes'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'customer_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    full_refund = forms.BooleanField(
        label=_('استرداد كامل المبلغ'),
        required=False,
        initial=True
    )

    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تعيين المبلغ الأقصى
        if self.payment:
            max_amount = self.payment.amount
            self.fields['amount'].widget.attrs['max'] = max_amount
            self.fields['amount'].initial = max_amount
            self.fields['amount'].help_text = _('الحد الأقصى: {amount} {currency}').format(
                amount=max_amount,
                currency=self.payment.currency
            )

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('معلومات الاسترداد'),
                'full_refund',
                'amount',
                'reason',
            ),
            Fieldset(
                _('الملاحظات'),
                'customer_notes',
                'admin_notes',
            ),
            FormActions(
                Submit('submit', _('استرداد المبلغ'), css_class='btn btn-warning'),
                HTML(
                    '<a href="{% url "dashboard:payment_detail" pk=payment.pk %}" class="btn btn-secondary">%s</a>' % _(
                        'إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        # إذا تم اختيار استرداد كامل المبلغ، تعيين المبلغ تلقائيًا
        full_refund = cleaned_data.get('full_refund')
        amount = cleaned_data.get('amount')

        if full_refund and self.payment:
            cleaned_data['amount'] = self.payment.amount
        elif amount:
            # التحقق من المبلغ
            if self.payment and amount > self.payment.amount:
                self.add_error('amount', _('لا يمكن أن يكون مبلغ الاسترداد أكبر من مبلغ الدفع'))

            if amount <= 0:
                self.add_error('amount', _('يجب أن يكون مبلغ الاسترداد أكبر من صفر'))

        return cleaned_data

    def save(self, commit=True):
        refund = super().save(commit=False)

        # تعيين الحقول الأخرى
        if self.payment:
            refund.payment = self.payment
            refund.order = self.payment.order
            refund.user = self.payment.user
            refund.currency = self.payment.currency
            refund.refund_gateway = self.payment.payment_gateway

        if self.user:
            refund.requested_by = self.user

        if commit:
            refund.save()

            # إنشاء معاملة مالية للاسترداد
            refund.create_transaction()

        return refund


class PaymentTransactionForm(forms.ModelForm):
    """نموذج إنشاء وتعديل المعاملات المالية"""

    class Meta:
        model = Transaction
        fields = [
            'transaction_type', 'amount', 'currency', 'status',
            'reference_number', 'payment_gateway', 'gateway_transaction_id',
            'description', 'metadata'
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'payment_gateway': forms.TextInput(attrs={'class': 'form-control'}),
            'gateway_transaction_id': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    metadata_field = forms.CharField(
        label=_('بيانات إضافية'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل البيانات الإضافية بتنسيق JSON')
    )

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

        # تعبئة حقل البيانات الإضافية
        if self.instance.pk and self.instance.metadata:
            import json
            self.fields['metadata_field'].initial = json.dumps(
                self.instance.metadata,
                indent=4,
                ensure_ascii=False
            )

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('معلومات المعاملة'),
                Row(
                    Column('transaction_type', css_class='col-md-6'),
                    Column('status', css_class='col-md-6'),
                ),
                Row(
                    Column('amount', css_class='col-md-6'),
                    Column('currency', css_class='col-md-6'),
                ),
                'description',
            ),
            Fieldset(
                _('معلومات البوابة'),
                Row(
                    Column('payment_gateway', css_class='col-md-6'),
                    Column('gateway_transaction_id', css_class='col-md-6'),
                ),
                'reference_number',
                'metadata_field',
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:transaction_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean_metadata_field(self):
        metadata = self.cleaned_data.get('metadata_field')
        if not metadata:
            return {}

        try:
            import json
            return json.loads(metadata)
        except json.JSONDecodeError:
            raise forms.ValidationError(_('تنسيق JSON غير صالح للبيانات الإضافية'))

    def save(self, commit=True):
        transaction = super().save(commit=False)

        # تعيين البيانات الإضافية
        transaction.metadata = self.cleaned_data.get('metadata_field', {})

        # تعيين المعاملة بالطلب إذا تم تمريره
        if self.order and not transaction.order_id:
            transaction.order = self.order

        if commit:
            transaction.save()

        return transaction


class PaymentForm(forms.ModelForm):
    """نموذج إنشاء وتعديل المدفوعات"""

    # حقول إضافية لتسهيل إدخال تاريخ انتهاء البطاقة
    card_expiry_month = forms.CharField(
        label=_('شهر انتهاء البطاقة'),
        required=False,
        max_length=2,
        widget=forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'min': '1', 'max': '12'})
    )

    card_expiry_year = forms.CharField(
        label=_('سنة انتهاء البطاقة'),
        required=False,
        max_length=4,
        widget=forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'min': '2023', 'max': '2050'})
    )

    class Meta:
        model = Payment
        fields = [
            'amount', 'currency', 'status', 'payment_method',
            'payment_gateway', 'gateway_payment_id', 'billing_address',
            'card_type', 'last_4_digits', 'card_expiry',
            'notes'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_gateway': forms.TextInput(attrs={'class': 'form-control'}),
            'gateway_payment_id': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'card_type': forms.TextInput(attrs={'class': 'form-control'}),
            'last_4_digits': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'maxlength': '4'}),
            'card_expiry': forms.HiddenInput(),  # نخفي هذا الحقل ونستخدم الحقلين الإضافيين بدلاً منه
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

        # تعبئة حقول تاريخ انتهاء البطاقة من حقل card_expiry
        if self.instance.pk and self.instance.card_expiry:
            try:
                parts = self.instance.card_expiry.split('/')
                if len(parts) == 2:
                    self.fields['card_expiry_month'].initial = parts[0]
                    self.fields['card_expiry_year'].initial = parts[1]
            except:
                pass

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('معلومات الدفع'),
                Row(
                    Column('amount', css_class='col-md-4'),
                    Column('currency', css_class='col-md-4'),
                    Column('status', css_class='col-md-4'),
                ),
                Row(
                    Column('payment_method', css_class='col-md-6'),
                    Column('payment_gateway', css_class='col-md-6'),
                ),
                'gateway_payment_id',
                'billing_address',
            ),
            Fieldset(
                _('معلومات البطاقة (اختياري)'),
                Row(
                    Column('card_type', css_class='col-md-4'),
                    Column('last_4_digits', css_class='col-md-4'),
                    Column(
                        Row(
                            Column('card_expiry_month', css_class='col-md-6'),
                            Column('card_expiry_year', css_class='col-md-6'),
                        ),
                        css_class='col-md-4'
                    ),
                ),
                Field('card_expiry', type="hidden"),
            ),
            Fieldset(
                _('ملاحظات'),
                'notes',
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:payment_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        # تحويل شهر وسنة انتهاء البطاقة إلى تنسيق MM/YYYY
        month = cleaned_data.get('card_expiry_month')
        year = cleaned_data.get('card_expiry_year')

        if month and year:
            # التأكد من صحة الشهر
            try:
                month_num = int(month)
                if month_num < 1 or month_num > 12:
                    self.add_error('card_expiry_month', _('يجب أن يكون الشهر بين 1 و 12'))
                else:
                    # تنسيق الشهر بشكل صحيح (مثلاً: 01، 02، ... إلخ)
                    month = f"{month_num:02d}"
            except ValueError:
                self.add_error('card_expiry_month', _('الشهر يجب أن يكون رقماً'))

            # التأكد من صحة السنة
            try:
                year_num = int(year)
                current_year = timezone.now().year
                if year_num < current_year or year_num > current_year + 30:
                    self.add_error('card_expiry_year', _('السنة غير صالحة'))
            except ValueError:
                self.add_error('card_expiry_year', _('السنة يجب أن تكون رقماً'))

            # إذا لم تكن هناك أخطاء، قم بتعيين حقل card_expiry
            if 'card_expiry_month' not in self.errors and 'card_expiry_year' not in self.errors:
                cleaned_data['card_expiry'] = f"{month}/{year}"

        return cleaned_data

    def save(self, commit=True):
        payment = super().save(commit=False)

        # تعيين الطلب إذا تم تمريره
        if self.order and not payment.order_id:
            payment.order = self.order

        if commit:
            payment.save()

        return payment