from django import forms
from events.models import Event, EventImage
from django.utils.translation import gettext as _

class EventForm(forms.ModelForm):
    """نموذج إضافة وتعديل الفعاليات"""
    class Meta:
        model = Event
        fields = [
            'title', 'title_en', 'slug',
            'description', 'description_en',
            'short_description', 'short_description_en',
            'start_date', 'end_date',
            'location', 'location_en',
            'banner_image', 'cover_image',
            'is_active', 'display_in', 'order',
            'registration_url', 'button_text', 'button_text_en'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'title_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': 'required'}),
            'description_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'dir': 'ltr'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'short_description_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': 'required'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': 'required'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'location_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'registration_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'button_text': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'button_text_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'display_in': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EventImageForm(forms.ModelForm):
    """نموذج إضافة صور للفعالية"""

    # تعريف حقل الصورة بشكل منفصل لجعله اختيارياً
    image = forms.ImageField(
        label=_("الصورة"),
        required=False,  # جعل الحقل اختياري
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = EventImage
        fields = ['image', 'caption', 'caption_en', 'order']
        widgets = {
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
            'caption_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }