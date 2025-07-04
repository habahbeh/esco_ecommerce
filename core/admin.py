from django.contrib import admin
from .models import SiteSettings, Newsletter, SliderItem, StaticContent
from django.utils.translation import gettext as _


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

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """إدارة اشتراكات النشرة البريدية"""
    list_display = ('email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email',)

@admin.register(SliderItem)
class SliderItemAdmin(admin.ModelAdmin):
    """
    إدارة عناصر السلايدر - تتيح للمشرفين إضافة وتعديل عناصر السلايدر
    Slider items admin - allows administrators to add and edit slider items
    """
    list_display = ('title', 'subtitle', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle', 'description')
    fieldsets = (
        (_('معلومات العنصر الأساسية'), {
            'fields': ('title', 'subtitle', 'description', 'image')
        }),
        (_('إعدادات الأزرار'), {
            'fields': ('primary_button_text', 'primary_button_url',
                      'secondary_button_text', 'secondary_button_url')
        }),
        (_('إعدادات العرض'), {
            'fields': ('order', 'is_active')
        }),
    )


@admin.register(StaticContent)
class StaticContentAdmin(admin.ModelAdmin):
    """
    إدارة المحتوى الثابت - تتيح للمشرفين إدارة المحتوى الثابت للموقع بلغات متعددة
    Static content admin - allows administrators to manage static content in multiple languages
    """
    list_display = ('key', 'last_updated')
    search_fields = ('key', 'content_ar', 'content_en')
    list_filter = ('last_updated',)
    readonly_fields = ('last_updated',)

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('key', 'last_updated')
        }),
        (_('المحتوى العربي'), {
            'fields': ('content_ar',),
            'classes': ('extrapretty',)
        }),
        (_('المحتوى الإنجليزي'), {
            'fields': ('content_en',),
            'classes': ('extrapretty',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # منع تعديل المفتاح بعد الإنشاء - Prevent key modification after creation
        if obj:  # إذا كان الكائن موجود بالفعل (تحرير وليس إنشاء)
            return self.readonly_fields + ('key',)
        return self.readonly_fields