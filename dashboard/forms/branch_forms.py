from django import forms
from core.models import Branch
from django.utils.translation import gettext as _


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = [
            'name', 'name_en',
            'address', 'address_en',
            'phone',
            'working_hours', 'working_hours_en',
            'is_active', 'sort_order',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'required': 'required'}),
            'address_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'dir': 'ltr'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'working_hours_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
