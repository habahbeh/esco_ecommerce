# dashboard/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from mptt.forms import TreeNodeChoiceField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, HTML, Row, Column
from crispy_forms.bootstrap import FormActions, TabHolder, Tab

import json
from decimal import Decimal
from datetime import datetime

from accounts.models import Role, UserProfile, UserAddress, UserActivity
from core.models import SiteSettings
from products.models import (
    Product, Category, Brand, Tag, ProductVariant, ProductImage, ProductReview,
    ProductAttribute, ProductDiscount, ProductAttributeValue
)
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from checkout.models import (
    CheckoutSession, PaymentMethod, ShippingMethod, PaymentTransaction, Coupon
)
from payment.models import Transaction, Payment, Refund
from dashboard.models import DashboardNotification, ProductReviewAssignment, DashboardWidget, DashboardUserSettings

User = get_user_model()


# ========== نماذج المصادقة والمستخدمين ==========

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
    """نموذج إدارة الأدوار"""
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
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

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
            'is_default', 'is_billing_default', 'is_shipping_default'
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
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and not self.user:
            self.user = self.instance.user

        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('معلومات العنوان'),
                Row(
                    Column('label', css_class='col-md-6'),
                    Column('type', css_class='col-md-6'),
                ),
                Row(
                    Column('first_name', css_class='col-md-6'),
                    Column('last_name', css_class='col-md-6'),
                ),
                'address_line_1',
                'address_line_2',
                Row(
                    Column('city', css_class='col-md-6'),
                    Column('state', css_class='col-md-6'),
                ),
                Row(
                    Column('postal_code', css_class='col-md-6'),
                    Column('country', css_class='col-md-6'),
                ),
                'phone_number',
            ),
            Fieldset(
                _('الإعدادات'),
                Row(
                    Column('is_default', css_class='col-md-4'),
                    Column('is_billing_default', css_class='col-md-4'),
                    Column('is_shipping_default', css_class='col-md-4'),
                ),
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML(
                    '<a href="{% url "dashboard:user_address_list" user_id=user.pk %}" class="btn btn-secondary">%s</a>' % _(
                        'إلغاء'))
            )
        )

    def save(self, commit=True):
        address = super().save(commit=False)

        if self.user and not address.user_id:
            address.user = self.user

        if commit:
            address.save()

        return address


# ========== نماذج المنتجات ==========

