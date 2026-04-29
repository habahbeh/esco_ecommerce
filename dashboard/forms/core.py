# dashboard/forms/core.py
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, HTML, Row, Column

from crispy_forms.bootstrap import FormActions, TabHolder, Tab

import json
from decimal import Decimal
from datetime import datetime

from core.models import SiteSettings


MAX_CATALOG_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_PROFILE_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_CATALOG_MIME = {'application/pdf'}
PDF_MAGIC = b'%PDF-'


def _validate_pdf(uploaded_file, max_size=MAX_CATALOG_SIZE, size_label='25'):
    if uploaded_file is None:
        return uploaded_file
    if uploaded_file.size > max_size:
        raise forms.ValidationError(
            _("حجم الملف يتجاوز الحد المسموح به (%s ميجابايت).") % size_label
        )
    name = (getattr(uploaded_file, 'name', '') or '').lower()
    if not name.endswith('.pdf'):
        raise forms.ValidationError(_("يجب أن يكون الملف بصيغة PDF فقط."))
    content_type = getattr(uploaded_file, 'content_type', '') or ''
    if content_type and content_type not in ALLOWED_CATALOG_MIME:
        raise forms.ValidationError(_("نوع الملف غير مدعوم. الرجاء رفع ملف PDF صالح."))
    try:
        pos = uploaded_file.tell()
        head = uploaded_file.read(5)
        uploaded_file.seek(pos)
    except Exception:
        head = b''
    if not head.startswith(PDF_MAGIC):
        raise forms.ValidationError(_("الملف لا يبدو ملف PDF صالحًا."))
    return uploaded_file


def _validate_catalog_pdf(uploaded_file):
    return _validate_pdf(uploaded_file, MAX_CATALOG_SIZE, '25')




class SiteSettingsForm(forms.ModelForm):
    """نموذج إعدادات الموقع"""
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_description', 'logo', 'favicon',
            'catalog_ar', 'catalog_en',
            'company_profile_ar', 'company_profile_en',
            'email', 'phone', 'address',
            'facebook', 'twitter', 'instagram', 'linkedin','whatsapp',
            'primary_color', 'enable_dark_mode', 'default_dark_mode',
            'show_announcement_banner', 'announcement_bg_color',
            'announcement_icon_1', 'announcement_text_1_ar', 'announcement_text_1_en',
            'announcement_icon_2', 'announcement_text_2_ar', 'announcement_text_2_en',
            'announcement_icon_3', 'announcement_text_3_ar', 'announcement_text_3_en',
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'site_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'whatsapp': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'primary_color': forms.Select(attrs={'class': 'form-select color-picker'}),
            'announcement_bg_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'width:80px;height:38px;padding:2px;'}),
            'announcement_icon_1': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'fas fa-truck-fast'}),
            'announcement_text_1_ar': forms.TextInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
            'announcement_text_1_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'announcement_icon_2': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'fas fa-shield-check'}),
            'announcement_text_2_ar': forms.TextInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
            'announcement_text_2_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'announcement_icon_3': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'fas fa-rotate-left'}),
            'announcement_text_3_ar': forms.TextInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
            'announcement_text_3_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
        }

    def clean_catalog_ar(self):
        return _validate_catalog_pdf(self.cleaned_data.get('catalog_ar'))

    def clean_catalog_en(self):
        return _validate_catalog_pdf(self.cleaned_data.get('catalog_en'))

    def clean_company_profile_ar(self):
        return _validate_pdf(self.cleaned_data.get('company_profile_ar'), MAX_PROFILE_SIZE, '100')

    def clean_company_profile_en(self):
        return _validate_pdf(self.cleaned_data.get('company_profile_en'), MAX_PROFILE_SIZE, '100')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            Fieldset(
                _('معلومات الموقع الأساسية'),
                'site_name',
                'site_description',
                Row(
                    Column('logo', css_class='col-md-6'),
                    Column('favicon', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('معلومات الاتصال'),
                'email',
                'phone',
                'address',
            ),
            Fieldset(
                _('وسائل التواصل الاجتماعي'),
                'facebook',
                'twitter',
                'instagram',
                'linkedin',
                'whatsapp',
            ),
            Fieldset(
                _('إعدادات المظهر'),
                'primary_color',
                'enable_dark_mode',
                'default_dark_mode',
            ),
            FormActions(
                Submit('submit', _('حفظ التغييرات'), css_class='btn btn-primary'),
            )
        )