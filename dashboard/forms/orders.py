"""
نماذج إدارة الطلبات - يحتوي على نماذج متعلقة بالطلبات وعناصرها وحالاتها
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Div, HTML, Row, Column
from crispy_forms.bootstrap import FormActions, TabHolder, Tab

from orders.models import Order, OrderItem
from products.models import Product, ProductVariant

User = get_user_model()


class OrderForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الطلبات"""

    class Meta:
        model = Order
        fields = [
            'order_number', 'user', 'full_name', 'email', 'phone',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_country', 'shipping_postal_code', 'shipping_cost',
            'tax_amount', 'discount_amount', 'status', 'payment_status',
            'payment_method', 'notes'
        ]
        widgets = {
            'order_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'user': forms.Select(attrs={'class': 'form-select select2'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_state': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_country': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.is_edit_mode = kwargs.pop('is_edit_mode', False)
        super().__init__(*args, **kwargs)

        # تقييد الاختيار للمستخدمين
        self.fields['user'].queryset = User.objects.filter(is_active=True)

        # في حالة التعديل، جعل بعض الحقول للقراءة فقط
        if self.is_edit_mode:
            for field_name in ['user', 'order_number']:
                self.fields[field_name].widget.attrs['readonly'] = True

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('معلومات الطلب'),
                    Row(
                        Column('order_number', css_class='col-md-6'),
                        Column('user', css_class='col-md-6'),
                    ),
                    Row(
                        Column('status', css_class='col-md-6'),
                        Column('payment_status', css_class='col-md-6'),
                    ),
                    'payment_method',
                    'notes',
                    ),

                Tab(_('معلومات العميل'),
                    Row(
                        Column('full_name', css_class='col-md-6'),
                        Column('email', css_class='col-md-6'),
                    ),
                    'phone',
                    ),

                Tab(_('عنوان الشحن'),
                    'shipping_address',
                    Row(
                        Column('shipping_city', css_class='col-md-6'),
                        Column('shipping_state', css_class='col-md-6'),
                    ),
                    Row(
                        Column('shipping_country', css_class='col-md-6'),
                        Column('shipping_postal_code', css_class='col-md-6'),
                    ),
                    ),

                Tab(_('التكاليف'),
                    Row(
                        Column('shipping_cost', css_class='col-md-4'),
                        Column('tax_amount', css_class='col-md-4'),
                        Column('discount_amount', css_class='col-md-4'),
                    ),
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:order_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من معلومات العميل
        full_name = cleaned_data.get('full_name')
        email = cleaned_data.get('email')

        if not full_name:
            self.add_error('full_name', _('يجب تحديد اسم العميل'))

        if not email:
            self.add_error('email', _('يجب تحديد البريد الإلكتروني للعميل'))

        return cleaned_data


class OrderItemForm(forms.ModelForm):
    """نموذج إضافة وتعديل عناصر الطلب"""

    class Meta:
        model = OrderItem
        fields = [
            'product', 'variant', 'quantity', 'unit_price'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select select2'}),
            'variant': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

        # تقييد الاختيار للمنتجات النشطة
        self.fields['product'].queryset = Product.objects.filter(is_active=True, status='published')

        # إذا تم تحديد منتج بالفعل، قم بتقييد المتغيرات له
        if self.instance.pk and self.instance.product:
            self.fields['variant'].queryset = ProductVariant.objects.filter(product=self.instance.product)
        else:
            self.fields['variant'].queryset = ProductVariant.objects.none()

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('معلومات المنتج'),
                'product',
                'variant',
            ),
            Fieldset(
                _('الكمية والسعر'),
                Row(
                    Column('quantity', css_class='col-md-6'),
                    Column('unit_price', css_class='col-md-6'),
                ),
                HTML('<div class="form-text text-muted">%s: <span id="total-price">0.00</span></div>' % _(
                    'السعر الإجمالي')),
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:order_detail" pk=order.pk %}" class="btn btn-secondary">%s</a>' % _(
                    'إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        product = cleaned_data.get('product')
        variant = cleaned_data.get('variant')
        quantity = cleaned_data.get('quantity')

        # التحقق من توافق المنتج والمتغير
        if variant and variant.product != product:
            self.add_error('variant', _('المتغير المحدد لا ينتمي للمنتج المحدد'))

        # التحقق من الكمية
        if quantity is not None and quantity < 1:
            self.add_error('quantity', _('يجب أن تكون الكمية أكبر من صفر'))

        return cleaned_data

    def save(self, commit=True):
        item = super().save(commit=False)

        # تعيين الطلب إذا كان جديدًا
        if not item.pk and self.order:
            item.order = self.order

        # تحديث المعلومات من المنتج
        product = item.product
        variant = item.variant

        item.product_name = product.name
        item.product_id = str(product.id)

        if variant:
            item.variant_name = variant.name
            item.variant_id = str(variant.id)

        # حساب السعر الإجمالي
        item.total_price = item.unit_price * item.quantity

        if commit:
            item.save()

        # تحديث المجموع الكلي للطلب
        if self.order:
            self.order.total_price = sum(i.total_price for i in self.order.items.all())
            self.order.grand_total = (
                    self.order.total_price +
                    self.order.shipping_cost +
                    self.order.tax_amount -
                    self.order.discount_amount
            )
            self.order.save(update_fields=['total_price', 'grand_total'])

        return item


class OrderStatusUpdateForm(forms.Form):
    """نموذج تحديث حالة الطلب"""
    status = forms.ChoiceField(
        label=_('حالة الطلب'),
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    payment_status = forms.ChoiceField(
        label=_('حالة الدفع'),
        choices=Order.PAYMENT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    notify_customer = forms.BooleanField(
        label=_('إخطار العميل'),
        required=False,
        initial=True
    )

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

        # تعيين القيم الأولية من الطلب
        if self.order:
            self.fields['status'].initial = self.order.status
            self.fields['payment_status'].initial = self.order.payment_status

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('تحديث حالة الطلب'),
                'status',
                'payment_status',
                'notes',
                'notify_customer',
            ),
            FormActions(
                Submit('submit', _('تحديث'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:order_detail" pk=order.pk %}" class="btn btn-secondary">%s</a>' % _(
                    'إلغاء'))
            )
        )