class ProductForm(forms.ModelForm):
    """نموذج إنشاء وتعديل المنتجات"""

    class Meta:
        model = Product
        fields = [
            'name', 'name_en', 'sku', 'barcode', 'category', 'brand',
            'short_description', 'description', 'base_price', 'compare_price', 'cost',
            'stock_quantity', 'stock_status', 'weight', 'length', 'width', 'height',
            'condition', 'status', 'is_active', 'is_featured', 'is_new', 'is_best_seller',
            'is_digital', 'requires_shipping', 'tax_rate', 'meta_title', 'meta_description',
            'meta_keywords', 'tags', 'search_keywords'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'category': TreeNodeChoiceField(queryset=Category.objects.all()),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control rich-text-editor', 'rows': 10}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'compare_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_status': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'length': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control'}),
            'search_keywords': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select select2', 'multiple': 'multiple'}),
        }

    specifications = forms.CharField(
        label=_('المواصفات الفنية'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل المواصفات الفنية بتنسيق JSON')
    )

    features = forms.CharField(
        label=_('الميزات'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل ميزات المنتج بتنسيق JSON أو قائمة مفصولة بسطور')
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تعبئة حقول JSON من النموذج
        if self.instance.pk:
            if self.instance.specifications:
                self.fields['specifications'].initial = json.dumps(self.instance.specifications, indent=4,
                                                                   ensure_ascii=False)

            if self.instance.features:
                if isinstance(self.instance.features, list):
                    self.fields['features'].initial = '\n'.join(self.instance.features)
                else:
                    self.fields['features'].initial = json.dumps(self.instance.features, indent=4, ensure_ascii=False)

        # تحسين حقول الاختيار
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['brand'].queryset = Brand.objects.filter(is_active=True)
        self.fields['tags'].queryset = Tag.objects.filter(is_active=True)

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'product-form'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('المعلومات الأساسية'),
                    Row(
                        Column('name', css_class='col-md-6'),
                        Column('name_en', css_class='col-md-6'),
                    ),
                    Row(
                        Column('sku', css_class='col-md-4'),
                        Column('barcode', css_class='col-md-4'),
                        Column('status', css_class='col-md-4'),
                    ),
                    Row(
                        Column('category', css_class='col-md-6'),
                        Column('brand', css_class='col-md-6'),
                    ),
                    'short_description',
                    'description'),

                Tab(_('التسعير والمخزون'),
                    Row(
                        Column('base_price', css_class='col-md-4'),
                        Column('compare_price', css_class='col-md-4'),
                        Column('cost', css_class='col-md-4'),
                    ),
                    Row(
                        Column('stock_quantity', css_class='col-md-6'),
                        Column('stock_status', css_class='col-md-6'),
                    ),
                    Row(
                        Column('tax_rate', css_class='col-md-6'),
                        Column('condition', css_class='col-md-6'),
                    )),

                Tab(_('المواصفات والميزات'),
                    'specifications',
                    'features',
                    Row(
                        Column('weight', css_class='col-md-3'),
                        Column('length', css_class='col-md-3'),
                        Column('width', css_class='col-md-3'),
                        Column('height', css_class='col-md-3'),
                    )),

                Tab(_('الإعدادات'),
                    Row(
                        Column(
                            'is_active',
                            'is_featured',
                            'is_new',
                            'is_best_seller',
                            css_class='col-md-6'
                        ),
                        Column(
                            'is_digital',
                            'requires_shipping',
                            css_class='col-md-6'
                        ),
                    )),

                Tab(_('SEO والوسوم'),
                    'meta_title',
                    'meta_description',
                    'meta_keywords',
                    'search_keywords',
                    'tags'),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:product_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean_specifications(self):
        specs = self.cleaned_data.get('specifications')
        if not specs:
            return {}

        try:
            return json.loads(specs)
        except json.JSONDecodeError:
            raise ValidationError(_('تنسيق JSON غير صالح للمواصفات الفنية'))

    def clean_features(self):
        features = self.cleaned_data.get('features')
        if not features:
            return []

        try:
            # محاولة معالجة كـ JSON
            return json.loads(features)
        except json.JSONDecodeError:
            # معالجة كقائمة مفصولة بسطور
            return [line.strip() for line in features.split('\n') if line.strip()]

    def save(self, commit=True):
        product = super().save(commit=False)

        # تعيين المستخدم الذي أنشأ المنتج
        if not product.pk and self.user:
            product.created_by = self.user

        # تعيين حالة النشر
        if product.status == 'published' and not product.published_at:
            product.published_at = timezone.now()

        # حفظ البيانات
        if commit:
            product.save()
            self.save_m2m()  # لحفظ العلاقات مثل الوسوم

        return product


class CategoryForm(forms.ModelForm):
    """نموذج إنشاء وتعديل فئات المنتجات"""

    class Meta:
        model = Category
        fields = [
            'name', 'name_en', 'slug', 'parent', 'description', 'description_en',
            'image', 'icon', 'color', 'banner_image', 'is_active', 'is_featured',
            'show_in_menu', 'sort_order', 'meta_title', 'meta_description', 'meta_keywords'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'parent': TreeNodeChoiceField(queryset=Category.objects.all(), level_indicator=u'⟹', required=False),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'dir': 'ltr'}),
            'icon': forms.TextInput(attrs={'class': 'form-control icon-picker', 'dir': 'ltr'}),
            'color': forms.TextInput(attrs={'class': 'form-control color-picker', 'dir': 'ltr'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control'}),
        }

    content_blocks = forms.CharField(
        label=_('كتل المحتوى'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل كتل المحتوى بتنسيق JSON (اختياري)')
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تجنب اختيار الفئة نفسها كأب عند التعديل
        if self.instance.pk:
            self.fields['parent'].queryset = Category.objects.exclude(
                pk=self.instance.pk
            ).exclude(
                pk__in=[child.pk for child in self.instance.get_all_children()]
            )

            # تعبئة حقل كتل المحتوى
            if self.instance.content_blocks:
                self.fields['content_blocks'].initial = json.dumps(
                    self.instance.content_blocks,
                    indent=4,
                    ensure_ascii=False
                )

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('المعلومات الأساسية'),
                    Row(
                        Column('name', css_class='col-md-6'),
                        Column('name_en', css_class='col-md-6'),
                    ),
                    Row(
                        Column('slug', css_class='col-md-6'),
                        Column('parent', css_class='col-md-6'),
                    ),
                    'description',
                    'description_en'),

                Tab(_('العرض والمظهر'),
                    Row(
                        Column(
                            HTML('<div class="img-preview mb-3" id="image-preview"></div>'),
                            'image',
                            css_class='col-md-6'
                        ),
                        Column(
                            HTML('<div class="img-preview mb-3" id="banner-preview"></div>'),
                            'banner_image',
                            css_class='col-md-6'
                        ),
                    ),
                    Row(
                        Column('icon', css_class='col-md-6'),
                        Column('color', css_class='col-md-6'),
                    ),
                    Row(
                        Column('sort_order', css_class='col-md-4'),
                        Column('is_active', css_class='col-md-4'),
                        Column('is_featured', css_class='col-md-4'),
                    ),
                    'show_in_menu',
                    'content_blocks'),

                Tab(_('SEO'),
                    'meta_title',
                    'meta_description',
                    'meta_keywords'),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:category_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean_content_blocks(self):
        content = self.cleaned_data.get('content_blocks')
        if not content:
            return {}

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValidationError(_('تنسيق JSON غير صالح لكتل المحتوى'))

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من أن الفئة لا تكون أب لنفسها
        parent = cleaned_data.get('parent')
        if self.instance.pk and parent and parent.pk == self.instance.pk:
            self.add_error('parent', _('لا يمكن أن تكون الفئة أب لنفسها'))

        return cleaned_data

    def save(self, commit=True):
        category = super().save(commit=False)

        # تعيين المستخدم الذي أنشأ الفئة
        if not category.pk and self.user:
            category.created_by = self.user

        if commit:
            category.save()

        return category


class ProductVariantForm(forms.ModelForm):
    """نموذج إنشاء وتعديل متغيرات المنتجات"""

    class Meta:
        model = ProductVariant
        fields = [
            'name', 'sku', 'base_price', 'stock_quantity',
            'weight', 'is_active', 'is_default', 'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    attributes = forms.CharField(
        label=_('خصائص المتغير'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل خصائص المتغير بتنسيق JSON (مثل: {"اللون": "أحمر", "الحجم": "كبير"})')
    )

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        # تعبئة حقل الخصائص
        if self.instance.pk and self.instance.attributes:
            self.fields['attributes'].initial = json.dumps(
                self.instance.attributes,
                indent=4,
                ensure_ascii=False
            )

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('معلومات المتغير'),
                'name',
                'sku',
                'attributes',
            ),
            Fieldset(
                _('التسعير والمخزون'),
                Row(
                    Column('base_price', css_class='col-md-6'),
                    Column('stock_quantity', css_class='col-md-6'),
                ),
                'weight',
            ),
            Fieldset(
                _('الإعدادات'),
                Row(
                    Column('is_active', css_class='col-md-4'),
                    Column('is_default', css_class='col-md-4'),
                    Column('sort_order', css_class='col-md-4'),
                ),
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML(
                    '<a href="{% url "dashboard:product_detail" pk=product.pk %}" class="btn btn-secondary">%s</a>' % _(
                        'إلغاء'))
            )
        )

    def clean_attributes(self):
        attrs = self.cleaned_data.get('attributes')
        if not attrs:
            return {}

        try:
            return json.loads(attrs)
        except json.JSONDecodeError:
            raise ValidationError(_('تنسيق JSON غير صالح للخصائص'))

    def save(self, commit=True):
        variant = super().save(commit=False)

        # تعيين المنتج إذا كان جديدًا
        if not variant.pk and self.product:
            variant.product = self.product

        if commit:
            variant.save()

        return variant


class ProductImageForm(forms.ModelForm):
    """نموذج إضافة وتعديل صور المنتجات"""

    class Meta:
        model = ProductImage
        fields = [
            'image', 'alt_text', 'caption', 'is_primary',
            'is_360', 'sort_order', 'color_code', 'variant'
        ]
        widgets = {
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'color_code': forms.TextInput(attrs={'class': 'form-control color-picker', 'dir': 'ltr'}),
            'variant': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        # تقييد الاختيار للمتغيرات المرتبطة بالمنتج فقط
        if self.product:
            self.fields['variant'].queryset = ProductVariant.objects.filter(product=self.product)

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('الصورة'),
                'image',
                HTML('<div class="img-preview my-3" id="image-preview"></div>'),
                Row(
                    Column('alt_text', css_class='col-md-6'),
                    Column('caption', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('الإعدادات'),
                Row(
                    Column('is_primary', css_class='col-md-6'),
                    Column('is_360', css_class='col-md-6'),
                ),
                Row(
                    Column('sort_order', css_class='col-md-6'),
                    Column('color_code', css_class='col-md-6'),
                ),
                'variant',
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML(
                    '<a href="{% url "dashboard:product_detail" pk=product.pk %}" class="btn btn-secondary">%s</a>' % _(
                        'إلغاء'))
            )
        )

    def save(self, commit=True):
        image = super().save(commit=False)

        # تعيين المنتج إذا كان جديدًا
        if not image.pk and self.product:
            image.product = self.product

        if commit:
            image.save()

        return image


class ProductDiscountForm(forms.ModelForm):
    """نموذج إنشاء وتعديل خصومات المنتجات"""

    class Meta:
        model = ProductDiscount
        fields = [
            'name', 'description', 'code', 'discount_type', 'value',
            'max_discount_amount', 'application_type', 'category', 'products',
            'start_date', 'end_date', 'min_purchase_amount', 'min_quantity',
            'max_uses', 'max_uses_per_user', 'buy_quantity', 'get_quantity',
            'get_discount_percentage', 'is_active', 'is_stackable',
            'requires_coupon_code', 'priority'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'application_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'products': forms.SelectMultiple(attrs={'class': 'form-select select2', 'multiple': 'multiple'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'min_purchase_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_uses_per_user': forms.NumberInput(attrs={'class': 'form-control'}),
            'buy_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'get_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'get_discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تحسين حقول الاختيار
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['products'].queryset = Product.objects.filter(is_active=True, status='published')

        # إخفاء/إظهار الحقول بناءً على نوع الخصم
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'discount-form'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('المعلومات الأساسية'),
                    'name',
                    'description',
                    Row(
                        Column('code', css_class='col-md-6'),
                        Column('requires_coupon_code', css_class='col-md-6'),
                    ),
                    Row(
                        Column('discount_type', css_class='col-md-4'),
                        Column('value', css_class='col-md-4'),
                        Column('max_discount_amount', css_class='col-md-4'),
                    ),
                    Row(
                        Column('start_date', css_class='col-md-6'),
                        Column('end_date', css_class='col-md-6'),
                    ),
                    'is_active',
                    ),

                Tab(_('نطاق التطبيق'),
                    'application_type',
                    Div(
                        'category',
                        css_class='category-fields',
                    ),
                    Div(
                        'products',
                        css_class='products-fields',
                    ),
                    Row(
                        Column('min_purchase_amount', css_class='col-md-6'),
                        Column('min_quantity', css_class='col-md-6'),
                    ),
                    ),

                Tab(_('إعدادات اشتري X واحصل على Y'),
                    Div(
                        Row(
                            Column('buy_quantity', css_class='col-md-4'),
                            Column('get_quantity', css_class='col-md-4'),
                            Column('get_discount_percentage', css_class='col-md-4'),
                        ),
                        css_class='buy-x-get-y-fields',
                    ),
                    ),

                Tab(_('الحدود والإعدادات المتقدمة'),
                    Row(
                        Column('max_uses', css_class='col-md-6'),
                        Column('max_uses_per_user', css_class='col-md-6'),
                    ),
                    Row(
                        Column('priority', css_class='col-md-6'),
                        Column('is_stackable', css_class='col-md-6'),
                    ),
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:discount_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من صحة تواريخ الخصم
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date >= end_date:
            self.add_error('end_date', _('يجب أن يكون تاريخ النهاية بعد تاريخ البداية'))

        # التحقق من حقول اشتري X واحصل على Y
        discount_type = cleaned_data.get('discount_type')
        if discount_type == 'buy_x_get_y':
            buy_quantity = cleaned_data.get('buy_quantity')
            get_quantity = cleaned_data.get('get_quantity')

            if not buy_quantity or buy_quantity < 1:
                self.add_error('buy_quantity', _('يجب تحديد كمية الشراء'))

            if not get_quantity or get_quantity < 1:
                self.add_error('get_quantity', _('يجب تحديد كمية الحصول'))

        # التحقق من نوع التطبيق
        application_type = cleaned_data.get('application_type')
        if application_type == 'category' and not cleaned_data.get('category'):
            self.add_error('category', _('يجب تحديد الفئة عند اختيار نوع التطبيق "فئة محددة"'))

        if application_type == 'specific_products' and not cleaned_data.get('products'):
            self.add_error('products', _('يجب تحديد المنتجات عند اختيار نوع التطبيق "منتجات محددة"'))

        # التحقق من الكود
        requires_code = cleaned_data.get('requires_coupon_code')
        code = cleaned_data.get('code')

        if requires_code and not code:
            self.add_error('code', _('يجب تحديد كود الخصم عند تفعيل "يتطلب كود خصم"'))

        return cleaned_data

    def save(self, commit=True):
        discount = super().save(commit=False)

        # تعيين المستخدم الذي أنشأ الخصم
        if not discount.pk and self.user:
            discount.created_by = self.user

        if commit:
            discount.save()
            self.save_m2m()  # لحفظ العلاقات مثل المنتجات

        return discount


# ========== نماذج الطلبات ==========

class OrderForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الطلبات"""

    class Meta:
        model = Order
        fields = [
            'order_number', 'user', 'full_name', 'email', 'phone',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_country', 'shipping_postal_code', 'shipping_cost',
            'tax_amount', 'discount_amount', 'status', 'payment_status',
            'payment_method', 'notes'
        ]
        widgets = {
            'order_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'user': forms.Select(attrs={'class': 'form-select select2'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_state': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_country': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.is_edit_mode = kwargs.pop('is_edit_mode', False)
        super().__init__(*args, **kwargs)

        # تقييد الاختيار للمستخدمين
        self.fields['user'].queryset = User.objects.filter(is_active=True)

        # في حالة التعديل، جعل بعض الحقول للقراءة فقط
        if self.is_edit_mode:
            for field_name in ['user', 'order_number']:
                self.fields[field_name].widget.attrs['readonly'] = True

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('معلومات الطلب'),
                    Row(
                        Column('order_number', css_class='col-md-6'),
                        Column('user', css_class='col-md-6'),
                    ),
                    Row(
                        Column('status', css_class='col-md-6'),
                        Column('payment_status', css_class='col-md-6'),
                    ),
                    'payment_method',
                    'notes',
                    ),

                Tab(_('معلومات العميل'),
                    Row(
                        Column('full_name', css_class='col-md-6'),
                        Column('email', css_class='col-md-6'),
                    ),
                    'phone',
                    ),

                Tab(_('عنوان الشحن'),
                    'shipping_address',
                    Row(
                        Column('shipping_city', css_class='col-md-6'),
                        Column('shipping_state', css_class='col-md-6'),
                    ),
                    Row(
                        Column('shipping_country', css_class='col-md-6'),
                        Column('shipping_postal_code', css_class='col-md-6'),
                    ),
                    ),

                Tab(_('التكاليف'),
                    Row(
                        Column('shipping_cost', css_class='col-md-4'),
                        Column('tax_amount', css_class='col-md-4'),
                        Column('discount_amount', css_class='col-md-4'),
                    ),
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:order_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من معلومات العميل
        full_name = cleaned_data.get('full_name')
        email = cleaned_data.get('email')

        if not full_name:
            self.add_error('full_name', _('يجب تحديد اسم العميل'))

        if not email:
            self.add_error('email', _('يجب تحديد البريد الإلكتروني للعميل'))

        return cleaned_data


class OrderItemForm(forms.ModelForm):
    """نموذج إضافة وتعديل عناصر الطلب"""

    class Meta:
        model = OrderItem
        fields = [
            'product', 'variant', 'quantity', 'unit_price'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select select2'}),
            'variant': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

        # تقييد الاختيار للمنتجات النشطة
        self.fields['product'].queryset = Product.objects.filter(is_active=True, status='published')

        # إذا تم تحديد منتج بالفعل، قم بتقييد المتغيرات له
        if self.instance.pk and self.instance.product:
            self.fields['variant'].queryset = ProductVariant.objects.filter(product=self.instance.product)
        else:
            self.fields['variant'].queryset = ProductVariant.objects.none()

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('معلومات المنتج'),
                'product',
                'variant',
            ),
            Fieldset(
                _('الكمية والسعر'),
                Row(
                    Column('quantity', css_class='col-md-6'),
                    Column('unit_price', css_class='col-md-6'),
                ),
                HTML('<div class="form-text text-muted">%s: <span id="total-price">0.00</span></div>' % _(
                    'السعر الإجمالي')),
            ),
            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:order_detail" pk=order.pk %}" class="btn btn-secondary">%s</a>' % _(
                    'إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        product = cleaned_data.get('product')
        variant = cleaned_data.get('variant')
        quantity = cleaned_data.get('quantity')

        # التحقق من توافق المنتج والمتغير
        if variant and variant.product != product:
            self.add_error('variant', _('المتغير المحدد لا ينتمي للمنتج المحدد'))

        # التحقق من الكمية
        if quantity is not None and quantity < 1:
            self.add_error('quantity', _('يجب أن تكون الكمية أكبر من صفر'))

        return cleaned_data

    def save(self, commit=True):
        item = super().save(commit=False)

        # تعيين الطلب إذا كان جديدًا
        if not item.pk and self.order:
            item.order = self.order

        # تحديث المعلومات من المنتج
        product = item.product
        variant = item.variant

        item.product_name = product.name
        item.product_id = str(product.id)

        if variant:
            item.variant_name = variant.name
            item.variant_id = str(variant.id)

        # حساب السعر الإجمالي
        item.total_price = item.unit_price * item.quantity

        if commit:
            item.save()

        # تحديث المجموع الكلي للطلب
        if self.order:
            self.order.total_price = sum(i.total_price for i in self.order.items.all())
            self.order.grand_total = (
                    self.order.total_price +
                    self.order.shipping_cost +
                    self.order.tax_amount -
                    self.order.discount_amount
            )
            self.order.save(update_fields=['total_price', 'grand_total'])

        return item


class OrderStatusUpdateForm(forms.Form):
    """نموذج تحديث حالة الطلب"""
    status = forms.ChoiceField(
        label=_('حالة الطلب'),
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    payment_status = forms.ChoiceField(
        label=_('حالة الدفع'),
        choices=Order.PAYMENT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    notify_customer = forms.BooleanField(
        label=_('إخطار العميل'),
        required=False,
        initial=True
    )

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

        # تعيين القيم الأولية من الطلب
        if self.order:
            self.fields['status'].initial = self.order.status
            self.fields['payment_status'].initial = self.order.payment_status

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('تحديث حالة الطلب'),
                'status',
                'payment_status',
                'notes',
                'notify_customer',
            ),
            FormActions(
                Submit('submit', _('تحديث'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:order_detail" pk=order.pk %}" class="btn btn-secondary">%s</a>' % _(
                    'إلغاء'))
            )
        )


# ========== نماذج الدفع والمعاملات ==========

class PaymentMethodForm(forms.ModelForm):
    """نموذج إنشاء وتعديل طرق الدفع"""

    class Meta:
        model = PaymentMethod
        fields = [
            'name', 'code', 'payment_type', 'description', 'icon',
            'instructions', 'fee_fixed', 'fee_percentage',
            'is_active', 'is_default', 'min_amount', 'max_amount',
            'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fee_fixed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fee_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    api_credentials = forms.CharField(
        label=_('بيانات اعتماد API'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل بيانات اعتماد API بتنسيق JSON')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعبئة حقل API credentials
        if self.instance.pk and self.instance.api_credentials:
            self.fields['api_credentials'].initial = json.dumps(
                self.instance.api_credentials,
                indent=4,
                ensure_ascii=False
            )

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('المعلومات الأساسية'),
                    Row(
                        Column('name', css_class='col-md-6'),
                        Column('code', css_class='col-md-6'),
                    ),
                    'payment_type',
                    'description',
                    'instructions',
                    ),

                Tab(_('الرسوم والتكاليف'),
                    Row(
                        Column('fee_fixed', css_class='col-md-6'),
                        Column('fee_percentage', css_class='col-md-6'),
                    ),
                    Row(
                        Column('min_amount', css_class='col-md-6'),
                        Column('max_amount', css_class='col-md-6'),
                    ),
                    ),

                Tab(_('الإعدادات'),
                    Row(
                        Column('is_active', css_class='col-md-6'),
                        Column('is_default', css_class='col-md-6'),
                    ),
                    'sort_order',
                    'icon',
                    ),

                Tab(_('إعدادات API'),
                    'api_credentials',
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML(
                    '<a href="{% url "dashboard:payment_method_list" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )

    def clean_api_credentials(self):
        creds = self.cleaned_data.get('api_credentials')
        if not creds:
            return {}

        try:
            return json.loads(creds)
        except json.JSONDecodeError:
            raise ValidationError(_('تنسيق JSON غير صالح لبيانات الاعتماد'))

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من المبالغ
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')

        if min_amount is not None and max_amount is not None and max_amount > 0:
            if min_amount > max_amount:
                self.add_error('max_amount', _('يجب أن يكون الحد الأقصى أكبر من الحد الأدنى'))

        return cleaned_data


class ShippingMethodForm(forms.ModelForm):
    """نموذج إنشاء وتعديل طرق الشحن"""

    class Meta:
        model = ShippingMethod
        fields = [
            'name', 'code', 'description', 'icon',
            'base_cost', 'free_shipping_threshold',
            'estimated_days_min', 'estimated_days_max',
            'is_active', 'is_default', 'sort_order',
            'restrictions'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'base_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'free_shipping_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_days_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'estimated_days_max': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'restrictions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    countries = forms.CharField(
        label=_('الدول المتاحة'),
        widget=forms.Textarea(attrs={'class': 'form-control json-editor', 'rows': 5}),
        required=False,
        help_text=_('أدخل قائمة الدول المتاحة بتنسيق JSON أو مفصولة بسطور جديدة')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعبئة حقل الدول
        if self.instance.pk and self.instance.countries:
            if isinstance(self.instance.countries, list):
                self.fields['countries'].initial = '\n'.join(self.instance.countries)
            else:
                self.fields['countries'].initial = json.dumps(
                    self.instance.countries,
                    indent=4,
                    ensure_ascii=False
                )

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab(_('المعلومات الأساسية'),
                    Row(
                        Column('name', css_class='col-md-6'),
                        Column('code', css_class='col-md-6'),
                    ),
                    'description',
                    ),

                Tab(_('التكاليف والوقت'),
                    Row(
                        Column('base_cost', css_class='col-md-6'),
                        Column('free_shipping_threshold', css_class='col-md-6'),
                    ),
                    Row(
                        Column('estimated_days_min', css_class='col-md-6'),
                        Column('estimated_days_max', css_class='col-md-6'),
                    ),
                    ),

                Tab(_('الإعدادات'),
                    Row(
                        Column('is_active', css_class='col-md-6'),
                        Column('is_default', css_class='col-md-6'),
                    ),
                    'sort_order',
                    'icon',
                    ),

                Tab(_('القيود والدول'),
                    'restrictions',
                    'countries',
                    ),
            ),

            FormActions(
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:shipping_method_list" %}" class="btn btn-secondary">%s</a>' % _(
                    'إلغاء'))
            )
        )

    def clean_countries(self):
        countries = self.cleaned_data.get('countries')
        if not countries:
            return []

        try:
            # محاولة معالجة كـ JSON
            return json.loads(countries)
        except json.JSONDecodeError:
            # معالجة كقائمة مفصولة بسطور
            return [line.strip() for line in countries.split('\n') if line.strip()]

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من أيام التوصيل
        min_days = cleaned_data.get('estimated_days_min')
        max_days = cleaned_data.get('estimated_days_max')

        if min_days is not None and max_days is not None:
            if min_days > max_days:
                self.add_error('estimated_days_max', _('يجب أن يكون الحد الأقصى للأيام أكبر من أو يساوي الحد الأدنى'))

        return cleaned_data


class PaymentRefundForm(forms.ModelForm):
    """نموذج استرداد المدفوعات"""

    class Meta:
        model = Refund
        fields = [
            'amount', 'reason', 'customer_notes', 'admin_notes'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'customer_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    full_refund = forms.BooleanField(
        label=_('استرداد كامل المبلغ'),
        required=False,
        initial=True
    )

    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تعيين المبلغ الأقصى
        if self.payment:
            max_amount = self.payment.amount
            self.fields['amount'].widget.attrs['max'] = max_amount
            self.fields['amount'].initial = max_amount
            self.fields['amount'].help_text = _('الحد الأقصى: {amount} {currency}').format(
                amount=max_amount,
                currency=self.payment.currency
            )

        # إعداد Crispy Form
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('معلومات الاسترداد'),
                'full_refund',
                'amount',
                'reason',
            ),
            Fieldset(
                _('الملاحظات'),
                'customer_notes',
                'admin_notes',
            ),
            FormActions(
                Submit('submit', _('استرداد المبلغ'), css_class='btn btn-warning'),
                HTML(
                    '<a href="{% url "dashboard:payment_detail" pk=payment.pk %}" class="btn btn-secondary">%s</a>' % _(
                        'إلغاء'))
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        # إذا تم اختيار استرداد كامل المبلغ، تعيين المبلغ تلقائيًا
        full_refund = cleaned_data.get('full_refund')
        amount = cleaned_data.get('amount')

        if full_refund and self.payment:
            cleaned_data['amount'] = self.payment.amount
        elif amount:
            # التحقق من المبلغ
            if self.payment and amount > self.payment.amount:
                self.add_error('amount', _('لا يمكن أن يكون مبلغ الاسترداد أكبر من مبلغ الدفع'))

            if amount <= 0:
                self.add_error('amount', _('يجب أن يكون مبلغ الاسترداد أكبر من صفر'))

        return cleaned_data

    def save(self, commit=True):
        refund = super().save(commit=False)

        # تعيين الحقول الأخرى
        if self.payment:
            refund.payment = self.payment
            refund.order = self.payment.order
            refund.user = self.payment.user
            refund.currency = self.payment.currency
            refund.refund_gateway = self.payment.payment_gateway

        if self.user:
            refund.requested_by = self.user

        if commit:
            refund.save()

            # إنشاء معاملة مالية للاسترداد
            refund.create_transaction()

        return refund


# ========== نماذج لوحة التحكم ==========

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


# ========== نماذج الإعدادات العامة ==========

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
                Submit('submit', _('حفظ'), css_class='btn btn-primary'),
                HTML('<a href="{% url "dashboard:index" %}" class="btn btn-secondary">%s</a>' % _('إلغاء'))
            )
        )