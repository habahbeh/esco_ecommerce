from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import BlogCategory, BlogTag, BlogPost


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'slug', 'sort_order', 'is_active', 'post_count']
    list_filter = ['is_active']
    list_editable = ['sort_order', 'is_active']
    search_fields = ['name', 'name_en']
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _post_count=Count('posts', filter=Q(posts__status='published'))
        )

    def post_count(self, obj):
        return obj._post_count
    post_count.short_description = _("عدد المقالات")
    post_count.admin_order_field = '_post_count'


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'slug']
    search_fields = ['name', 'name_en']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'status', 'is_featured', 'views_count', 'published_at', 'image_preview']
    list_filter = ['status', 'is_featured', 'category', 'created_at']
    list_editable = ['status', 'is_featured']
    search_fields = ['title', 'title_en', 'content', 'content_en']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags', 'related_products', 'related_categories']
    date_hierarchy = 'created_at'
    readonly_fields = ['views_count', 'reading_time', 'created_at', 'updated_at']
    list_select_related = ['category', 'author']

    fieldsets = (
        (_("المحتوى الأساسي"), {
            'fields': ('title', 'title_en', 'slug', 'category', 'tags', 'author',
                       'excerpt', 'excerpt_en', 'content', 'content_en')
        }),
        (_("الصورة"), {
            'fields': ('featured_image', 'featured_image_alt', 'featured_image_alt_en')
        }),
        (_("الإعدادات"), {
            'fields': ('status', 'is_featured', 'allow_comments', 'published_at')
        }),
        (_("SEO"), {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'canonical_url'),
            'classes': ('collapse',)
        }),
        (_("الربط الداخلي"), {
            'fields': ('related_products', 'related_categories'),
            'classes': ('collapse',)
        }),
        (_("إحصائيات"), {
            'fields': ('views_count', 'reading_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:4px;" />', obj.featured_image.url)
        return '-'
    image_preview.short_description = _("الصورة")

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)
