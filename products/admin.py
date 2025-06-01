# products/admin.py
from django.contrib import admin
from django.utils.html import mark_safe, format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Avg, Q, Sum, F, Max, Min
from django.urls import reverse, path
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin import SimpleListFilter
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe
import json
import csv
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    Category, Brand, Product, ProductImage, ProductVariant,
    Tag, ProductReview, Wishlist, ProductComparison, ProductViewHistory,
    ProductAttribute, ProductAttributeValue, ProductQuestion,
    ProductSubscription, ProductDiscount, DiscountUsage
)


# ==================== CUSTOM FILTERS ====================

class StockLevelFilter(SimpleListFilter):
    """فلتر مستوى المخزون"""
    title = _('مستوى المخزون')
    parameter_name = 'stock_level'

    def lookups(self, request, model_admin):
        return (
            ('in_stock', _('متوفر')),
            ('low_stock', _('مخزون منخفض')),
            ('out_of_stock', _('نفد المخزون')),
            ('overstocked', _('مخزون زائد')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(stock_quantity__gt=F('min_stock_level'))
        elif self.value() == 'low_stock':
            return queryset.filter(
                stock_quantity__gt=0,
                stock_quantity__lte=F('min_stock_level')
            )
        elif self.value() == 'out_of_stock':
            return queryset.filter(stock_quantity=0)
        elif self.value() == 'overstocked':
            return queryset.filter(stock_quantity__gt=100)


class PriceRangeFilter(SimpleListFilter):
    """فلتر نطاق الأسعار"""
    title = _('نطاق السعر')
    parameter_name = 'price_range'

    def lookups(self, request, model_admin):
        return (
            ('0-100', _('0 - 100 ر.س')),
            ('100-500', _('100 - 500 ر.س')),
            ('500-1000', _('500 - 1000 ر.س')),
            ('1000-5000', _('1000 - 5000 ر.س')),
            ('5000+', _('أكثر من 5000 ر.س')),
        )

    def queryset(self, request, queryset):
        if self.value() == '0-100':
            return queryset.filter(base_price__range=(0, 100))
        elif self.value() == '100-500':
            return queryset.filter(base_price__range=(100, 500))
        elif self.value() == '500-1000':
            return queryset.filter(base_price__range=(500, 1000))
        elif self.value() == '1000-5000':
            return queryset.filter(base_price__range=(1000, 5000))
        elif self.value() == '5000+':
            return queryset.filter(base_price__gt=5000)


class DateCreatedFilter(SimpleListFilter):
    """فلتر تاريخ الإنشاء"""
    title = _('تاريخ الإنشاء')
    parameter_name = 'date_created'

    def lookups(self, request, model_admin):
        return (
            ('today', _('اليوم')),
            ('yesterday', _('أمس')),
            ('this_week', _('هذا الأسبوع')),
            ('this_month', _('هذا الشهر')),
            ('last_month', _('الشهر الماضي')),
            ('this_year', _('هذا العام')),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(created_at__date=now.date())
        elif self.value() == 'yesterday':
            yesterday = now - timedelta(days=1)
            return queryset.filter(created_at__date=yesterday.date())
        elif self.value() == 'this_week':
            start_week = now - timedelta(days=now.weekday())
            return queryset.filter(created_at__gte=start_week)
        elif self.value() == 'this_month':
            return queryset.filter(
                created_at__year=now.year,
                created_at__month=now.month
            )
        elif self.value() == 'last_month':
            last_month = now.replace(day=1) - timedelta(days=1)
            return queryset.filter(
                created_at__year=last_month.year,
                created_at__month=last_month.month
            )
        elif self.value() == 'this_year':
            return queryset.filter(created_at__year=now.year)


# ==================== CUSTOM FORMS ====================

class CategoryAdminForm(forms.ModelForm):
    """نموذج محسن لإدارة الفئات"""

    class Meta:
        model = Category
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # منع المرجع الدائري
        if self.instance.pk:
            descendants = self.instance.get_all_children()
            descendants_ids = [d.id for d in descendants] + [self.instance.pk]
            self.fields['parent'].queryset = Category.objects.exclude(id__in=descendants_ids)

        # تحسين عرض الخيارات
        self.fields['parent'].empty_label = _("-- فئة جذر --")

        # إضافة help text مخصص
        self.fields['color'].help_text = _('اللون بصيغة سداسية عشرية مثل: #FF5733')
        self.fields['icon'].help_text = _('CSS class للأيقونة مثل: fas fa-laptop')


class ProductAdminForm(forms.ModelForm):
    """نموذج محسن لإدارة المنتجات"""

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'short_description': forms.Textarea(attrs={'rows': 3}),
            'specifications': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من منطق الخصومات
        discount_percentage = cleaned_data.get('discount_percentage', 0)
        discount_amount = cleaned_data.get('discount_amount', 0)
        base_price = cleaned_data.get('base_price', 0)

        if discount_percentage > 0 and discount_amount > 0:
            raise ValidationError(_("لا يمكن تطبيق نسبة خصم ومبلغ خصم معاً"))

        if discount_amount >= base_price:
            raise ValidationError(_("مبلغ الخصم لا يمكن أن يكون أكبر من السعر الأساسي"))

        return cleaned_data


class ProductImageWidget(AdminFileWidget):
    """ويدجت محسن لصور المنتجات"""

    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and hasattr(value, 'url'):
            output.append(format_html(
                '<div class="image-preview" style="margin-bottom: 10px;">'
                '<img src="{}" style="max-width: 200px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px;">'
                '</div>',
                value.url
            ))
        output.append(super().render(name, value, attrs, renderer))
        return mark_safe(''.join(output))


# ==================== INLINE ADMINS ====================

class ProductImageInline(admin.TabularInline):
    """إدارة صور المنتجات المضمنة"""
    model = ProductImage
    extra = 1
    max_num = 10
    fields = ['image', 'image_preview', 'alt_text', 'is_primary', 'sort_order']
    readonly_fields = ['image_preview']
    ordering = ['sort_order', '-is_primary']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 4px;">',
                obj.image.url
            )
        return _('لا توجد صورة')

    image_preview.short_description = _('معاينة')


class ProductVariantInline(admin.TabularInline):
    """إدارة متغيرات المنتجات المضمنة"""
    model = ProductVariant
    extra = 0
    fields = [
        'name', 'sku', 'attributes', 'base_price',
        'stock_quantity', 'is_active', 'is_default'
    ]
    readonly_fields = ['available_quantity_display']

    def available_quantity_display(self, obj):
        return f"{obj.available_quantity} / {obj.stock_quantity}"

    available_quantity_display.short_description = _('متاح / إجمالي')


class ProductAttributeValueInline(admin.TabularInline):
    """إدارة قيم خصائص المنتجات المضمنة"""
    model = ProductAttributeValue
    extra = 0
    autocomplete_fields = ['attribute']


class SubCategoryInline(admin.TabularInline):
    """إدارة الفئات الفرعية المضمنة"""
    model = Category
    fk_name = 'parent'
    extra = 0
    fields = ['name', 'slug', 'is_active', 'sort_order', 'products_count']
    readonly_fields = ['products_count']
    show_change_link = True


# ==================== MAIN ADMIN CLASSES ====================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """إدارة فئات المنتجات المحسنة"""

    form = CategoryAdminForm
    list_display = [
        'indented_name', 'level', 'products_count', 'views_count',
        'is_active', 'is_featured', 'sort_order', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_featured', 'show_in_menu', 'level',
        ('parent', admin.RelatedOnlyFieldListFilter),
        DateCreatedFilter
    ]
    search_fields = ['name', 'name_en', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['level', 'sort_order', 'name']
    list_editable = ['sort_order', 'is_active', 'is_featured']
    list_per_page = 50
    inlines = [SubCategoryInline]

    fieldsets = (
        (_('المعلومات الأساسية'), {
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
                'level',
            ),
        }),
        (_('المظهر والعرض'), {
            'fields': (
                ('image', 'banner_image'),
                ('icon', 'color'),
                ('is_active', 'is_featured', 'show_in_menu'),
                'show_prices',
            ),
            'classes': ('collapse',),
        }),
        (_('الإعدادات التجارية'), {
            'fields': ('commission_rate',),
            'classes': ('collapse',),
        }),
        (_('تحسين محركات البحث'), {
            'fields': (
                'meta_title',
                'meta_description',
                'meta_keywords',
            ),
            'classes': ('collapse',),
        }),
        (_('المحتوى الإضافي'), {
            'fields': ('content_blocks',),
            'classes': ('collapse',),
        }),
        (_('الإحصائيات'), {
            'fields': (
                'products_count', 'views_count',
                'created_at', 'updated_at', 'created_by'
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = [
        'level', 'products_count', 'views_count',
        'created_at', 'updated_at', 'breadcrumb_display'
    ]

    actions = [
        'make_active', 'make_inactive', 'make_featured',
        'remove_featured', 'update_products_count', 'export_csv'
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent', 'created_by')

    def indented_name(self, obj):
        """عرض الاسم مع المسافة البادئة"""
        indent = '──' * obj.level
        return format_html('{} {}', indent, obj.name)

    indented_name.short_description = _('اسم الفئة')
    indented_name.admin_order_field = 'name'

    def breadcrumb_display(self, obj):
        """عرض التسلسل الهرمي"""
        breadcrumb = obj.get_breadcrumb()
        links = []
        for cat in breadcrumb[:-1]:
            url = reverse('admin:products_category_change', args=[cat.pk])
            links.append(f'<a href="{url}">{cat.name}</a>')
        links.append(f'<strong>{obj.name}</strong>')
        return format_html(' > '.join(links))

    breadcrumb_display.short_description = _('التسلسل الهرمي')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # إجراءات مخصصة
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} فئة تم تفعيلها بنجاح.', messages.SUCCESS)

    make_active.short_description = _('تفعيل الفئات المختارة')

    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} فئة تم إلغاء تفعيلها بنجاح.', messages.SUCCESS)

    make_inactive.short_description = _('إلغاء تفعيل الفئات المختارة')

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} فئة تم تمييزها بنجاح.', messages.SUCCESS)

    make_featured.short_description = _('تمييز الفئات المختارة')

    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} فئة تم إلغاء تمييزها بنجاح.', messages.SUCCESS)

    remove_featured.short_description = _('إلغاء تمييز الفئات المختارة')

    def update_products_count(self, request, queryset):
        for category in queryset:
            category.update_products_count()
        self.message_user(request, f'تم تحديث عدد المنتجات لـ {queryset.count()} فئة.', messages.SUCCESS)

    update_products_count.short_description = _('تحديث عدد المنتجات')

    def export_csv(self, request, queryset):
        """تصدير الفئات إلى CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="categories.csv"'

        writer = csv.writer(response)
        writer.writerow(['الاسم', 'المستوى', 'عدد المنتجات', 'نشط', 'مميز'])

        for category in queryset:
            writer.writerow([
                category.name, category.level, category.products_count,
                'نعم' if category.is_active else 'لا',
                'نعم' if category.is_featured else 'لا'
            ])

        return response

    export_csv.short_description = _('تصدير إلى CSV')


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """إدارة العلامات التجارية المحسنة"""

    list_display = [
        'logo_thumbnail', 'name', 'country', 'products_count',
        'rating', 'is_featured', 'is_active', 'is_verified', 'views_count'
    ]
    list_filter = [
        'is_active', 'is_featured', 'is_verified', 'country',
        DateCreatedFilter
    ]
    search_fields = ['name', 'name_en', 'country', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']
    list_editable = ['is_featured', 'is_active', 'is_verified',]
    readonly_fields = ['products_count', 'views_count', 'rating', 'created_at', 'updated_at']

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': (
                ('name', 'name_en'),
                'slug',
                ('logo', 'banner_image'),
            )
        }),
        (_('معلومات التواصل'), {
            'fields': (
                ('website', 'email'),
                'phone',
                ('country', 'city'),
            ),
            'classes': ('collapse',),
        }),
        (_('الوصف'), {
            'fields': ('description', 'history'),
            'classes': ('collapse',),
        }),
        (_('الإعدادات'), {
            'fields': (
                ('is_active', 'is_featured', 'is_verified'),
                'sort_order',
            )
        }),
        (_('الشبكات الاجتماعية'), {
            'fields': ('social_links',),
            'classes': ('collapse',),
        }),
        (_('تحسين محركات البحث'), {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',),
        }),
        (_('الإحصائيات'), {
            'fields': (
                'products_count', 'views_count', 'rating',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',),
        }),
    )

    actions = ['make_featured', 'remove_featured', 'verify_brands', 'export_csv']

    def logo_thumbnail(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: contain; border-radius: 4px;">',
                obj.logo.url
            )
        return '—'

    logo_thumbnail.short_description = _('الشعار')

    def products_count(self, obj):
        count = obj.products.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:products_product_changelist') + f'?brand__id__exact={obj.id}'
            return format_html('<a href="{}">{} منتج</a>', url, count)
        return '0'

    products_count.short_description = _('عدد المنتجات')

    def verify_brands(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'تم توثيق {updated} علامة تجارية.', messages.SUCCESS)

    verify_brands.short_description = _('توثيق العلامات التجارية')

    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="brands.csv"'

        writer = csv.writer(response)
        writer.writerow(['الاسم', 'البلد', 'عدد المنتجات', 'التقييم', 'موثق'])

        for brand in queryset:
            writer.writerow([
                brand.name, brand.country, brand.products_count,
                f'{brand.rating:.1f}', 'نعم' if brand.is_verified else 'لا'
            ])

        return response

    export_csv.short_description = _('تصدير إلى CSV')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """إدارة المنتجات المحسنة"""

    form = ProductAdminForm
    list_display = [
        'image_thumbnail', 'name', 'sku', 'category', 'brand',
        'formatted_price', 'stock_status_display', 'status',
        'is_featured', 'rating_display', 'sales_count', 'views_count'
    ]
    list_filter = [
        'status', 'is_active', 'is_featured', 'is_new', 'is_best_seller',
        'category', 'brand', 'stock_status', 'condition',
        StockLevelFilter, PriceRangeFilter, DateCreatedFilter
    ]
    search_fields = [
        'name', 'name_en', 'sku', 'barcode', 'description',
        'category__name', 'brand__name'
    ]
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = [
        'sku', 'views_count', 'sales_count', 'created_at',
        'updated_at', 'published_at', 'current_price_display',
        'available_quantity', 'rating_display'
    ]
    autocomplete_fields = ['category', 'brand', 'tags', 'related_products']
    filter_horizontal = ['tags', 'related_products', 'cross_sell_products', 'upsell_products']
    date_hierarchy = 'created_at'
    list_per_page = 25
    list_max_show_all = 100
    save_on_top = True

    inlines = [ProductImageInline, ProductVariantInline, ProductAttributeValueInline]

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': (
                ('name', 'name_en'),
                'slug',
                ('sku', 'barcode'),
                ('category', 'brand'),
                'tags',
            ),
            'classes': ('wide',),
        }),
        (_('الوصف'), {
            'fields': (
                'short_description',
                'description',
                'specifications',
                'features',
            ),
        }),
        (_('التسعير'), {
            'fields': (
                ('base_price', 'compare_price', 'cost'),
                ('discount_percentage', 'discount_amount'),
                ('discount_start', 'discount_end'),
                ('tax_rate', 'tax_class'),
                'current_price_display',
            ),
        }),
        (_('المخزون'), {
            'fields': (
                ('stock_quantity', 'reserved_quantity'),
                ('stock_status', 'min_stock_level'),
                ('max_order_quantity', 'track_inventory'),
                'available_quantity',
            ),
        }),
        (_('الأبعاد والوزن'), {
            'fields': (
                'weight',
                ('length', 'width', 'height'),
            ),
            'classes': ('collapse',),
        }),
        (_('خصائص المنتج'), {
            'fields': (
                'condition',
                ('is_digital', 'requires_shipping', 'is_gift_card'),
                ('available_for_preorder', 'preorder_message'),
                ('warranty_period', 'warranty_details'),
            ),
            'classes': ('collapse',),
        }),
        (_('الإعدادات'), {
            'fields': (
                ('status', 'is_active'),
                ('show_price', 'allow_reviews'),
                ('is_featured', 'is_new', 'is_best_seller'),
                ('featured_until',),
            ),
        }),
        (_('المنتجات ذات الصلة'), {
            'fields': (
                'related_products',
                'cross_sell_products',
                'upsell_products',
            ),
            'classes': ('collapse',),
        }),
        (_('تحسين محركات البحث'), {
            'fields': (
                'meta_title',
                'meta_description',
                'meta_keywords',
                'search_keywords',
            ),
            'classes': ('collapse',),
        }),
        (_('الإحصائيات'), {
            'fields': (
                ('views_count', 'sales_count', 'wishlist_count'),
                'rating_display',
                ('created_at', 'updated_at', 'published_at'),
                'created_by',
            ),
            'classes': ('collapse',),
        }),
    )

    actions = [
        'make_published', 'make_draft', 'make_featured', 'remove_featured',
        'duplicate_products', 'update_stock_status', 'apply_discount', 'export_csv'
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'brand', 'created_by'
        ).prefetch_related('tags', 'images', 'reviews')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def image_thumbnail(self, obj):
        image = obj.default_image
        if image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">',
                image.image.url
            )
        return '—'

    image_thumbnail.short_description = _('الصورة')

    def formatted_price(self, obj):
        if obj.has_discount:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">{}</span><br>'
                '<span style="color: #e74c3c; font-weight: bold;">{}</span>',
                f'{obj.base_price:.2f} ر.س',
                f'{obj.current_price:.2f} ر.س'
            )
        return f'{obj.base_price:.2f} ر.س'

    formatted_price.short_description = _('السعر')

    def current_price_display(self, obj):
        return f'{obj.current_price:.2f} ر.س'

    current_price_display.short_description = _('السعر الحالي')

    def stock_status_display(self, obj):
        colors = {
            'in_stock': '#28a745',
            'out_of_stock': '#dc3545',
            'pre_order': '#ffc107',
            'discontinued': '#6c757d'
        }

        color = colors.get(obj.stock_status, '#6c757d')
        status_text = obj.get_stock_status_display()

        if obj.track_inventory:
            if obj.low_stock:
                color = '#ffc107'
                status_text += f' ({obj.available_quantity})'
            elif obj.available_quantity > 0:
                status_text += f' ({obj.available_quantity})'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status_text
        )

    stock_status_display.short_description = _('حالة المخزون')

    def rating_display(self, obj):
        rating = obj.rating
        if rating > 0:
            stars = '⭐' * int(rating)
            # Format the rating value before passing to format_html
            rating_str = f'{float(rating):.1f}'
            return format_html(
                '<span style="color: #f39c12;">{}</span> ({})',
                stars, rating_str
            )
        return '—'

    rating_display.short_description = _('التقييم')

    # إجراءات مخصصة
    def make_published(self, request, queryset):
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} منتج تم نشره.', messages.SUCCESS)

    make_published.short_description = _('نشر المنتجات المحددة')

    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} منتج تم تحويله لمسودة.', messages.SUCCESS)

    make_draft.short_description = _('تحويل لمسودة')

    def duplicate_products(self, request, queryset):
        """تكرار المنتجات المختارة"""
        duplicated_count = 0
        for product in queryset:
            # إنشاء نسخة جديدة
            product.pk = None
            product.sku = product.generate_sku()
            product.slug = f"{product.slug}-copy"
            product.name = f"{product.name} - نسخة"
            product.status = 'draft'
            product.save()
            duplicated_count += 1

        self.message_user(
            request,
            f'تم تكرار {duplicated_count} منتج بنجاح.',
            messages.SUCCESS
        )

    duplicate_products.short_description = _('تكرار المنتجات')

    def update_stock_status(self, request, queryset):
        """تحديث حالة المخزون تلقائياً"""
        updated_count = 0
        for product in queryset:
            if product.track_inventory:
                if product.available_quantity <= 0:
                    product.stock_status = 'out_of_stock'
                elif product.available_quantity <= product.min_stock_level:
                    product.stock_status = 'in_stock'  # Low stock but in stock
                else:
                    product.stock_status = 'in_stock'
                product.save(update_fields=['stock_status'])
                updated_count += 1

        self.message_user(
            request,
            f'تم تحديث حالة المخزون لـ {updated_count} منتج.',
            messages.SUCCESS
        )

    update_stock_status.short_description = _('تحديث حالة المخزون')

    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'الاسم', 'SKU', 'الفئة', 'العلامة التجارية', 'السعر',
            'الكمية', 'الحالة', 'تاريخ الإنشاء'
        ])

        for product in queryset:
            writer.writerow([
                product.name, product.sku,
                product.category.name, product.brand.name if product.brand else '',
                product.current_price, product.stock_quantity,
                product.get_status_display(), product.created_at.strftime('%Y-%m-%d')
            ])

        return response

    export_csv.short_description = _('تصدير إلى CSV')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """إدارة صور المنتجات"""

    list_display = ['image_preview', 'product', 'alt_text', 'is_primary', 'sort_order', 'created_at']
    list_filter = ['is_primary', 'is_360', 'created_at']
    search_fields = ['product__name', 'alt_text', 'caption']
    list_editable = ['is_primary', 'sort_order']
    ordering = ['product', 'sort_order']
    autocomplete_fields = ['product', 'variant']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;">',
                obj.get_thumbnail_url()
            )
        return '—'

    image_preview.short_description = _('معاينة')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """إدارة متغيرات المنتجات"""

    list_display = [
        'name', 'product', 'sku', 'current_price',
        'stock_quantity_display', 'is_active', 'is_default', 'sort_order'
    ]
    list_filter = [
        'is_active', 'is_default', 'track_inventory',
        ('product', admin.RelatedOnlyFieldListFilter),
        DateCreatedFilter
    ]
    search_fields = ['name', 'sku', 'product__name']
    autocomplete_fields = ['product']
    list_editable = ['is_active', 'sort_order']
    ordering = ['product', 'sort_order']

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': (
                'product', 'name', 'sku',
                ('is_active', 'is_default'), 'sort_order'
            )
        }),
        (_('الخصائص'), {
            'fields': ('attributes',),
        }),
        (_('التسعير'), {
            'fields': ('base_price',),
        }),
        (_('المخزون'), {
            'fields': (
                ('stock_quantity', 'reserved_quantity'),
                'track_inventory',
            ),
        }),
        (_('الأبعاد'), {
            'fields': ('weight',),
            'classes': ('collapse',),
        }),
    )

    def stock_quantity_display(self, obj):
        if obj.track_inventory:
            available = obj.available_quantity
            total = obj.stock_quantity
            color = '#28a745' if available > 0 else '#dc3545'
            return format_html(
                '<span style="color: {};">{} / {}</span>',
                color, available, total
            )
        return _('غير محدود')

    stock_quantity_display.short_description = _('المخزون')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """إدارة الوسوم"""

    list_display = ['name', 'color_display', 'products_count', 'usage_count', 'is_featured', 'is_active']
    list_filter = ['is_active', 'is_featured', DateCreatedFilter]
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_featured', 'is_active']
    readonly_fields = ['products_count', 'usage_count']

    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="background-color: {}; padding: 2px 8px; border-radius: 3px; color: white;">{}</span>',
                obj.color, obj.name
            )
        return obj.name

    color_display.short_description = _('اللون')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """إدارة تقييمات المنتجات"""

    list_display = [
        'product', 'user', 'rating_stars', 'title',
        'is_approved', 'is_featured', 'helpful_stats', 'created_at'
    ]
    list_filter = [
        'rating', 'is_approved', 'is_featured', 'recommend',
        ('product', admin.RelatedOnlyFieldListFilter),
        DateCreatedFilter
    ]
    search_fields = ['product__name', 'user__username', 'title', 'content']
    readonly_fields = [
        'helpful_votes', 'unhelpful_votes', 'report_count',
        'ip_address', 'user_agent', 'created_at', 'updated_at'
    ]
    list_editable = ['is_approved', 'is_featured']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['product']

    fieldsets = (
        (_('معلومات التقييم'), {
            'fields': (
                ('product', 'user'),
                ('rating', 'recommend'),
                'title', 'content',
            )
        }),
        (_('تقييمات فرعية'), {
            'fields': (
                ('quality_rating', 'value_rating', 'delivery_rating'),
            ),
            'classes': ('collapse',),
        }),
        (_('الصورة'), {
            'fields': ('image',),
            'classes': ('collapse',),
        }),
        (_('الإعدادات'), {
            'fields': (
                ('is_approved', 'is_featured'),
                ('approved_at', 'approved_by'),
            )
        }),
        (_('الإحصائيات'), {
            'fields': (
                ('helpful_votes', 'unhelpful_votes'),
                'report_count', 'is_spam',
            ),
            'classes': ('collapse',),
        }),
        (_('معلومات تقنية'), {
            'fields': (
                'ip_address', 'user_agent',
                'purchase_date',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )

    actions = ['approve_reviews', 'reject_reviews', 'make_featured', 'mark_as_spam']

    def rating_stars(self, obj):
        stars = '⭐' * obj.rating
        empty_stars = '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color: #f39c12; font-size: 16px;">{}{}</span>',
            stars, empty_stars
        )

    rating_stars.short_description = _('التقييم')

    def helpful_stats(self, obj):
        if obj.total_votes > 0:
            percentage = obj.helpful_percentage
            color = '#28a745' if percentage >= 70 else '#ffc107' if percentage >= 50 else '#dc3545'
            return format_html(
                '<span style="color: {};">{}% ({}/{})</span>',
                color, percentage, obj.helpful_votes, obj.total_votes
            )
        return '—'

    helpful_stats.short_description = _('نسبة الإفادة')

    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True, approved_at=timezone.now(), approved_by=request.user)
        self.message_user(request, f'{updated} تقييم تم اعتماده.', messages.SUCCESS)

    approve_reviews.short_description = _('اعتماد التقييمات')

    def reject_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} تقييم تم رفضه.', messages.SUCCESS)

    reject_reviews.short_description = _('رفض التقييمات')

    def mark_as_spam(self, request, queryset):
        updated = queryset.update(is_spam=True, is_approved=False)
        self.message_user(request, f'{updated} تقييم تم تصنيفه كرسالة مزعجة.', messages.SUCCESS)

    mark_as_spam.short_description = _('تصنيف كرسالة مزعجة')


@admin.register(ProductDiscount)
class ProductDiscountAdmin(admin.ModelAdmin):
    """إدارة خصومات المنتجات"""

    list_display = [
        'name', 'discount_type', 'value', 'application_type',
        'start_date', 'end_date', 'is_active', 'used_count', 'usage_percentage'
    ]
    list_filter = [
        'discount_type', 'application_type', 'is_active',
        'requires_coupon_code', 'is_stackable',
        DateCreatedFilter
    ]
    search_fields = ['name', 'description', 'code']
    filter_horizontal = ['products']
    date_hierarchy = 'start_date'
    readonly_fields = ['used_count', 'created_at', 'updated_at']

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': (
                ('name', 'code'),
                'description',
            )
        }),
        (_('إعدادات الخصم'), {
            'fields': (
                ('discount_type', 'value'),
                'max_discount_amount',
                ('application_type', 'category'),
                'products',
            )
        }),
        (_('فترة الصلاحية'), {
            'fields': (
                ('start_date', 'end_date'),
            )
        }),
        (_('شروط الاستخدام'), {
            'fields': (
                ('min_purchase_amount', 'min_quantity'),
                ('max_uses', 'max_uses_per_user'),
            ),
            'classes': ('collapse',),
        }),
        (_('خصم اشتري X احصل على Y'), {
            'fields': (
                ('buy_quantity', 'get_quantity'),
                'get_discount_percentage',
            ),
            'classes': ('collapse',),
        }),
        (_('الإعدادات'), {
            'fields': (
                ('is_active', 'requires_coupon_code'),
                ('is_stackable', 'priority'),
            )
        }),
        (_('الإحصائيات'), {
            'fields': (
                'used_count',
                ('created_at', 'updated_at', 'created_by'),
            ),
            'classes': ('collapse',),
        }),
    )

    def usage_percentage(self, obj):
        if obj.max_uses:
            percentage = obj.get_usage_percentage()
            color = '#dc3545' if percentage >= 90 else '#ffc107' if percentage >= 70 else '#28a745'
            return format_html(
                '<span style="color: {};">{}%</span>',
                color, percentage
            )
        return '—'

    usage_percentage.short_description = _('نسبة الاستخدام')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """إدارة قوائم الأمنيات"""

    list_display = ['user', 'product', 'variant', 'notify_on_sale', 'notify_on_restock', 'created_at']
    list_filter = ['notify_on_sale', 'notify_on_restock', DateCreatedFilter]
    search_fields = ['user__username', 'product__name']
    autocomplete_fields = ['user', 'product', 'variant']
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product', 'variant')


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    """إدارة خصائص المنتجات"""

    list_display = ['name', 'attribute_type', 'is_required', 'is_filterable', 'sort_order', 'is_active']
    list_filter = ['attribute_type', 'is_required', 'is_filterable', 'is_searchable', 'is_active']
    search_fields = ['name', 'name_en']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['categories']
    list_editable = ['sort_order', 'is_active']

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': (
                ('name', 'name_en'),
                'slug',
                'attribute_type',
            )
        }),
        (_('خيارات الاختيار'), {
            'fields': ('options',),
            'classes': ('collapse',),
        }),
        (_('الإعدادات'), {
            'fields': (
                ('is_required', 'is_filterable'),
                ('is_searchable', 'is_active'),
                'sort_order',
            )
        }),
        (_('الفئات'), {
            'fields': ('categories',),
            'classes': ('collapse',),
        }),
    )


@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    """إدارة أسئلة المنتجات"""

    list_display = [
        'product', 'user', 'question_preview', 'is_answered',
        'is_public', 'helpful_votes', 'created_at'
    ]
    list_filter = ['is_answered', 'is_public', 'is_featured', DateCreatedFilter]
    search_fields = ['product__name', 'user__username', 'question', 'answer']
    autocomplete_fields = ['product', 'user', 'answered_by']
    readonly_fields = ['helpful_votes', 'answered_at', 'created_at', 'updated_at']

    fieldsets = (
        (_('السؤال'), {
            'fields': (
                ('product', 'user'),
                'question',
                ('is_public', 'is_featured'),
            )
        }),
        (_('الإجابة'), {
            'fields': (
                'answer',
                ('answered_by', 'answered_at'),
                'is_answered',
            )
        }),
        (_('الإحصائيات'), {
            'fields': (
                'helpful_votes',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )

    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question

    question_preview.short_description = _('السؤال')

    actions = ['mark_as_answered', 'make_public', 'make_private']

    def mark_as_answered(self, request, queryset):
        for question in queryset:
            if question.answer:
                question.is_answered = True
                question.answered_by = request.user
                question.answered_at = timezone.now()
                question.save()

        self.message_user(request, f'تم تحديث حالة الإجابة للأسئلة.', messages.SUCCESS)

    mark_as_answered.short_description = _('تصنيف كمجاب عليه')


# ==================== DASHBOARD CUSTOMIZATION ====================

def get_admin_stats():
    """إحصائيات سريعة للوحة الإدارة"""
    stats = {
        'total_products': Product.objects.count(),
        'active_products': Product.objects.filter(is_active=True, status='published').count(),
        'total_categories': Category.objects.count(),
        'total_brands': Brand.objects.count(),
        'low_stock_products': Product.objects.filter(
            track_inventory=True,
            stock_quantity__lte=F('min_stock_level'),
            stock_quantity__gt=0
        ).count(),
        'out_of_stock': Product.objects.filter(
            track_inventory=True,
            stock_quantity=0
        ).count(),
        'pending_reviews': ProductReview.objects.filter(is_approved=False).count(),
        'total_reviews': ProductReview.objects.filter(is_approved=True).count(),
    }
    return stats


# تسجيل الباقي من النماذج
admin.site.register(ProductComparison)
admin.site.register(ProductViewHistory)
admin.site.register(ProductAttributeValue)
admin.site.register(ProductSubscription)
admin.site.register(DiscountUsage)

# تخصيص عناوين الإدارة
admin.site.site_header = _('إدارة المنتجات')
admin.site.site_title = _('لوحة التحكم')
admin.site.index_title = _('مرحباً بك في لوحة إدارة المنتجات')


# تخصيص CSS للإدارة
class AdminConfig:
    """إعدادات مخصصة للإدارة"""

    class Media:
        css = {
            'all': (
                'admin/css/custom_admin.css',
                'admin/css/arabic_admin.css',
            )
        }
        js = (
            'admin/js/custom_admin.js',
            'admin/js/admin_enhancements.js',
        )