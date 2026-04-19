from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import SiteSettings


def validate_file_size_100mb(value):
    if value.size > 100 * 1024 * 1024:
        raise ValidationError(_('حجم الملف يجب أن لا يتجاوز 100 ميجابايت'))


class SiteSettingsForm(forms.ModelForm):
    """
    نموذج إعدادات الموقع
    Site settings form
    """

    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_description', 'logo', 'favicon',
            'catalog_ar', 'catalog_en',
            'company_profile_ar', 'company_profile_en',
            'email', 'phone', 'address',
            'facebook', 'twitter', 'instagram', 'linkedin',
            'primary_color', 'enable_dark_mode', 'default_dark_mode'
        ]

        widgets = {
            'site_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
            'address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'primary_color': forms.Select(attrs={
                'class': 'form-select color-select',
                'data-preview': 'true'
            }),
            'enable_dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # إضافة placeholder للحقول
        placeholders = {
            'site_name': 'اسم الموقع',
            'email': 'example@domain.com',
            'phone': '+966 XX XXX XXXX',
            'facebook': 'https://facebook.com/yourpage',
            'twitter': 'https://twitter.com/yourhandle',
            'instagram': 'https://instagram.com/yourprofile',
            'linkedin': 'https://linkedin.com/company/yourcompany',
        }

        for field_name, placeholder in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['placeholder'] = placeholder

        for field_name in ['catalog_ar', 'catalog_en', 'company_profile_ar', 'company_profile_en']:
            if field_name in self.fields:
                self.fields[field_name].validators.append(validate_file_size_100mb)