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






class SiteSettingsForm(forms.ModelForm):
    """نموذج إعدادات الموقع"""
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_description', 'logo', 'favicon',
            'email', 'phone', 'address',
            'facebook', 'twitter', 'instagram', 'linkedin',
            'primary_color', 'enable_dark_mode', 'default_dark_mode'
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
            'primary_color': forms.Select(attrs={'class': 'form-select color-picker'}),
        }

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