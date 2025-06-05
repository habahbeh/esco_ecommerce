# accounts/forms.py
"""
نماذج المستخدمين والملفات الشخصية
User and Profile forms
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from .models import User, UserProfile, UserAddress, Role

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    نموذج التسجيل المخصص
    Custom User Registration Form
    """
    email = forms.EmailField(
        label=_("البريد الإلكتروني"),
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل البريد الإلكتروني')
        })
    )

    first_name = forms.CharField(
        label=_("الاسم الأول"),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('الاسم الأول')
        })
    )

    last_name = forms.CharField(
        label=_("اسم العائلة"),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('اسم العائلة')
        })
    )

    phone_number = forms.CharField(
        label=_("رقم الهاتف"),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('رقم الهاتف (اختياري)')
        })
    )

    accept_terms = forms.BooleanField(
        label=_("أوافق على الشروط والأحكام"),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    accept_marketing = forms.BooleanField(
        label=_("أوافق على تلقي رسائل تسويقية"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'password1', 'password2'
        )
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المستخدم')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تخصيص حقول كلمة المرور
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('كلمة المرور')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('تأكيد كلمة المرور')
        })

    def clean_email(self):
        """التحقق من عدم وجود البريد الإلكتروني مسبقاً"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('هذا البريد الإلكتروني مستخدم بالفعل'))
        return email

    def save(self, commit=True):
        """حفظ المستخدم مع البيانات الإضافية"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.accept_marketing = self.cleaned_data.get('accept_marketing', False)

        # تعيين الدور الافتراضي للمستخدم (مستخدم عادي)
        default_role, created = Role.objects.get_or_create(
            name=_("مستخدم عادي"),
            defaults={"description": _("دور المستخدمين العاديين مع صلاحيات محدودة")}
        )

        if commit:
            user.save()
            user.role = default_role
            user.save(update_fields=['role'])

            # إنشاء رمز التحقق وإعداد البريد الإلكتروني للتفعيل
            user.generate_verification_token()

        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    نموذج تسجيل الدخول المخصص
    Custom Login Form
    """
    username = forms.CharField(
        label=_("اسم المستخدم أو البريد الإلكتروني"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('اسم المستخدم أو البريد الإلكتروني')
        })
    )

    password = forms.CharField(
        label=_("كلمة المرور"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('كلمة المرور')
        })
    )

    remember_me = forms.BooleanField(
        label=_("تذكرني"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class CustomPasswordResetForm(PasswordResetForm):
    """
    نموذج طلب إعادة تعيين كلمة المرور
    Custom Password Reset Form
    """
    email = forms.EmailField(
        label=_("البريد الإلكتروني"),
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('البريد الإلكتروني')
        })
    )

    def clean_email(self):
        """التحقق من وجود البريد الإلكتروني في قاعدة البيانات"""
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            # لا نكشف وجود أو عدم وجود البريد في رسالة الخطأ للأمان
            # نترك المستخدم يتلقى رسالة نجاح لكن لن يتم إرسال أي بريد
            pass
        return email


class CustomSetPasswordForm(SetPasswordForm):
    """
    نموذج تعيين كلمة مرور جديدة
    Custom Set Password Form
    """
    new_password1 = forms.CharField(
        label=_("كلمة المرور الجديدة"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('كلمة المرور الجديدة')
        }),
        strip=False,
    )

    new_password2 = forms.CharField(
        label=_("تأكيد كلمة المرور الجديدة"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('تأكيد كلمة المرور الجديدة')
        }),
    )


class EmailVerificationForm(forms.Form):
    """
    نموذج التحقق من البريد الإلكتروني
    Email Verification Form
    """
    token = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_token(self):
        token = self.cleaned_data.get('token')
        if not self.user.verify_email(token):
            raise ValidationError(_('رمز التحقق غير صالح أو منتهي الصلاحية'))
        return token


class UserProfileForm(forms.ModelForm):
    """
    نموذج تحديث الملف الشخصي للمستخدم
    User Profile Update Form
    """

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'avatar', 'birth_date', 'gender', 'language', 'timezone'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم الأول')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم العائلة')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني')
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الهاتف')
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'language': forms.Select(attrs={
                'class': 'form-select'
            }),
            'timezone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المنطقة الزمنية')
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def clean_email(self):
        """التحقق من البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        # التحقق من عدم استخدام البريد من قبل مستخدم آخر
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('هذا البريد الإلكتروني مستخدم بالفعل'))
        return email


class ExtendedUserProfileForm(forms.ModelForm):
    """
    نموذج الملف الشخصي الموسع
    Extended User Profile Form
    """

    class Meta:
        model = UserProfile
        fields = [
            'bio', 'interests', 'profession', 'company',
            'website', 'twitter', 'facebook', 'instagram', 'linkedin'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('نبذة مختصرة عنك...')
            }),
            'interests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('اهتماماتك مفصولة بفواصل...')
            }),
            'profession': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المهنة')
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الشركة')
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('الموقع الشخصي')
            }),
            'twitter': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المستخدم في تويتر')
            }),
            'facebook': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المستخدم في فيسبوك')
            }),
            'instagram': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المستخدم في انستغرام')
            }),
            'linkedin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المستخدم في لينكد إن')
            }),
        }


