"""
نماذج إدارة سلة التسوق - يحتوي على نماذج متعلقة بسلة التسوق وعناصرها
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Div, HTML, Row, Column
from crispy_forms.bootstrap import FormActions

from cart.models import Cart, CartItem
from products.models import Product, ProductVariant


class CartUpdateForm(forms.ModelForm):
    """نموذج تحديث سلة التسوق"""

    class Meta:
        model = Cart
        fields = ['notes', 'coupon_code']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'coupon_code': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('تحديث سلة التسوق'),
                'notes',
                Row(
                    Column('coupon_code', css_class='col-md-8'),
                    Column(
                        HTML('<button type="submit" name="apply_coupon" class="btn btn-secondary mt-4">%s</button>' % _(
                            'تطبيق الكوبون')),
                        css_class='col-md-4'
                    ),
                ),
            ),
            FormActions(
                Submit('update_cart', _('تحديث السلة'), css_class='btn btn-primary'),
                HTML('<a href="{% url "cart:clear" %}" class="btn btn-danger ms-2">%s</a>' % _('تفريغ السلة')),
                HTML('<a href="{% url "products:list" %}" class="btn btn-secondary ms-2">%s</a>' % _('متابعة التسوق')),
                HTML('<a href="{% url "checkout:index" %}" class="btn btn-success ms-2">%s</a>' % _('إتمام الطلب'))
            )
        )


class CartItemForm(forms.ModelForm):
    """نموذج إضافة أو تعديل عنصر في سلة التسوق"""

    class Meta:
        model = CartItem
        fields = ['product', 'variant', 'quantity', 'notes']
        widgets = {
            'product': forms.HiddenInput(),
            'variant': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '100'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart', None)
        self.product_instance = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        # إذا تم تمرير منتج، يتم تعيينه وجلب متغيراته
        if self.product_instance:
            self.fields['product'].initial = self.product_instance.id
            self.fields['variant'].queryset = ProductVariant.objects.filter(
                product=self.product_instance, is_active=True
            )

            # إذا كان هناك متغير افتراضي، يتم اختياره تلقائيًا
            default_variant = ProductVariant.objects.filter(
                product=self.product_instance, is_default=True, is_active=True
            ).first()
            if default_variant:
                self.fields['variant'].initial = default_variant.id
        else:
            self.fields['variant'].queryset = ProductVariant.objects.none()

        # تحقق مما إذا كان المنتج يحتوي على متغيرات أم لا
        if self.product_instance and not self.product_instance.has_variants:
            self.fields['variant'].widget = forms.HiddenInput()
            self.fields['variant'].required = False

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'add-to-cart-form'

        self.helper.layout = Layout(
            'product',
            Fieldset(
                '',
                Div(
                    'variant',
                    css_class='variant-selection',
                    # يتم إخفاؤه إذا لم يكن للمنتج متغيرات
                    style='display: none;' if self.product_instance and not self.product_instance.has_variants else ''
                ),
                Row(
                    Column('quantity', css_class='col-md-6'),
                ),
                'notes',
            ),
            FormActions(
                Submit('add_to_cart', _('إضافة إلى السلة'), css_class='btn btn-primary'),
                HTML('<a href="javascript:history.back()" class="btn btn-secondary ms-2">%s</a>' % _('رجوع'))
            )
        )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 1:
            raise forms.ValidationError(_('يجب أن تكون الكمية أكبر من صفر'))
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product') or self.product_instance
        variant = cleaned_data.get('variant')
        quantity = cleaned_data.get('quantity', 1)

        if variant and variant.product != product:
            raise forms.ValidationError(_('المتغير المحدد غير متوافق مع المنتج'))

        # التحقق من توفر المخزون
        if variant:
            stock = variant.stock_quantity
            if stock < quantity:
                self.add_error('quantity', _('الكمية المطلوبة غير متوفرة. المتاح حالياً: %d') % stock)
        elif product:
            stock = product.stock_quantity
            if stock < quantity:
                self.add_error('quantity', _('الكمية المطلوبة غير متوفرة. المتاح حالياً: %d') % stock)

        return cleaned_data

    def save(self, commit=True):
        item = super().save(commit=False)

        # تعيين سلة التسوق
        if self.cart and not item.cart_id:
            item.cart = self.cart

        # تعيين المنتج إذا لم يتم تعيينه
        if not item.product and self.product_instance:
            item.product = self.product_instance

        # حساب السعر بناءً على المنتج والمتغير
        if item.variant:
            item.price = item.variant.base_price
        else:
            item.price = item.product.base_price

        # حساب المجموع
        item.total = item.price * item.quantity

        if commit:
            item.save()

        return item


class ApplyCouponForm(forms.Form):
    """نموذج تطبيق كوبون الخصم"""
    code = forms.CharField(
        label=_('كود الخصم'),
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Fieldset(
                _('تطبيق كود خصم'),
                Row(
                    Column('code', css_class='col-md-8'),
                    Column(
                        HTML('<button type="submit" class="btn btn-primary mt-4">%s</button>' % _('تطبيق')),
                        css_class='col-md-4'
                    ),
                ),
            )
        )