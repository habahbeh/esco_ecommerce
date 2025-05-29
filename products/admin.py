from django.contrib import admin
from django.utils.html import mark_safe, format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Avg, Q
from django.urls import reverse
from django.utils import timezone
from django import forms
import json

from .models import (
    Category, Brand, Product, ProductImage, ProductVariant,
    Tag, ProductReview, Wishlist, ProductComparison
)


class CategoryAdminForm(forms.ModelForm):
    """Custom form for category with better parent selection"""

    class Meta:
        model = Category
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude self and descendants from parent choices
        if self.instance.pk:
            descendants = self.instance.get_descendants()
            descendants_ids = [d.id for d in descendants] + [self.instance.pk]
            self.fields['parent'].queryset = Category.objects.exclude(id__in=descendants_ids)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    إدارة فئات المنتجات في لوحة التحكم
    Category administration in dashboard
    """

    # List Display
    list_display = [
        'indented_name', 'slug', 'parent', 'level', 'products_count',
        'is_active', 'is_featured', 'sort_order', 'views_count', 'created_at'
    ]

    # List Filters
    list_filter = [
        'is_active',
        'is_featured',
        'show_in_menu',
        'level',
        'parent',
        'created_at',
        'updated_at',
        ('parent', admin.RelatedOnlyFieldListFilter),
    ]

    # Search Fields
    search_fields = [
        'name',
        'name_en',
        'description',
        'slug',
        'meta_title',
        'meta_keywords'
    ]

    # Ordering
    ordering = ['level', 'sort_order', 'name']

    # Prepopulated Fields
    prepopulated_fields = {
        'slug': ('name',),
        'meta_title': ('name',),
    }

    # Fieldsets for better organization
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': (
                ('name', 'name_en'),
                'slug',
                ('description', 'description_en'),
            ),
            'classes': ('wide',),
        }),
        (_('التصنيف الهرمي'), {
            'fields': (
                ('parent', 'sort_order'),
            ),
            'description': _('إعدادات ترتيب وتصنيف الفئة'),
        }),
        (_('المظهر والعرض'), {
            'fields': (
                ('image', 'icon'),
                'color',
                ('is_active', 'is_featured', 'show_in_menu'),
            ),
            'classes': ('collapse',),
        }),
        (_('الأعمال والعمولة'), {
            'fields': ('commission_rate',),
            'classes': ('collapse',),
        }),
        (_('تحسين محركات البحث (SEO)'), {
            'fields': (
                'meta_title',
                'meta_description',
                'meta_keywords',
            ),
            'classes': ('collapse',),
            'description': _('إعدادات تحسين محركات البحث'),
        }),
    )

    # Read-only fields
    readonly_fields = [
        'level',
        'products_count',
        'views_count',
        'created_at',
        'updated_at',
        'full_name_display',
        'breadcrumb_display'
    ]

    # List editable fields
    list_editable = ['sort_order', 'is_active', 'is_featured']

    # Filters
    list_per_page = 50
    list_max_show_all = 200

    # Actions
    actions = [
        'make_active',
        'make_inactive',
        'make_featured',
        'remove_featured',
        'update_products_count'
    ]

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('parent', 'created_by').prefetch_related('children')

    def indented_name(self, obj):
        """Display indented category name based on level"""
        indent = '——' * obj.level
        return f"{indent} {obj.name}"

    indented_name.short_description = _('اسم الفئة')
    indented_name.admin_order_field = 'name'

    def full_name_display(self, obj):
        """Display full hierarchical name"""
        return obj.full_name

    full_name_display.short_description = _('الاسم الكامل')

    def breadcrumb_display(self, obj):
        """Display breadcrumb"""
        breadcrumb = obj.get_breadcrumb()
        names = [f'<a href="../{cat.pk}/change/">{cat.name}</a>' for cat in breadcrumb[:-1]]
        names.append(f'<strong>{obj.name}</strong>')
        return format_html(' > '.join(names))

    breadcrumb_display.short_description = _('التسلسل الهرمي')
    breadcrumb_display.allow_tags = True

    def get_form(self, request, obj=None, **kwargs):
        """Customize form"""
        form = super().get_form(request, obj, **kwargs)

        # Filter parent choices to prevent circular references
        if obj:
            # Exclude self and all descendants from parent choices
            excluded_ids = [obj.pk] + [child.pk for child in obj.get_all_children()]
            form.base_fields['parent'].queryset = Category.objects.exclude(
                pk__in=excluded_ids
            )

        # Add help text
        if 'color' in form.base_fields:
            form.base_fields['color'].help_text = _(
                'أدخل لون سداسي عشري (مثل: #FF5733) أو اتركه فارغاً'
            )

        return form

    def get_readonly_fields(self, request, obj=None):
        """Dynamic readonly fields"""
        readonly = list(self.readonly_fields)

        if obj:  # Editing existing object
            readonly.extend(['full_name_display', 'breadcrumb_display'])

        return readonly

    def save_model(self, request, obj, form, change):
        """Save model with user tracking"""
        if not change:  # Creating new object
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    # Custom Actions
    def make_active(self, request, queryset):
        """Make selected categories active"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f'تم تفعيل {updated} فئة بنجاح.'),
            messages.SUCCESS
        )

    make_active.short_description = _('تفعيل الفئات المختارة')

    def make_inactive(self, request, queryset):
        """Make selected categories inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f'تم إلغاء تفعيل {updated} فئة بنجاح.'),
            messages.SUCCESS
        )

    make_inactive.short_description = _('إلغاء تفعيل الفئات المختارة')

    def make_featured(self, request, queryset):
        """Make selected categories featured"""
        updated = queryset.update(is_featured=True)
        self.message_user(
            request,
            _(f'تم جعل {updated} فئة مميزة بنجاح.'),
            messages.SUCCESS
        )

    make_featured.short_description = _('جعل الفئات مميزة')

    def remove_featured(self, request, queryset):
        """Remove featured status from selected categories"""
        updated = queryset.update(is_featured=False)
        self.message_user(
            request,
            _(f'تم إلغاء حالة مميزة من {updated} فئة بنجاح.'),
            messages.SUCCESS
        )

    remove_featured.short_description = _('إلغاء حالة مميزة')

    def update_products_count(self, request, queryset):
        """Update products count for selected categories"""
        updated_count = 0
        for category in queryset:
            category.update_products_count()
            updated_count += 1

        self.message_user(
            request,
            _(f'تم تحديث عدد المنتجات لـ {updated_count} فئة بنجاح.'),
            messages.SUCCESS
        )

    update_products_count.short_description = _('تحديث عدد المنتجات')

    def get_list_display_links(self, request, list_display):
        """Customize list display links"""
        return ['indented_name']

    def changelist_view(self, request, extra_context=None):
        """Add extra context to changelist"""
        extra_context = extra_context or {}

        # Add statistics
        total_categories = Category.objects.count()
        active_categories = Category.objects.filter(is_active=True).count()
        featured_categories = Category.objects.filter(is_featured=True).count()
        root_categories = Category.objects.filter(parent__isnull=True).count()

        extra_context.update({
            'total_categories': total_categories,
            'active_categories': active_categories,
            'featured_categories': featured_categories,
            'root_categories': root_categories,
        })

        return super().changelist_view(request, extra_context)

    def response_add(self, request, obj, post_url_continue=None):
        """Custom response after adding"""
        response = super().response_add(request, obj, post_url_continue)
        self.message_user(
            request,
            _(f'تم إنشاء الفئة "{obj.name}" بنجاح.'),
            messages.SUCCESS
        )
        return response

    def response_change(self, request, obj):
        """Custom response after changing"""
        response = super().response_change(request, obj)
        self.message_user(
            request,
            _(f'تم تحديث الفئة "{obj.name}" بنجاح.'),
            messages.SUCCESS
        )
        return response

    def delete_model(self, request, obj):
        """Custom delete with message"""
        category_name = obj.name
        super().delete_model(request, obj)
        self.message_user(
            request,
            _(f'تم حذف الفئة "{category_name}" بنجاح.'),
            messages.SUCCESS
        )

    def has_delete_permission(self, request, obj=None):
        """Custom delete permission"""
        if obj and obj.products.exists():
            return False  # Don't allow deletion if category has products
        return super().has_delete_permission(request, obj)

    class Media:
        """Additional CSS and JS"""
        css = {
            'all': ('admin/css/category_admin.css',)
        }
        js = ('admin/js/category_admin.js',)


# Inline admin for subcategories
class SubCategoryInline(admin.TabularInline):
    """Inline admin for subcategories"""
    model = Category
    fk_name = 'parent'
    extra = 0
    fields = ['name', 'slug', 'is_active', 'sort_order']
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')


# Add inline to CategoryAdmin if needed
# CategoryAdmin.inlines = [SubCategoryInline]



@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = [
        'logo_thumbnail', 'name', 'country', 'product_count',
        'is_featured', 'is_active', 'order'
    ]
    list_filter = ['is_active', 'is_featured', 'country']
    search_fields = ['name', 'name_en', 'country']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    list_editable = ['is_featured', 'is_active', 'order']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'name_en', 'slug', 'logo', 'country', 'website')
        }),
        (_('الوصف'), {
            'fields': ('description',)
        }),
        (_('الإعدادات'), {
            'fields': ('is_active', 'is_featured', 'order')
        }),
    )

    def logo_thumbnail(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="50" height="50" style="object-fit: contain;">')
        return '-'

    logo_thumbnail.short_description = _('الشعار')

    def product_count(self, obj):
        count = obj.products.filter(is_active=True).count()
        url = reverse('admin:products_product_changelist') + f'?brand__id__exact={obj.id}'
        return format_html('<a href="{}">{} منتج</a>', url, count)

    product_count.short_description = _('عدد المنتجات')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'caption', 'is_primary', 'order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: contain;">')
        return '-'

    image_preview.short_description = _('معاينة')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['name', 'sku', 'size', 'color', 'material', 'price_adjustment', 'stock_quantity', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'image_thumbnail', 'name', 'sku', 'category', 'brand',
        'formatted_price', 'stock_status_display', 'status',
        'is_featured', 'is_new', 'views_count', 'sales_count'
    ]
    list_filter = [
        'status', 'is_active', 'is_featured', 'is_new', 'is_best_seller',
        'category', 'brand', 'stock_status', 'created_at'
    ]
    search_fields = ['name', 'name_en', 'sku', 'barcode', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = [
        'sku', 'views_count', 'sales_count', 'created_at',
        'updated_at', 'published_at', 'created_by'
    ]
    autocomplete_fields = ['category', 'brand', 'tags', 'related_products']
    date_hierarchy = 'created_at'
    inlines = [ProductImageInline, ProductVariantInline]

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': (
                'name', 'name_en', 'slug', 'sku', 'barcode',
                'category', 'brand', 'tags'
            )
        }),
        (_('الوصف'), {
            'fields': (
                'short_description', 'short_description_en',
                'description', 'description_en', 'specifications'
            )
        }),
        (_('التسعير'), {
            'fields': (
                'base_price', 'discount_percentage', 'discount_amount',
                'discount_start', 'discount_end', 'tax_rate', 'cost'
            )
        }),
        (_('المخزون'), {
            'fields': (
                'stock_quantity', 'stock_status', 'min_stock_level',
                'max_order_quantity', 'track_inventory'
            )
        }),
        (_('الأبعاد والوزن'), {
            'fields': ('weight', 'length', 'width', 'height'),
            'classes': ('collapse',)
        }),
        (_('الإعدادات'), {
            'fields': (
                'status', 'is_active', 'show_price', 'is_featured',
                'is_new', 'is_best_seller', 'is_digital', 'requires_shipping'
            )
        }),
        (_('المنتجات ذات الصلة'), {
            'fields': ('related_products',),
            'classes': ('collapse',)
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        (_('الإحصائيات'), {
            'fields': (
                'views_count', 'sales_count', 'created_at',
                'updated_at', 'published_at', 'created_by'
            ),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def image_thumbnail(self, obj):
        image = obj.default_image
        if image:
            return mark_safe(
                f'<img src="{image.image.url}" width="50" height="50" '
                f'style="object-fit: contain; border: 1px solid #ddd; border-radius: 4px;">'
            )
        return '-'

    image_thumbnail.short_description = _('الصورة')

    def formatted_price(self, obj):
        if obj.has_discount:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">{}</span> '
                '<span style="color: #e74c3c; font-weight: bold;">{}</span>',
                f'{obj.base_price:.2f}',
                f'{obj.current_price:.2f}'
            )
        return f'{obj.base_price:.2f}'

    formatted_price.short_description = _('السعر')

    def stock_status_display(self, obj):
        if obj.stock_status == 'in_stock':
            color = 'green'
            icon = '✓'
        elif obj.stock_status == 'out_of_stock':
            color = 'red'
            icon = '✗'
        else:
            color = 'orange'
            icon = '⏳'

        if obj.track_inventory:
            text = f'{icon} {obj.stock_quantity}'
        else:
            text = f'{icon} {obj.get_stock_status_display()}'

        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            text
        )

    stock_status_display.short_description = _('المخزون')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'brand', 'created_by'
        ).prefetch_related('tags', 'images')

    actions = ['make_published', 'make_draft', 'make_featured', 'remove_featured']

    def make_published(self, request, queryset):
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} منتج تم نشره.')

    make_published.short_description = _('نشر المنتجات المحددة')

    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} منتج تم تحويله لمسودة.')

    make_draft.short_description = _('تحويل لمسودة')

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} منتج تم تمييزه.')

    make_featured.short_description = _('تمييز المنتجات')

    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} منتج تم إلغاء تمييزه.')

    remove_featured.short_description = _('إلغاء التمييز')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'product', 'alt_text', 'is_primary', 'order']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text', 'caption']
    list_editable = ['is_primary', 'order']
    ordering = ['product', 'order']

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="100" height="100" '
                f'style="object-fit: contain; border: 1px solid #ddd; border-radius: 4px;">'
            )
        return '-'

    image_preview.short_description = _('معاينة')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        count = obj.products.filter(is_active=True).count()
        return f'{count} منتج'

    product_count.short_description = _('عدد المنتجات')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'user', 'rating_stars', 'title',
        'is_approved', 'is_featured', 'helpful_stats', 'created_at'
    ]
    list_filter = ['rating', 'is_approved', 'is_featured', 'created_at']
    search_fields = ['product__name', 'user__username', 'user__email', 'title', 'comment']
    readonly_fields = [
        'product', 'user', 'rating', 'title', 'comment',
        'image1', 'image2', 'image3', 'helpful_count',
        'not_helpful_count', 'created_at', 'updated_at'
    ]
    list_editable = ['is_approved', 'is_featured']
    date_hierarchy = 'created_at'

    fieldsets = (
        (_('معلومات التقييم'), {
            'fields': ('product', 'user', 'rating', 'title', 'comment')
        }),
        (_('الصور'), {
            'fields': ('image1', 'image2', 'image3'),
            'classes': ('collapse',)
        }),
        (_('الإعدادات'), {
            'fields': ('is_approved', 'is_featured')
        }),
        (_('الإحصائيات'), {
            'fields': ('helpful_count', 'not_helpful_count', 'created_at', 'updated_at')
        }),
    )

    def rating_stars(self, obj):
        stars = '⭐' * obj.rating
        empty_stars = '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color: #f39c12; font-size: 16px;">{}{}</span>',
            stars,
            empty_stars
        )

    rating_stars.short_description = _('التقييم')

    def helpful_stats(self, obj):
        if obj.helpful_count + obj.not_helpful_count > 0:
            percentage = obj.helpful_percentage
            return format_html(
                '<span style="color: {};">{}% ({}/{})</span>',
                'green' if percentage >= 70 else 'orange' if percentage >= 50 else 'red',
                percentage,
                obj.helpful_count,
                obj.helpful_count + obj.not_helpful_count
            )
        return '-'

    helpful_stats.short_description = _('نسبة الإفادة')

    actions = ['approve_reviews', 'reject_reviews', 'make_featured']

    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} تقييم تم اعتماده.')

    approve_reviews.short_description = _('اعتماد التقييمات المحددة')

    def reject_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} تقييم تم رفضه.')

    reject_reviews.short_description = _('رفض التقييمات المحددة')

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} تقييم تم تمييزه.')

    make_featured.short_description = _('تمييز التقييمات')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'product_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'product__name']
    date_hierarchy = 'created_at'

    def product_price(self, obj):
        return f'{obj.product.current_price:.2f} د.أ'

    product_price.short_description = _('سعر المنتج')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')


# Register ProductVariant if needed separately
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    إدارة متغيرات المنتجات في لوحة التحكم
    Product variants administration
    """

    # List Display
    list_display = [
        'full_name_display', 'product', 'color', 'size', 'sku',
        'stock_status_display', 'stock_quantity', 'available_quantity',
        'current_price', 'sort_order', 'is_default', 'is_active', 'sales_count'
    ]

    # List Filters
    list_filter = [
        'is_active',
        'is_default',
        'color',
        'size',
        'material',
        ('product', admin.RelatedOnlyFieldListFilter),
        ('product__category', admin.RelatedOnlyFieldListFilter),
        'created_at',
        'updated_at',
    ]

    # Search Fields
    search_fields = [
        'name',
        'sku',
        'product__name',
        'product__sku',
        'material',
        'pattern'
    ]

    # Ordering
    ordering = ['product__name', 'sort_order', 'name']

    # Fieldsets
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': (
                'product',
                ('name', 'sku'),
                ('is_active', 'is_default'),
                'sort_order',
            ),
        }),
        (_('خصائص المتغير'), {
            'fields': (
                ('color', 'color_code'),
                ('size', 'material'),
                'pattern',
                'custom_attributes',
            ),
            'classes': ('collapse',),
        }),
        (_('الأسعار والتكاليف'), {
            'fields': (
                ('price_adjustment', 'cost_adjustment'),
            ),
            'classes': ('collapse',),
        }),
        (_('إدارة المخزون'), {
            'fields': (
                ('stock_quantity', 'reserved_quantity'),
                'min_stock_level',
            ),
        }),
        (_('الأبعاد والوزن'), {
            'fields': (
                ('weight',),
                ('length', 'width', 'height'),
            ),
            'classes': ('collapse',),
        }),
    )

    # Read-only Fields
    readonly_fields = [
        'sales_count',
        'views_count',
        'created_at',
        'updated_at',
        'current_price_display',
        'available_quantity_display',
        'stock_status_display'
    ]

    # List Editable
    list_editable = ['sort_order', 'is_active', 'stock_quantity']

    # Actions
    actions = [
        'make_active',
        'make_inactive',
        'set_as_default',
        'update_stock',
        'reset_reserved_quantity'
    ]

    # Pagination
    list_per_page = 50
    list_max_show_all = 200

    # Raw ID Fields (for better performance with many products)
    raw_id_fields = ['product']

    # Autocomplete Fields
    autocomplete_fields = ['product']

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'product',
            'product__category'
        ).prefetch_related('product__images')

    # Custom Display Methods
    def full_name_display(self, obj):
        """Display full variant name with color coding"""
        name = obj.full_name
        if obj.color_code:
            return format_html(
                '<span style="display: inline-block; width: 15px; height: 15px; '
                'background-color: {}; border: 1px solid #ccc; margin-right: 5px; '
                'vertical-align: middle;"></span>{}',
                obj.color_code,
                name
            )
        return name

    full_name_display.short_description = _('اسم المتغير')
    full_name_display.admin_order_field = 'name'

    def stock_status_display(self, obj):
        """Display stock status with colors"""
        status = obj.stock_status
        colors = {
            'in_stock': '#28a745',  # أخضر
            'low_stock': '#ffc107',  # أصفر
            'out_of_stock': '#dc3545',  # أحمر
        }

        status_text = {
            'in_stock': _('متوفر'),
            'low_stock': _('مخزون منخفض'),
            'out_of_stock': _('غير متوفر'),
        }

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(status, '#6c757d'),
            status_text.get(status, status)
        )

    stock_status_display.short_description = _('حالة المخزون')

    def current_price_display(self, obj):
        """Display current price with currency"""
        return f"{obj.current_price} ر.س"

    current_price_display.short_description = _('السعر الحالي')

    def available_quantity_display(self, obj):
        """Display available quantity"""
        return f"{obj.available_quantity} / {obj.stock_quantity}"

    available_quantity_display.short_description = _('المتاح / المخزون')

    # Form Customization
    def get_form(self, request, obj=None, **kwargs):
        """Customize form"""
        form = super().get_form(request, obj, **kwargs)

        # Add help text for custom attributes
        if 'custom_attributes' in form.base_fields:
            form.base_fields['custom_attributes'].help_text = _(
                'أدخل الخصائص المخصصة بصيغة JSON. مثال: '
                '{"الوزن": "500 جرام", "البلد": "السعودية"}'
            )

        return form

    def get_readonly_fields(self, request, obj=None):
        """Dynamic readonly fields"""
        readonly = list(self.readonly_fields)

        if obj:  # Editing existing object
            readonly.extend(['current_price_display', 'available_quantity_display'])

        return readonly

    # Custom Actions
    def make_active(self, request, queryset):
        """Make selected variants active"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f'تم تفعيل {updated} متغير بنجاح.'),
            messages.SUCCESS
        )

    make_active.short_description = _('تفعيل المتغيرات المختارة')

    def make_inactive(self, request, queryset):
        """Make selected variants inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f'تم إلغاء تفعيل {updated} متغير بنجاح.'),
            messages.SUCCESS
        )

    make_inactive.short_description = _('إلغاء تفعيل المتغيرات المختارة')

    def set_as_default(self, request, queryset):
        """Set selected variant as default for its product"""
        updated_count = 0
        for variant in queryset:
            # Remove default from other variants of the same product
            ProductVariant.objects.filter(
                product=variant.product
            ).update(is_default=False)

            # Set this variant as default
            variant.is_default = True
            variant.save()
            updated_count += 1

        self.message_user(
            request,
            _(f'تم تعيين {updated_count} متغير كافتراضي.'),
            messages.SUCCESS
        )

    set_as_default.short_description = _('تعيين كمتغير افتراضي')

    def update_stock(self, request, queryset):
        """Custom action to update stock (placeholder for future implementation)"""
        self.message_user(
            request,
            _('تم اختيار المتغيرات لتحديث المخزون. استخدم نموذج التحديث المجمع.'),
            messages.INFO
        )

    update_stock.short_description = _('تحديث المخزون')

    def reset_reserved_quantity(self, request, queryset):
        """Reset reserved quantity to zero"""
        updated = queryset.update(reserved_quantity=0)
        self.message_user(
            request,
            _(f'تم إعادة تعيين الكمية المحجوزة لـ {updated} متغير.'),
            messages.SUCCESS
        )

    reset_reserved_quantity.short_description = _('إعادة تعيين الكمية المحجوزة')

    def save_model(self, request, obj, form, change):
        """Custom save with validation"""
        try:
            super().save_model(request, obj, form, change)

            if not change:  # New object
                self.message_user(
                    request,
                    _(f'تم إنشاء المتغير "{obj.name}" بنجاح.'),
                    messages.SUCCESS
                )
            else:  # Updated object
                self.message_user(
                    request,
                    _(f'تم تحديث المتغير "{obj.name}" بنجاح.'),
                    messages.SUCCESS
                )

        except Exception as e:
            self.message_user(
                request,
                _(f'حدث خطأ: {str(e)}'),
                messages.ERROR
            )

    def delete_model(self, request, obj):
        """Custom delete with message"""
        variant_name = obj.name
        super().delete_model(request, obj)
        self.message_user(
            request,
            _(f'تم حذف المتغير "{variant_name}" بنجاح.'),
            messages.SUCCESS
        )

    class Media:
        """Additional CSS and JS"""
        css = {
            'all': ('admin/css/variant_admin.css',)
        }
        js = ('admin/js/variant_admin.js',)


# Inline Admin for Product Variants
class ProductVariantInline(admin.TabularInline):
    """Inline admin for product variants in ProductAdmin"""
    model = ProductVariant
    extra = 1
    fields = [
        'name', 'color', 'size', 'sku', 'price_adjustment',
        'stock_quantity', 'is_active', 'is_default', 'sort_order'
    ]
    readonly_fields = ['sales_count']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


# Alternative: Stacked Inline for more detailed view
class ProductVariantStackedInline(admin.StackedInline):
    """Stacked inline for detailed variant management"""
    model = ProductVariant
    extra = 0
    fieldsets = (
        (None, {
            'fields': (
                ('name', 'sku'),
                ('color', 'size'),
                ('price_adjustment', 'stock_quantity'),
                ('is_active', 'is_default'),
            )
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')