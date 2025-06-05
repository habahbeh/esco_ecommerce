# cart/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, HTML, Row, Column
from crispy_forms.bootstrap import FormActions

from cart.models import Cart, CartItem


# في الوقت الحالي، لا توجد نماذج محددة لسلة التسوق في الملف الأصلي
# يمكن إضافة نماذج جديدة عند الحاجة

class CartUpdateForm(forms.Form):
    """نموذج تحديث كميات عناصر سلة التسوق"""

    quantity = forms.IntegerField(
        label=_('الكمية'),
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )

    item_id = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'update-cart-form'
        self.helper.layout = Layout(
            'item_id',
            Row(
                Column('quantity', css_class='col-md-6'),
                Column(
                    FormActions(
                        Submit('update', _('تحديث'), css_class='btn btn-primary'),
                    ),
                    css_class='col-md-6 d-flex align-items-end'
                ),
            )
        )