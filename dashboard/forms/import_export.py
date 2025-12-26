# dashboard/forms/import_export.py
from django import forms
from django.utils.translation import gettext_lazy as _
from products.models import Category, Brand


class ProductImportForm(forms.Form):
    """نموذج استيراد المنتجات المحسن مع دعم المتغيرات"""

    IMPORT_MODE_CHOICES = [
        ('full', _('استيراد كامل (منتجات + متغيرات)')),
        ('products_only', _('منتجات فقط (بدون متغيرات)')),
        ('variants_only', _('متغيرات فقط (لمنتجات موجودة)')),
        ('update', _('تحديث فقط (لا يتم إنشاء جديد)')),
    ]

    import_mode = forms.ChoiceField(
        label=_("نوع الاستيراد"),
        choices=IMPORT_MODE_CHOICES,
        initial='full',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        help_text=_("اختر نوع الاستيراد المناسب لملفك")
    )

    file = forms.FileField(
        label=_("ملف الاستيراد"),
        help_text=_("يدعم ملفات Excel (.xlsx, .xls) و CSV (.csv). الحد الأقصى 10 ميجابايت."),
        widget=forms.FileInput(attrs={
            'class': 'form-control d-none',
            'accept': '.csv,.xlsx,.xls',
            'id': 'import-file-input'
        })
    )

    category = forms.ModelChoiceField(
        label=_("الفئة الافتراضية"),
        queryset=Category.objects.filter(is_active=True),
        required=False,
        help_text=_("تُستخدم للمنتجات التي لا تحتوي على فئة في الملف"),
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    brand = forms.ModelChoiceField(
        label=_("العلامة التجارية الافتراضية"),
        queryset=Brand.objects.filter(is_active=True),
        required=False,
        help_text=_("تُستخدم للمنتجات التي لا تحتوي على علامة تجارية في الملف"),
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    filter_by_category = forms.ModelChoiceField(
        label=_("استيراد لفئة محددة"),
        queryset=Category.objects.filter(is_active=True),
        required=False,
        help_text=_("تعيين جميع المنتجات المستوردة لهذه الفئة (يتجاهل الفئة في الملف)"),
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    filter_by_brand = forms.ModelChoiceField(
        label=_("استيراد لعلامة تجارية محددة"),
        queryset=Brand.objects.filter(is_active=True),
        required=False,
        help_text=_("تعيين جميع المنتجات المستوردة لهذه العلامة التجارية (يتجاهل العلامة في الملف)"),
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    update_existing = forms.BooleanField(
        label=_("تحديث المنتجات الموجودة"),
        required=False,
        initial=True,
        help_text=_("تحديث المنتجات الموجودة إذا تطابق الـ SKU أو الاسم"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    skip_errors = forms.BooleanField(
        label=_("تخطي الصفوف الخاطئة"),
        required=False,
        initial=True,
        help_text=_("الاستمرار في الاستيراد حتى مع وجود أخطاء في بعض الصفوف"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    create_categories = forms.BooleanField(
        label=_("إنشاء فئات جديدة تلقائياً"),
        required=False,
        initial=True,
        help_text=_("إنشاء فئات جديدة إذا لم تكن موجودة"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    create_brands = forms.BooleanField(
        label=_("إنشاء علامات تجارية جديدة تلقائياً"),
        required=False,
        initial=True,
        help_text=_("إنشاء علامات تجارية جديدة إذا لم تكن موجودة"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # التحقق من حجم الملف (10 ميجابايت كحد أقصى)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(_("حجم الملف يتجاوز الحد الأقصى (10 ميجابايت)"))

            # التحقق من امتداد الملف
            allowed_extensions = ['.csv', '.xlsx', '.xls']
            file_ext = '.' + file.name.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                raise forms.ValidationError(
                    _("صيغة الملف غير مدعومة. الصيغ المدعومة: CSV, Excel (.xlsx, .xls)")
                )

        return file
