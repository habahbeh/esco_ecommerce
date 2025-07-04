# dashboard/forms/import_export.py
from django import forms
from django.utils.translation import gettext_lazy as _
from products.models import Category


class ProductImportForm(forms.Form):
    """نموذج استيراد المنتجات من ملف Excel"""

    file = forms.FileField(
        label=_("ملف Excel"),
        help_text=_("يرجى اختيار ملف Excel (.xlsx) يحتوي على بيانات المنتجات"),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx'})
    )

    category = forms.ModelChoiceField(
        label=_("الفئة الافتراضية"),
        queryset=Category.objects.filter(is_active=True),
        required=False,
        help_text=_("سيتم تعيين هذه الفئة للمنتجات التي لا تحتوي على فئة محددة"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    update_existing = forms.BooleanField(
        label=_("تحديث المنتجات الموجودة"),
        required=False,
        initial=True,
        help_text=_("تحديث المنتجات الموجودة إذا كان الـ SKU متطابقاً"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )