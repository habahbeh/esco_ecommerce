# accounts/admin.py
"""
Django Admin configuration for accounts models
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count

from .models import User, UserProfile, UserAddress, UserActivity


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for user profile
    """
    model = UserProfile
    extra = 0
    fields = [
        'profession', 'company', 'bio', 'interests',
        'identity_verified', 'phone_verified'
    ]
    readonly_fields = ['created_at', 'updated_at']


class UserAddressInline(admin.TabularInline):
    """
    Inline admin for user addresses
    """
    model = UserAddress
    extra = 0
    fields = [
        'label', 'type', 'city', 'country',
        'is_default', 'is_billing_default', 'is_shipping_default'
    ]
    readonly_fields = ['created_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    إدارة المستخدمين المخصصة
    Custom User Admin
    """
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'is_product_reviewer', 'is_verified',
        'total_orders', 'date_joined'
    ]
    list_filter = [
        'is_staff', 'is_superuser', 'is_active', 'is_verified',
        'is_product_reviewer', 'gender', 'language', 'date_joined'
    ]
    search_fields = [
        'username', 'first_name', 'last_name', 'email', 'phone_number'
    ]
    ordering = ['-date_joined']
    readonly_fields = [
        'last_login', 'date_joined', 'last_activity',
        'total_orders', 'total_spent'
    ]

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('username', 'password')
        }),
        (_('معلومات شخصية'), {
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'birth_date', 'gender', 'avatar'
            )
        }),
        (_('العنوان'), {
            'fields': ('address', 'city', 'country', 'postal_code'),
            'classes': ('collapse',)
        }),
        (_('الصلاحيات'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'is_verified', 'is_product_reviewer'
            )
        }),
        (_('التفضيلات'), {
            'fields': ('language', 'timezone', 'accept_marketing'),
            'classes': ('collapse',)
        }),
        (_('الإحصائيات'), {
            'fields': ('total_orders', 'total_spent'),
            'classes': ('collapse',)
        }),
        (_('مجموعات المستخدمين'), {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('تواريخ مهمة'), {
            'fields': ('last_login', 'date_joined', 'last_activity'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (_('معلومات أساسية'), {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        (_('معلومات شخصية'), {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'phone_number'),
        }),
        (_('الصلاحيات'), {
            'classes': ('wide',),
            'fields': ('is_staff', 'is_product_reviewer'),
        }),
    )

    inlines = [UserProfileInline, UserAddressInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'groups', 'addresses', 'profile'
        ).annotate(
            address_count=Count('addresses')
        )

    actions = ['verify_users', 'make_product_reviewer', 'remove_product_reviewer']

    def verify_users(self, request, queryset):
        """Verify selected users"""
        updated = queryset.filter(is_verified=False).update(is_verified=True)
        self.message_user(
            request,
            f"تم توثيق {updated} مستخدم."
        )

    verify_users.short_description = _("توثيق المستخدمين المحددين")

    def make_product_reviewer(self, request, queryset):
        """Make users product reviewers"""
        updated = queryset.filter(is_product_reviewer=False).update(
            is_product_reviewer=True
        )
        self.message_user(
            request,
            f"تم تعيين {updated} مستخدم كمراجع منتجات."
        )

    make_product_reviewer.short_description = _("تعيين كمراجعي منتجات")

    def remove_product_reviewer(self, request, queryset):
        """Remove product reviewer permission"""
        updated = queryset.filter(is_product_reviewer=True).update(
            is_product_reviewer=False
        )
        self.message_user(
            request,
            f"تم إزالة صلاحية مراجعة المنتجات من {updated} مستخدم."
        )

    remove_product_reviewer.short_description = _("إزالة صلاحية مراجعة المنتجات")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    إدارة الملفات الشخصية للمستخدمين
    User Profile Admin
    """
    list_display = [
        'user', 'profession', 'company', 'identity_verified',
        'phone_verified', 'created_at'
    ]
    list_filter = [
        'identity_verified', 'phone_verified', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'profession', 'company'
    ]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (_('المستخدم'), {
            'fields': ('user',)
        }),
        (_('معلومات مهنية'), {
            'fields': ('profession', 'company')
        }),
        (_('نبذة شخصية'), {
            'fields': ('bio', 'interests')
        }),
        (_('روابط التواصل الاجتماعي'), {
            'fields': ('website', 'twitter', 'facebook', 'instagram', 'linkedin'),
            'classes': ('collapse',)
        }),
        (_('التوثيق'), {
            'fields': ('identity_verified', 'phone_verified')
        }),
        (_('الإعدادات'), {
            'fields': ('notification_preferences', 'privacy_settings'),
            'classes': ('collapse',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    """
    إدارة عناوين المستخدمين
    User Address Admin
    """
    list_display = [
        'user', 'label', 'type', 'city', 'country',
        'is_default', 'is_billing_default', 'is_shipping_default'
    ]
    list_filter = [
        'type', 'country', 'is_default',
        'is_billing_default', 'is_shipping_default'
    ]
    search_fields = [
        'user__username', 'user__email', 'label',
        'first_name', 'last_name', 'city', 'country'
    ]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (_('المستخدم'), {
            'fields': ('user', 'label', 'type')
        }),
        (_('معلومات الاستلام'), {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        (_('العنوان'), {
            'fields': (
                'address_line_1', 'address_line_2',
                'city', 'state', 'postal_code', 'country'
            )
        }),
        (_('إعدادات افتراضية'), {
            'fields': (
                'is_default', 'is_billing_default', 'is_shipping_default'
            )
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """
    إدارة أنشطة المستخدمين
    User Activity Admin
    """
    list_display = [
        'user', 'activity_type', 'short_description', 'timestamp', 'ip_address'
    ]
    list_filter = [
        'activity_type', 'timestamp'
    ]
    search_fields = [
        'user__username', 'user__email', 'activity_type', 'description'
    ]
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

    fieldsets = (
        (_('معلومات النشاط'), {
            'fields': ('user', 'activity_type', 'description')
        }),
        (_('معلومات تقنية'), {
            'fields': ('object_id', 'content_type', 'ip_address', 'timestamp'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def short_description(self, obj):
        """عرض وصف مختصر للنشاط"""
        if len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description

    short_description.short_description = _("الوصف المختصر")

    # إعدادات إضافية للأداء
    list_per_page = 50
    list_max_show_all = 200

    def has_add_permission(self, request):
        """منع إضافة أنشطة يدوياً"""
        return False

    def has_change_permission(self, request, obj=None):
        """منع تعديل الأنشطة"""
        return False


# إعدادات إضافية للـ Admin Site
admin.site.site_header = _("إدارة الموقع")
admin.site.site_title = _("لوحة التحكم")
admin.site.index_title = _("مرحباً بك في لوحة التحكم")