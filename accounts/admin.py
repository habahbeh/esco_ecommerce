# accounts/admin.py
"""
إعدادات لوحة الإدارة لتطبيق الحسابات
Admin panel settings for the accounts app
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group, Permission
from .models import User, UserProfile, UserAddress, UserActivity, Role


class UserProfileInline(admin.StackedInline):
    """
    عرض الملف الشخصي كجزء داخلي في صفحة المستخدم
    Show profile as an inline in user page
    """
    model = UserProfile
    can_delete = False
    verbose_name = _("الملف الشخصي")
    verbose_name_plural = _("الملف الشخصي")
    fk_name = "user"
    fieldsets = (
        (_("المعلومات الشخصية"), {
            'fields': ('bio', 'interests', 'profession', 'company')
        }),
        (_("روابط التواصل"), {
            'fields': ('website', 'twitter', 'facebook', 'instagram', 'linkedin')
        }),
        (_("الإعدادات"), {
            'fields': ('notification_preferences', 'privacy_settings')
        }),
        (_("التوثيق"), {
            'fields': ('identity_verified', 'phone_verified')
        }),
    )


class UserAddressInline(admin.TabularInline):
    """
    عرض عناوين المستخدم كجزء داخلي في صفحة المستخدم
    Show user addresses as an inline in user page
    """
    model = UserAddress
    extra = 0
    verbose_name = _("العنوان")
    verbose_name_plural = _("العناوين")
    fields = ('label', 'type', 'city', 'country', 'is_default')


class CustomUserAdmin(UserAdmin):
    """
    إعدادات عرض نموذج المستخدم في لوحة الإدارة
    User model admin settings
    """
    list_display = ('username', 'email', 'get_full_name', 'is_active', 'is_verified',
                    'is_staff', 'role', 'total_orders', 'date_joined', 'last_activity')
    list_filter = ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'role', 'gender', 'language')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    readonly_fields = ('id', 'date_joined', 'last_login', 'last_activity', 'total_orders', 'total_spent')

    fieldsets = (
        (_("معلومات تسجيل الدخول"), {
            'fields': ('username', 'email', 'password')
        }),
        (_("المعلومات الشخصية"), {
            'fields': ('first_name', 'last_name', 'phone_number', 'avatar', 'birth_date', 'gender')
        }),
        (_("العنوان"), {
            'fields': ('address', 'city', 'country', 'postal_code')
        }),
        (_("الصلاحيات"), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'groups', 'user_permissions')
        }),
        (_("التفعيل والتوثيق"), {
            'fields': ('is_verified', 'verification_token', 'verification_token_expires')
        }),
        (_("التفضيلات"), {
            'fields': ('language', 'timezone', 'accept_marketing')
        }),
        (_("الإحصائيات"), {
            'fields': ('date_joined', 'last_login', 'last_activity', 'total_orders', 'total_spent')
        }),
    )

    add_fieldsets = (
        (_("معلومات تسجيل الدخول"), {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        (_("المعلومات الشخصية"), {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        (_("الصلاحيات"), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'role')
        }),
    )

    inlines = [UserProfileInline, UserAddressInline]

    def get_inline_instances(self, request, obj=None):
        """عدم عرض الأقسام الداخلية عند إنشاء مستخدم جديد"""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

    def save_model(self, request, obj, form, change):
        """تحديث إحصائيات الطلبات عند حفظ المستخدم"""
        super().save_model(request, obj, form, change)
        if change:  # فقط للتحديثات وليس عند الإنشاء
            obj.update_order_stats()


class RoleAdmin(admin.ModelAdmin):
    """
    إعدادات عرض نموذج الأدوار في لوحة الإدارة
    Role model admin settings
    """
    list_display = ('name', 'description', 'get_users_count')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)

    def get_users_count(self, obj):
        """عرض عدد المستخدمين لكل دور"""
        return obj.users.count()

    get_users_count.short_description = _("عدد المستخدمين")


class UserAddressAdmin(admin.ModelAdmin):
    """
    إعدادات عرض نموذج عناوين المستخدمين في لوحة الإدارة
    User address model admin settings
    """
    list_display = ('label', 'user', 'type', 'city', 'country', 'is_default', 'created_at')
    list_filter = ('type', 'is_default', 'is_billing_default', 'is_shipping_default', 'city', 'country')
    search_fields = ('user__username', 'user__email', 'label', 'city', 'country', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)

    fieldsets = (
        (_("معلومات العنوان"), {
            'fields': ('user', 'label', 'type')
        }),
        (_("بيانات المستلم"), {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        (_("تفاصيل العنوان"), {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country')
        }),
        (_("الإعدادات"), {
            'fields': ('is_default', 'is_billing_default', 'is_shipping_default')
        }),
        (_("التواريخ"), {
            'fields': ('created_at', 'updated_at')
        }),
    )


class UserActivityAdmin(admin.ModelAdmin):
    """
    إعدادات عرض نموذج نشاطات المستخدمين في لوحة الإدارة
    User activity model admin settings
    """
    list_display = ('user', 'activity_type', 'timestamp', 'ip_address', 'description_short')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'activity_type', 'description', 'ip_address')
    readonly_fields = ('user', 'activity_type', 'description', 'object_id', 'content_type', 'timestamp', 'ip_address')
    date_hierarchy = 'timestamp'

    def description_short(self, obj):
        """عرض وصف مختصر للنشاط"""
        if len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description

    description_short.short_description = _("الوصف")

    def has_add_permission(self, request):
        """منع إضافة سجلات نشاط يدوياً"""
        return False

    def has_change_permission(self, request, obj=None):
        """منع تعديل سجلات النشاط"""
        return False


class UserProfileAdmin(admin.ModelAdmin):
    """
    إعدادات عرض نموذج الملفات الشخصية في لوحة الإدارة
    User profile model admin settings
    """
    list_display = ('user', 'profession', 'company', 'identity_verified', 'phone_verified', 'updated_at')
    list_filter = ('identity_verified', 'phone_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'profession', 'company', 'bio')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)

    fieldsets = (
        (_("المعلومات الأساسية"), {
            'fields': ('user', 'bio', 'interests')
        }),
        (_("معلومات مهنية"), {
            'fields': ('profession', 'company')
        }),
        (_("روابط التواصل"), {
            'fields': ('website', 'twitter', 'facebook', 'instagram', 'linkedin')
        }),
        (_("الإعدادات"), {
            'fields': ('notification_preferences', 'privacy_settings')
        }),
        (_("التوثيق"), {
            'fields': ('identity_verified', 'phone_verified')
        }),
        (_("التواريخ"), {
            'fields': ('created_at', 'updated_at')
        }),
    )


# تسجيل النماذج في لوحة الإدارة
# Register models in admin panel
admin.site.register(User, CustomUserAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserAddress, UserAddressAdmin)
admin.site.register(UserActivity, UserActivityAdmin)

# تغيير عنوان لوحة الإدارة
# Change admin panel title
admin.site.site_header = _("لوحة إدارة الموقع")
admin.site.site_title = _("نظام إدارة المستخدمين")
admin.site.index_title = _("مرحباً بك في نظام إدارة المستخدمين")