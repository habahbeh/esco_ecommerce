from django import forms
from django.utils.translation import gettext_lazy as _
from core.models import SiteSettings, SEOKeyword


class SEOSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'seo_title', 'seo_description', 'seo_keywords',
            'google_analytics_id', 'google_search_console_code',
            'og_image', 'enable_structured_data', 'enable_sitemap',
            'canonical_domain',
        ]
        widgets = {
            'seo_title': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 70,
                'placeholder': _('عنوان الموقع لمحركات البحث (60-70 حرف)')
            }),
            'seo_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'maxlength': 160,
                'placeholder': _('وصف الموقع لمحركات البحث (150-160 حرف)')
            }),
            'seo_keywords': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('كلمات مفتاحية مفصولة بفواصل')
            }),
            'google_analytics_id': forms.TextInput(attrs={
                'class': 'form-control',
                'dir': 'ltr',
                'placeholder': 'G-XXXXXXXXXX'
            }),
            'google_search_console_code': forms.TextInput(attrs={
                'class': 'form-control',
                'dir': 'ltr',
                'placeholder': _('رمز التحقق من Google')
            }),
            'canonical_domain': forms.URLInput(attrs={
                'class': 'form-control',
                'dir': 'ltr',
                'placeholder': 'https://www.example.com'
            }),
        }


class SEOKeywordForm(forms.ModelForm):
    class Meta:
        model = SEOKeyword
        fields = [
            'keyword', 'keyword_en', 'level', 'category', 'product',
            'search_volume', 'competition', 'is_competitor',
            'competitor_url', 'notes', 'is_active',
        ]
        widgets = {
            'keyword': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الكلمة المفتاحية بالعربية')}),
            'keyword_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': _('Keyword in English')}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'search_volume': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'competition': forms.Select(attrs={'class': 'form-select'}),
            'competitor_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['product'].required = False
        self.fields['keyword_en'].required = False
        self.fields['competitor_url'].required = False
        self.fields['notes'].required = False

    def clean(self):
        cleaned_data = super().clean()
        level = cleaned_data.get('level')
        if level == 'category' and not cleaned_data.get('category'):
            self.add_error('category', _('يجب اختيار فئة لهذا المستوى'))
        if level == 'product' and not cleaned_data.get('product'):
            self.add_error('product', _('يجب اختيار منتج لهذا المستوى'))
        return cleaned_data
