from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Event, EventImage


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 3
    fields = ('image', 'caption', 'order', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
        return _("لا توجد صورة")

    preview.short_description = _("معاينة")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'location', 'is_active', 'display_in', 'event_status')
    list_filter = ('is_active', 'display_in')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EventImageInline]

    fieldsets = (
        (_('معلومات الفعالية'), {
            'fields': ('title', 'slug', 'description', 'short_description', 'start_date', 'end_date', 'location')
        }),
        (_('الصور'), {
            'fields': ('banner_image', 'cover_image')
        }),
        (_('إعدادات العرض'), {
            'fields': ('is_active', 'display_in', 'order', 'registration_url', 'button_text')
        }),
    )

    def event_status(self, obj):
        status = obj.status_text
        if obj.is_upcoming:
            return format_html('<span style="color: blue;">{}</span>', status)
        elif obj.is_ongoing:
            return format_html('<span style="color: green;">{}</span>', status)
        else:
            return format_html('<span style="color: gray;">{}</span>', status)

    event_status.short_description = _("حالة الفعالية")