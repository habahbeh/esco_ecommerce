from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from .models import Category, Product, ProductVariant, ProductImage, ProductDiscount


class ProductVariantInline(admin.TabularInline):
    """
    إضافة متغيرات المنتج مباشرة في صفحة تحرير المنتج
    Add product variants directly in the product edit page
    """
    model = ProductVariant
    extra = 1
    fields = ('name_ar', 'name_en', 'color_code', 'price_adjustment', 'stock_quantity', 'is_active')


class ProductImageInline(admin.TabularInline):
    """
    إضافة صور المنتج مباشرة في صفحة تحرير المنتج
    Add product images directly in the product edit page
    """
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'variant', 'sort_order')
    readonly_fields = ('thumbnail',)

    def thumbnail(self, obj):
        """عرض صورة مصغرة للصورة - Display thumbnail of the image"""
        if obj.image:
            return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
        return "لا توجد صورة"

    thumbnail.short_description = _("معاينة")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    إدارة تصنيفات المنتجات - تسمح للمشرفين بإدارة تصنيفات المنتجات
    Category admin - allows administrators to manage product categories
    """
    list_display = ('name', 'name_ar', 'name_en', 'level', 'parent', 'is_active', 'show_prices', 'created_at')
    list_filter = ('level', 'is_active', 'show_prices', 'created_at')
    search_fields = ('name', 'name_ar', 'name_en', 'description')
    prepopulated_fields = {'slug': ('name_en',)}
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'level')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name_ar', 'name_en', 'slug', 'description', 'image')
        }),
        (_('التصنيف الأب'), {
            'fields': ('parent',)
        }),
        (_('الإعدادات'), {
            'fields': ('is_active', 'show_prices')
        }),
        (_('معلومات النظام'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'level')
        }),
    )

    def save_model(self, request, obj, form, change):
        """تسجيل المستخدم الذي أنشأ/عدّل التصنيف - Record the user who created/modified the category"""
        if not change:  # إذا كان هذا إنشاء جديد - If this is a new creation
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProductDiscount)
class ProductDiscountAdmin(admin.ModelAdmin):
    """
    إدارة خصومات المنتجات - تسمح للمشرفين بإدارة الخصومات
    Product discount admin - allows administrators to manage discounts
    """
    list_display = ('name', 'discount_type', 'value', 'start_date', 'end_date', 'is_active', 'category', 'is_valid_now')
    list_filter = ('discount_type', 'is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'
    fieldsets = (
        (_('معلومات الخصم'), {
            'fields': ('name', 'description', 'discount_type', 'value')
        }),
        (_('التوقيت'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('الإعدادات'), {
            'fields': ('is_active', 'category')
        }),
    )

    def is_valid_now(self, obj):
        """التحقق مما إذا كان الخصم ساري المفعول حالياً - Check if the discount is currently valid"""
        return obj.is_valid

    is_valid_now.boolean = True
    is_valid_now.short_description = _("ساري المفعول")


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    """
    إدارة المنتجات - تسمح للمشرفين بإدارة المنتجات مع دعم الاستيراد/التصدير
    Product admin - allows administrators to manage products with import/export support
    """
    list_display = (
    'sku', 'name', 'category', 'base_price', 'current_price_display', 'stock_status', 'status', 'is_active',
    'created_at')
    list_filter = ('status', 'is_active', 'is_featured', 'stock_status', 'category', 'created_at')
    search_fields = ('name', 'name_ar', 'name_en', 'sku', 'description')
    prepopulated_fields = {'slug': ('name_en',)}
    readonly_fields = ('created_at', 'updated_at', 'published_at', 'created_by', 'updated_by', 'approved_by')
    date_hierarchy = 'created_at'
    inlines = [ProductVariantInline, ProductImageInline]
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name_ar', 'name_en', 'slug', 'sku', 'category')
        }),
        (_('الوصف'), {
            'fields': ('description_ar', 'description_en', 'short_description')
        }),
        (_('السعر والمخزون'), {
            'fields': ('base_price', 'show_price', 'discount', 'stock_quantity', 'stock_status')
        }),
        (_('الصورة الافتراضية'), {
            'fields': ('default_image',)
        }),
        (_('حالة المنتج'), {
            'fields': ('status', 'is_featured', 'is_active')
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        (_('معلومات النظام'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'published_at', 'created_by', 'updated_by', 'approved_by')
        }),
    )

    def current_price_display(self, obj):
        """عرض السعر الحالي بعد الخصم إن وجد - Display current price after discount if any"""
        if obj.has_discount:
            return format_html('{} <strike style="color: #999;">{}</strike>',
                               obj.current_price, obj.base_price)
        return obj.base_price

    current_price_display.short_description = _("السعر الحالي")

    def save_model(self, request, obj, form, change):
        """تسجيل المستخدم الذي أنشأ/عدّل المنتج - Record the user who created/modified the product"""
        if not change:  # إذا كان هذا إنشاء جديد - If this is a new creation
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    إدارة متغيرات المنتج - تسمح للمشرفين بإدارة متغيرات المنتج
    Product variant admin - allows administrators to manage product variants
    """
    list_display = ('product', 'name', 'color_display', 'price_adjustment', 'stock_quantity', 'is_active')
    list_filter = ('is_active', 'product')
    search_fields = ('name', 'name_ar', 'name_en', 'product__name')

    def color_display(self, obj):
        """عرض مربع ملون يمثل لون المتغير - Display colored box representing the variant color"""
        if obj.color_code:
            return format_html(
                '<div style="background-color: {}; width: 20px; height: 20px; border: 1px solid #ddd;"></div>',
                obj.color_code)
        return "-"

    color_display.short_description = _("اللون")


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """
    إدارة صور المنتج - تسمح للمشرفين بإدارة صور المنتج
    Product image admin - allows administrators to manage product images
    """
    list_display = ('thumbnail_display', 'product', 'variant', 'alt_text', 'is_primary', 'sort_order')
    list_filter = ('is_primary', 'product')
    search_fields = ('product__name', 'alt_text')

    def thumbnail_display(self, obj):
        """عرض صورة مصغرة للصورة - Display thumbnail of the image"""
        if obj.image:
            return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
        return "لا توجد صورة"

    thumbnail_display.short_description = _("الصورة")