# في ملف dashboard/forms/slider_forms.py
from django import forms
from core.models import SliderItem

class SliderItemForm(forms.ModelForm):
    """نموذج إضافة وتعديل عناصر السلايدر"""
    class Meta:
        model = SliderItem
        fields = [
            'title', 'subtitle', 'description', 'image',
            'primary_button_text', 'primary_button_url',
            'secondary_button_text', 'secondary_button_url',
            'order', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'primary_button_text': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_button_url': forms.TextInput(attrs={'class': 'form-control'}),
            'secondary_button_text': forms.TextInput(attrs={'class': 'form-control'}),
            'secondary_button_url': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }