# core/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Row, Column
from crispy_forms.bootstrap import FormActions, TabHolder, Tab

from core.models import SiteSettings

class SiteSettingsForm(forms.ModelForm):
    """نموذج إعدادات الموقع العامة"""

    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_description', 'logo', 'favicon',
            'email', 'phone', 'address', 'facebook', 'twitter',
            'instagram', 'linkedin', 'primary_color',
            'enable_dark_mode', 'default_dark_mode'
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

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('معلومات الموقع'),
                    'site_name',
                    'site_description',
                    Row(
                        Column(
                            HTML('<div class="img-preview mb-3" id="logo-preview"></div>'),
                            'logo',
                            css_class='col-md-6'
                        ),
                        Column(
                            HTML('<div class="img-preview mb-3" id="favicon-preview"></div>'),
                            'favicon',
                            css_class='col-md-6'
                        ),
                    ),
                    ),

                Tab(_('معلومات الاتصال'),
                    'email',
                    'phone',
                    'address',
                    ),

                Tab(_('مواقع التواصل'),
                    'facebook',
                    'twitter',
                    'instagram',
                    'linkedin',
                    ),

                Tab(_('المظهر'),
                    'primary_color',
                    Row(
                        Column('enable_dark_mode', css_class='col-md-6'),
                        Column('default_dark_mode', css_class='col-md-6'),
                    ),
                    HTML(
                        '<div class="color-preview mt-3 p-4 rounded" style="background-color: var(--bs-primary);">%s</div>' % _(
                            'معاينة اللون الرئيسي')),
                    ),
            ),

            FormActions(
                forms.Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:index" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )