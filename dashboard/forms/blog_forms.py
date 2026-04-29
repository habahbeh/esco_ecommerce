from django import forms
from django.utils.translation import gettext_lazy as _, get_language
from blog.models import BlogPost, BlogCategory, BlogTag


class BilingualModelChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, en_field='name_en', ar_field='name', **kwargs):
        self._en_field = en_field
        self._ar_field = ar_field
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        lang = get_language() or 'ar'
        en_val = getattr(obj, self._en_field, '') if self._en_field else ''
        ar_val = getattr(obj, self._ar_field, str(obj))
        if lang == 'en' and en_val:
            return en_val
        return ar_val


class BilingualModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, *args, en_field='name_en', ar_field='name', **kwargs):
        self._en_field = en_field
        self._ar_field = ar_field
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        lang = get_language() or 'ar'
        en_val = getattr(obj, self._en_field, '') if self._en_field else ''
        ar_val = getattr(obj, self._ar_field, str(obj))
        if lang == 'en' and en_val:
            return en_val
        return ar_val


class BlogPostForm(forms.ModelForm):
    category = BilingualModelChoiceField(
        queryset=BlogCategory.objects.filter(is_active=True),
        required=False,
        empty_label=_("اختر التصنيف"),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    tags = BilingualModelMultipleChoiceField(
        queryset=BlogTag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
    )
    related_products = BilingualModelMultipleChoiceField(
        queryset=None,
        required=False,
        en_field='name_en', ar_field='name',
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
    )
    related_categories = BilingualModelMultipleChoiceField(
        queryset=None,
        required=False,
        en_field='name_en', ar_field='name',
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
    )

    class Meta:
        model = BlogPost
        fields = [
            'title', 'title_en', 'slug', 'category', 'tags', 'author',
            'excerpt', 'excerpt_en', 'content', 'content_en',
            'featured_image', 'featured_image_alt', 'featured_image_alt_en',
            'card_icon', 'card_icon_color',
            'status', 'is_featured', 'allow_comments', 'published_at',
            'meta_title', 'meta_description', 'meta_keywords', 'canonical_url',
            'related_products', 'related_categories',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'title_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'author': forms.Select(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'excerpt_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'dir': 'ltr'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'content_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'dir': 'ltr'}),
            'featured_image': forms.FileInput(attrs={'class': 'form-control'}),
            'featured_image_alt': forms.TextInput(attrs={'class': 'form-control'}),
            'featured_image_alt_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'published_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control'}),
            'canonical_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'card_icon': forms.HiddenInput(),
            'card_icon_color': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from products.models import Product, Category
        self.fields['related_products'].queryset = Product.objects.all()
        self.fields['related_categories'].queryset = Category.objects.all()
        self.fields['author'].empty_label = _("اختر الكاتب")


class BlogCategoryForm(forms.ModelForm):
    class Meta:
        model = BlogCategory
        fields = [
            'name', 'name_en', 'slug', 'description', 'description_en',
            'icon', 'sort_order', 'is_active', 'meta_title', 'meta_description',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'dir': 'ltr'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'fa-tools'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class BlogTagForm(forms.ModelForm):
    class Meta:
        model = BlogTag
        fields = ['name', 'name_en', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
        }
