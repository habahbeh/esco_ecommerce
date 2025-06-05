# payment/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, HTML
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