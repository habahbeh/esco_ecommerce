# accounts/admin.py
"""
تكوين الإدارة لتطبيق الحسابات
Admin configuration for accounts app
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, UserActivity, UserAddress, Role


class UserProfileInline(admin.StackedInline):
    """إدراج داخلي للملف الشخصي للمستخدم"""
    model = UserProfile
    can_delete = False
    verbose_name = _("الملف الشخصي")
    verbose_name_plural = _("الملف الشخصي")
    fk_name = 'user'


class UserAddressInline(admin.TabularInline):
    """إدراج داخلي لعناوين المستخدم"""
    model = UserAddress
    extra = 0
    verbose_name = _("عنوان")
    verbose_name_plural = _("العناوين")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """تكوين إدارة المستخدمين المخصصة"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_verified')
    list_filter = ('is_staff', 'is_active', 'is_verified', 'role', 'gender', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('المعلومات الشخصية'),
         {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'avatar', 'gender', 'birth_date')}),
        (_('العنوان'), {'fields': ('address', 'city', 'country', 'postal_code')}),
        (_('التفضيلات'), {'fields': ('language', 'timezone', 'accept_marketing')}),
        (_('التحقق'), {'fields': ('is_verified', 'verification_token', 'verification_token_expires')}),
        (_('إعادة تعيين كلمة المرور'), {'fields': ('password_reset_token', 'password_reset_expires')}),
        (_('الأذونات'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'groups', 'user_permissions')}),
        (_('تواريخ مهمة'), {'fields': ('last_login', 'date_joined', 'last_activity')}),
        (_('إحصائيات'), {'fields': ('total_orders', 'total_spent')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('last_login', 'date_joined', 'total_orders', 'total_spent')
    inlines = (UserProfileInline, UserAddressInline)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """تكوين إدارة الأدوار"""
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """تكوين إدارة نشاطات المستخدم"""
    list_display = ('user', 'activity_type', 'description', 'timestamp', 'ip_address')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'description', 'ip_address')
    readonly_fields = ('user', 'activity_type', 'description', 'timestamp', 'ip_address', 'content_type', 'object_id')

    def has_add_permission(self, request):
        """منع إضافة سجلات نشاط يدويًا"""
        return False

    def has_change_permission(self, request, obj=None):
        """منع تعديل سجلات النشاط"""
        return False