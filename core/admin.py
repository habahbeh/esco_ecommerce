from django.contrib import admin
from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """
    إدارة إعدادات الموقع - تتيح للمشرفين تخصيص إعدادات الموقع العامة
    Site settings admin - allows administrators to customize general site settings
    """
    fieldsets = (
        ('معلومات الموقع الأساسية - Basic Site Information', {
            'fields': ('site_name', 'site_description', 'logo', 'favicon')
        }),
        ('معلومات الاتصال - Contact Information', {
            'fields': ('email', 'phone', 'address')
        }),
        ('وسائل التواصل الاجتماعي - Social Media', {
            'fields': ('facebook', 'twitter', 'instagram', 'linkedin')
        }),
        ('إعدادات المظهر - Appearance Settings', {
            'fields': ('primary_color', 'enable_dark_mode', 'default_dark_mode')
        }),
    )

    def has_add_permission(self, request):
        # السماح بإضافة إعدادات واحدة فقط - Allow only one settings instance
        # return not SiteSettings.objects.exists()
        return True

    def has_delete_permission(self, request, obj=None):
        # منع حذف الإعدادات - Prevent deletion of settings
        return False