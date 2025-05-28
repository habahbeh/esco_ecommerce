from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserActivity


class CustomUserAdmin(UserAdmin):
    """
    إدارة المستخدمين المخصصة - تعرض وتدير حسابات المستخدمين
    Custom user admin - displays and manages user accounts
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('معلومات شخصية'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'address')}),
        (_('أذونات'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_product_manager', 'is_product_reviewer', 'groups',
                       'user_permissions'),
        }),
        (_('تواريخ مهمة'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = (
    'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_product_manager', 'is_product_reviewer')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_product_manager', 'is_product_reviewer', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    ordering = ('username',)

    def get_readonly_fields(self, request, obj=None):
        # جعل بعض الحقول للقراءة فقط عند التعديل - Make some fields read-only when editing
        if obj:  # هذا عند تحرير مستخدم موجود - This is when editing an existing user
            return ['date_joined', 'last_login']
        return []


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """
    إدارة نشاطات المستخدمين - تعرض سجل نشاطات المستخدمين
    User activity admin - displays user activity log
    """
    list_display = ('user', 'activity_type', 'description', 'timestamp', 'ip_address')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'description', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'activity_type', 'description', 'timestamp', 'ip_address', 'object_id', 'content_type')

    def has_add_permission(self, request):
        # منع إضافة سجلات نشاط يدوياً - Prevent manual addition of activity records
        return False

    def has_change_permission(self, request, obj=None):
        # منع تعديل سجلات النشاط - Prevent editing activity records
        return False


# تسجيل النماذج في موقع الإدارة - Register models to admin site
admin.site.register(User, CustomUserAdmin)