"""
نماذج إدارة المستخدمين والأدوار - يحتوي على نماذج مرتبطة بالمصادقة وإدارة المستخدمين
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, HTML, Row, Column
from crispy_forms.bootstrap import FormActions, TabHolder, Tab

import json

from accounts.models import Role, UserProfile, UserAddress, UserActivity

User = get_user_model()


class DashboardLoginForm(AuthenticationForm):
    """نموذج تسجيل الدخول المخصص للوحة التحكم"""
    username = forms.CharField(
        label=_('اسم المستخدم أو البريد الإلكتروني'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل اسم المستخدم أو البريد الإلكتروني'),
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label=_('كلمة المرور'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل كلمة المرور'),
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        label=_('تذكرني'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    error_messages = {
        'invalid_login': _("يرجى التأكد من اسم المستخدم وكلمة المرور. لاحظ أن كلاهما حساس لحالة الأحرف."),
        'inactive': _("هذا الحساب غير نشط."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # عدم استخدام FormHelper لتجنب مشكلات الترجمة
        # مع النموذج المخصص

    def confirm_login_allowed(self, user):
        """التحقق من صلاحية المستخدم للوصول إلى لوحة التحكم"""
        super().confirm_login_allowed(user)
        if not user.is_staff and not user.is_superuser and not hasattr(user, 'can_access_dashboard'):
            raise ValidationError(
                _("ليس لديك صلاحية الوصول إلى لوحة التحكم."),
                code='no_dashboard_access',
            )

class UserForm(forms.ModelForm):
    """نموذج إنشاء وتعديل المستخدمين"""
    confirm_password = forms.CharField(
        label=_('تأكيد كلمة المرور'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    password = forms.CharField(
        label=_('كلمة المرور'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text=_('اترك هذا الحقل فارغاً إذا كنت لا تريد تغيير كلمة المرور')
    )
    is_staff = forms.BooleanField(
        label=_('الوصول للوحة التحكم'),
        required=False,
        help_text=_('يسمح للمستخدم بالوصول إلى لوحة التحكم')
    )
    is_superuser = forms.BooleanField(
        label=_('مشرف كامل الصلاحيات'),
        required=False,
        help_text=_('يمنح المستخدم جميع الصلاحيات')
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password', 'confirm_password',
            'phone_number', 'avatar', 'birth_date', 'gender', 'address', 'city', 'country',
            'postal_code', 'is_active', 'role', 'is_staff', 'is_superuser', 'is_product_reviewer',
            'accept_marketing', 'language'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.is_edit_mode = kwargs.pop('is_edit_mode', False)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'

        # جعل حقل كلمة المرور مطلوبًا عند إنشاء مستخدم جديد
        if not self.is_edit_mode:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True

        # تنظيم الحقول في تبويبات
        self.helper.layout = Layout(
            TabHolder(
                Tab(_('المعلومات الأساسية'),
                    'username', 'email', 'first_name', 'last_name',
                    'password', 'confirm_password'),
                Tab(_('معلومات الاتصال'),
                    'phone_number', 'address', 'city', 'country', 'postal_code'),
                Tab(_('المعلومات الشخصية'),
                    'avatar', 'birth_date', 'gender', 'language'),
                Tab(_('الصلاحيات'),
                    'is_active', 'role', 'is_staff', 'is_superuser', 'is_product_reviewer'),
                Tab(_('تفضيلات'),
                    'accept_marketing'),
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:user_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password:
            # التحقق من كلمة المرور وتأكيدها
            if password != confirm_password:
                self.add_error('confirm_password', _('كلمة المرور وتأكيدها غير متطابقين'))

            # التحقق من قوة كلمة المرور
            try:
                validate_password(password)
            except ValidationError as e:
                self.add_error('password', e)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # تعيين كلمة المرور إذا تم توفيرها
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
            self.save_m2m()

        return user


class RoleForm(forms.ModelForm):
    """نموذج إدارة الأدوار  """
    permissions = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label=_('الصلاحيات')
    )

    class Meta:
        model = Role
        fields = ['name', 'description', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تجميع الصلاحيات حسب التطبيق
        self.fields['permissions'].queryset = Permission.objects.all().order_by('content_type__app_label',
                                                                                'content_type__model', 'name')

        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        # تنظيم الصلاحيات في مجموعات
        content_types = ContentType.objects.all().order_by('app_label')
        permissions_layout = []

        for ct in content_types:
            ct_permissions = Permission.objects.filter(content_type=ct)
            if ct_permissions.exists():
                permission_fields = []
                for permission in ct_permissions:
                    permission_fields.append(
                        forms.BooleanField(
                            label=str(permission.name),
                            required=False,
                            widget=forms.CheckboxInput()
                        )
                    )

                permissions_layout.append(
                    Fieldset(
                        f"{ct.app_label.title()}: {ct.name.title()}",
                        *permission_fields
                    )
                )

        self.helper.layout = Layout(
            Fieldset(
                _('معلومات الدور'),
                'name',
                'description',
            ),
            Fieldset(
                _('الصلاحيات'),
                HTML('<div class="permissions-container">'),
                'permissions',
                HTML('</div>'),
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:role_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )


class UserProfileForm(forms.ModelForm):
    """نموذج الملف الشخصي للمستخدم"""

    class Meta:
        model = UserProfile
        fields = [
            'website', 'twitter', 'facebook', 'instagram', 'linkedin',
            'bio', 'interests', 'profession', 'company',
            'notification_preferences', 'privacy_settings'
        ]
        widgets = {
            'website': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'twitter': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'facebook': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'linkedin': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تحويل حقول JSON إلى حقول مخصصة
        notification_types = {
            'order_updates': _('تحديثات الطلبات'),
            'product_updates': _('تحديثات المنتجات'),
            'promotions': _('العروض والخصومات'),
            'newsletters': _('النشرات الإخبارية'),
            'system_messages': _('رسائل النظام')
        }

        self.notification_fields = {}
        notification_prefs = self.instance.notification_preferences if self.instance.pk else {}

        for key, label in notification_types.items():
            field_name = f'notification_{key}'
            self.fields[field_name] = forms.BooleanField(
                label=label,
                required=False,
                initial=notification_prefs.get(key, True)
            )
            self.notification_fields[key] = field_name

        # تنظيم الحقول
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('المعلومات الشخصية'),
                    'bio', 'profession', 'company', 'interests'),
                Tab(_('مواقع التواصل'),
                    'website', 'twitter', 'facebook', 'instagram', 'linkedin'),
                Tab(_('الإشعارات'),
                    *[field_name for field_name in self.notification_fields.values()]),
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:user_detail" pk=user.pk %}" class="btn btn-secondary">%s</a>' % _(
                    'إلغاء'))
            )
        )

    def save(self, commit=True):
        profile = super().save(commit=False)

        # حفظ تفضيلات الإشعارات
        notification_prefs = {}
        for key, field_name in self.notification_fields.items():
            notification_prefs[key] = self.cleaned_data.get(field_name, True)

        profile.notification_preferences = notification_prefs

        if commit:
            profile.save()

        return profile


class UserAddressForm(forms.ModelForm):
    """نموذج عناوين المستخدم"""

    class Meta:
        model = UserAddress
        fields = [
            'label', 'type', 'first_name', 'last_name',
            'address_line_1', 'address_line_2', 'city', 'state',
            'postal_code', 'country', 'phone_number',
            'is_default', 'is_shipping_default', 'is_billing_default'
        ]
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_shipping_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_billing_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and not self.user:
            self.user = self.instance.user

    def save(self, commit=True):
        address = super().save(commit=False)

        if self.user and not address.user_id:
            address.user = self.user

        if commit:
            address.save()

        return address