class UserAddressForm(forms.ModelForm):
    """
    نموذج عنوان المستخدم
    User Address Form
    """

    class Meta:
        model = UserAddress
        exclude = ['user']
        widgets = {
            'label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('تسمية العنوان (مثل: المنزل، العمل)')
            }),
            'type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم الأول')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم العائلة')
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('سطر العنوان الأول')
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('سطر العنوان الثاني (اختياري)')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المدينة')
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الولاية/المنطقة')
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الرمز البريدي')
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الدولة')
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الهاتف')
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_billing_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_shipping_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        # التحقق من وجود عنوان افتراضي واحد فقط
        user = cleaned_data.get('user')  # سيتم تعيينه في view
        is_default = cleaned_data.get('is_default')
        is_billing_default = cleaned_data.get('is_billing_default')
        is_shipping_default = cleaned_data.get('is_shipping_default')

        if user:
            # فحص العنوان الافتراضي
            if is_default:
                existing = UserAddress.objects.filter(
                    user=user,
                    is_default=True
                ).exclude(pk=self.instance.pk if self.instance else None)

                if existing.exists():
                    raise ValidationError({
                        'is_default': _('يوجد عنوان افتراضي بالفعل')
                    })

        return cleaned_data


class PasswordChangeForm(forms.Form):
    """
    نموذج تغيير كلمة المرور
    Password Change Form
    """
    old_password = forms.CharField(
        label=_("كلمة المرور الحالية"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('كلمة المرور الحالية')
        })
    )

    new_password1 = forms.CharField(
        label=_("كلمة المرور الجديدة"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('كلمة المرور الجديدة')
        })
    )

    new_password2 = forms.CharField(
        label=_("تأكيد كلمة المرور الجديدة"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('تأكيد كلمة المرور الجديدة')
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """التحقق من كلمة المرور الحالية"""
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError(_('كلمة المرور الحالية غير صحيحة'))
        return old_password

    def clean(self):
        """التحقق من تطابق كلمات المرور الجديدة"""
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError({
                    'new_password2': _('كلمات المرور الجديدة غير متطابقة')
                })

        return cleaned_data

    def save(self):
        """حفظ كلمة المرور الجديدة"""
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user


class NotificationPreferencesForm(forms.ModelForm):
    """
    نموذج تفضيلات الإشعارات
    Notification Preferences Form
    """
    email_notifications = forms.BooleanField(
        label=_("إشعارات البريد الإلكتروني"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    sms_notifications = forms.BooleanField(
        label=_("إشعارات الرسائل النصية"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    order_updates = forms.BooleanField(
        label=_("تحديثات الطلبات"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    marketing_emails = forms.BooleanField(
        label=_("رسائل تسويقية"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['notification_preferences']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تحميل التفضيلات الحالية
        if self.instance and self.instance.notification_preferences:
            prefs = self.instance.notification_preferences
            self.fields['email_notifications'].initial = prefs.get('email_notifications', True)
            self.fields['sms_notifications'].initial = prefs.get('sms_notifications', False)
            self.fields['order_updates'].initial = prefs.get('order_updates', True)
            self.fields['marketing_emails'].initial = prefs.get('marketing_emails', False)

    def save(self, commit=True):
        """حفظ تفضيلات الإشعارات"""
        instance = super().save(commit=False)

        # تحديث تفضيلات الإشعارات
        preferences = {
            'email_notifications': self.cleaned_data.get('email_notifications', True),
            'sms_notifications': self.cleaned_data.get('sms_notifications', False),
            'order_updates': self.cleaned_data.get('order_updates', True),
            'marketing_emails': self.cleaned_data.get('marketing_emails', False),
        }

        instance.notification_preferences = preferences

        if commit:
            instance.save()

        return instance


class RoleForm(forms.ModelForm):
    """
    نموذج الأدوار في النظام
    Role Form for the system
    """
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        label=_("الصلاحيات")
    )

    class Meta:
        model = Role
        fields = ['name', 'description', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الدور')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف مختصر للدور وصلاحياته')
            }),
        }


class AdminUserManagementForm(forms.ModelForm):
    """
    نموذج إدارة المستخدمين للمشرفين
    Admin User Management Form
    """
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        label=_("الدور"),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        label=_("المجموعات"),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )

    is_active = forms.BooleanField(
        label=_("نشط"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    is_staff = forms.BooleanField(
        label=_("مشرف"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    is_superuser = forms.BooleanField(
        label=_("مدير النظام"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser', 'role', 'groups'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المستخدم')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني')
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم الأول')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم العائلة')
            }),
        }