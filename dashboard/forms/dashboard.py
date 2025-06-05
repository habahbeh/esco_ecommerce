# dashboard/forms/dashboard.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, HTML, Row, Column
from crispy_forms.bootstrap import FormActions, TabHolder, Tab

import json
from decimal import Decimal
from datetime import datetime

from dashboard.models import DashboardNotification, DashboardWidget, DashboardUserSettings

User = get_user_model()


class DashboardLoginForm(AuthenticationForm):
    """نموذج تسجيل الدخول المخصص للوحة التحكم"""
    username = forms.CharField(
        label=_('اسم المستخدم أو البريد الإلكتروني'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم المستخدم أو البريد الإلكتروني')})
    )
    password = forms.CharField(
        label=_('كلمة المرور'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('كلمة المرور')})
    )
    remember_me = forms.BooleanField(
        label=_('تذكرني'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'login-form'
        self.helper.layout = Layout(
            Fieldset(
                _('تسجيل الدخول إلى لوحة التحكم'),
                'username',
                'password',
                'remember_me'
            ),
            FormActions(
                Submit('submit', _('تسجيل الدخول'), css_class='btn btn-primary btn-block'),
                HTML('<a href="{% url "accounts:password_reset" %}" class="btn btn-link btn-block">%s</a>' % _(
                    'نسيت كلمة المرور؟'))
            )
        )

    def confirm_login_allowed(self, user):
        """التحقق من صلاحية المستخدم للوصول إلى لوحة التحكم"""
        super().confirm_login_allowed(user)
        if not user.is_staff and not user.is_superuser and not hasattr(user, 'can_access_dashboard'):
            raise ValidationError(
                _("ليس لديك صلاحية الوصول إلى لوحة التحكم."),
                code='no_dashboard_access',
            )


class DashboardWidgetForm(forms.ModelForm):
    """نموذج إنشاء وتعديل ودجات لوحة التحكم"""

    class Meta:
        model = DashboardWidget
        fields = [
            'name', 'title', 'description', 'widget_type',
            'row', 'column', 'width', 'height', 'is_active',
            'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'widget_type': forms.Select(attrs={'class': 'form-select'}),
            'row': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'column': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '12'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'min': '100'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    config = forms.CharField(
        label=_('إعدادات الودجة'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 10}),
        required=False,
        help_text=_('أدخل إعدادات الودجة بتنسيق JSON')
    )

    required_permissions = forms.CharField(
        label=_('الصلاحيات المطلوبة'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        help_text=_('أدخل الصلاحيات المطلوبة مفصولة بسطر جديد')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعبئة حقول JSON
        if self.instance.pk:
            if self.instance.config:
                self.fields['config'].initial = json.dumps(
                    self.instance.config,
                    indent=4,
                    ensure_ascii=False
                )

            if self.instance.required_permissions:
                self.fields['required_permissions'].initial = '\n'.join(self.instance.required_permissions)

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('المعلومات الأساسية'),
                    'name',
                    'title',
                    'description',
                    'widget_type',
                    ),

                Tab(_('التخطيط'),
                    Row(
                        Column('row', css_class='col-md-6'),
                        Column('column', css_class='col-md-6'),
                    ),
                    Row(
                        Column('width', css_class='col-md-6'),
                        Column('height', css_class='col-md-6'),
                    ),
                    'sort_order',
                    ),

                Tab(_('الإعدادات'),
                    'config',
                    'required_permissions',
                    'is_active',
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:widget_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean_config(self):
        config = self.cleaned_data.get('config')
        if not config:
            return {}

        try:
            return json.loads(config)
        except json.JSONDecodeError:
            raise ValidationError(_('تنسيق JSON غير صالح للإعدادات'))

    def clean_required_permissions(self):
        permissions = self.cleaned_data.get('required_permissions')
        if not permissions:
            return []

        return [perm.strip() for perm in permissions.split('\n') if perm.strip()]


class DashboardUserSettingsForm(forms.ModelForm):
    """نموذج إعدادات المستخدم للوحة التحكم"""

    class Meta:
        model = DashboardUserSettings
        fields = [
            'theme', 'language', 'default_view', 'items_per_page',
            'email_notifications', 'browser_notifications', 'notification_sound'
        ]
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'default_view': forms.TextInput(attrs={'class': 'form-control'}),
            'items_per_page': forms.NumberInput(attrs={'class': 'form-control', 'min': '10', 'max': '100'}),
        }

    widgets_layout = forms.CharField(
        label=_('تخطيط الودجات'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 10}),
        required=False,
        help_text=_('تخطيط ودجات لوحة التحكم بتنسيق JSON')
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تعبئة حقل تخطيط الودجات
        if self.instance.pk and self.instance.widgets_layout:
            self.fields['widgets_layout'].initial = json.dumps(
                self.instance.widgets_layout,
                indent=4,
                ensure_ascii=False
            )

        # إضافة حقول لإعدادات التنبيهات المحددة
        notification_types = {
            'order_updates': _('تحديثات الطلبات'),
            'product_updates': _('تحديثات المنتجات'),
            'user_actions': _('إجراءات المستخدمين'),
            'system_alerts': _('تنبيهات النظام'),
        }

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('التفضيلات العامة'),
                    Row(
                        Column('theme', css_class='col-md-6'),
                        Column('language', css_class='col-md-6'),
                    ),
                    Row(
                        Column('default_view', css_class='col-md-6'),
                        Column('items_per_page', css_class='col-md-6'),
                    ),
                    ),

                Tab(_('الإشعارات'),
                    'email_notifications',
                    'browser_notifications',
                    'notification_sound',
                    ),

                Tab(_('تخطيط الودجات'),
                    'widgets_layout',
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:index" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean_widgets_layout(self):
        layout = self.cleaned_data.get('widgets_layout')
        if not layout:
            return {}

        try:
            return json.loads(layout)
        except json.JSONDecodeError:
            raise ValidationError(_('تنسيق JSON غير صالح لتخطيط الودجات'))

    def save(self, commit=True):
        settings = super().save(commit=False)

        # تعيين المستخدم إذا كان جديدًا
        if not settings.pk and self.user:
            settings.user = self.user

        if commit:
            settings.save()

        return settings