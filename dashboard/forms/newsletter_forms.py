from django import forms
from core.models import Newsletter

class NewsletterForm(forms.ModelForm):
    """نموذج إضافة وتعديل اشتراكات النشرة البريدية"""
    class Meta:
        model = Newsletter
        fields = ['email', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr', 'required': 'required'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }